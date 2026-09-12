import sys, os, math, json
sys.path.extend([
    os.path.abspath("packages/core/src"),
    os.path.abspath("packages/domain/src"),
    os.path.abspath("packages/data_access/src"),
    os.path.abspath("packages/models/src"),
    os.path.abspath("packages/iceberg_physics/src"),
    os.path.abspath("packages/risk_engine/src"),
    os.path.abspath("packages/routing/src"),
    os.path.abspath("packages/services/src"),
    os.path.abspath("apps/backend/src"),
    os.path.abspath(".")
])

from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from data_access.spatial import haversine_distance_nm
from data_access.environment_provider import default_environment_provider
from routing.speed_model import VesselSpeedModel
from routing.fuel_model import NavalArchitectureFuelModel
from datetime import datetime, timezone, timedelta

def normalize_lon(lon: float) -> float:
    """Normalize longitude to [-180, 180]."""
    return (lon + 180.0) % 360.0 - 180.0

def shortest_lon_diff(lon1: float, lon2: float) -> float:
    """Returns the signed shortest angular difference from lon1 to lon2 in [-180, 180]."""
    diff = (lon2 - lon1 + 180.0) % 360.0 - 180.0
    return diff

def get_antarctic_land_limit_lat(lon: float) -> float:
    """
    Returns the northernmost boundary of the Antarctic continent / ice shelves at a given longitude.
    Any latitude south of this value is land or permanent shelf ice.
    """
    norm_lon = normalize_lon(lon)
    # Antarctic Peninsula (Graham Land / Palmer Land) extends up to -63.2S between -65W and -56W
    if -75.0 <= norm_lon <= -53.0:
        return -62.8
    # Ross Sea embayment: deep ocean extends down to -77.5S between 165E and -155W
    elif (norm_lon >= 165.0) or (norm_lon <= -155.0):
        return -77.5
    # Weddell Sea embayment: ocean extends to -75.0S between -53W and -30W
    elif -53.0 < norm_lon <= -30.0:
        return -74.5
    # Prydz Bay (Bharati / Davis): ocean extends to -69.5S between 70E and 80E
    elif 68.0 <= norm_lon <= 82.0:
        return -69.5
    # Lazarev Sea (Maitri): ocean extends to -70.5S between 10E and 15E
    elif 9.0 <= norm_lon <= 15.0:
        return -70.5
    # General East and West Antarctic coastline
    else:
        return -65.5

def plan_maritime_voyage(
    origin: GeoPoint,
    dest: GeoPoint,
    departure_time: datetime,
    vessel: VesselProfile,
    objective: RouteObjective
):
    speed_model = VesselSpeedModel()
    fuel_model = NavalArchitectureFuelModel()
    env_prov = default_environment_provider

    orig_lat, orig_lon = origin.latitude, normalize_lon(origin.longitude)
    dest_lat, dest_lon = dest.latitude, normalize_lon(dest.longitude)

    # 1. Determine Objective Characteristics
    if objective == RouteObjective.SHORTEST:
        transit_lat = -61.5   # closest safe polar circumpolar latitude
        desired_speed = vessel.service_speed_knots
        lat_safety_offset = 0.5
    elif objective == RouteObjective.FASTEST:
        transit_lat = -53.0   # open-water sprint band with near-zero ice
        desired_speed = getattr(vessel, "max_speed_knots", vessel.service_speed_knots * 1.15)
        lat_safety_offset = 3.5
    elif objective == RouteObjective.SAFEST:
        transit_lat = -52.0   # wide clearance north of Marginal Ice Zone & major iceberg pack
        desired_speed = vessel.service_speed_knots * 0.90
        lat_safety_offset = 5.0
    elif objective == RouteObjective.FUEL_EFFICIENT:
        transit_lat = -50.5   # core of ACC eastward jet stream for current assist
        desired_speed = vessel.service_speed_knots * 0.80 # economical slow steam (~8 kn)
        lat_safety_offset = 4.0
    else: # BALANCED
        transit_lat = -57.0   # optimal multi-criteria trade-off
        desired_speed = vessel.service_speed_knots
        lat_safety_offset = 2.0

    # 2. Check if a direct leg crosses Antarctica or needs circumpolar routing
    lon_diff = shortest_lon_diff(orig_lon, dest_lon)
    direct_dist = haversine_distance_nm(orig_lat, orig_lon, dest_lat, dest_lon)

    # Check sample points along direct spherical interpolation
    crosses_continent = False
    for frac in [0.2, 0.35, 0.5, 0.65, 0.8]:
        interp_lat = orig_lat + frac * (dest_lat - orig_lat)
        interp_lon = normalize_lon(orig_lon + frac * lon_diff)
        land_limit = get_antarctic_land_limit_lat(interp_lon)
        # If the point dips south of the continental coastline, or cuts through the Peninsula
        if interp_lat <= (land_limit - 0.2):
            crosses_continent = True
            break
        # Also check if it cuts through the Antarctic Peninsula between -72W and -54W south of -62.8
        if -75.0 <= interp_lon <= -53.0 and interp_lat < -61.5:
            crosses_continent = True
            break

    # Build sequence of Navigable Maritime Corridor Waypoints
    corridor_pts: list[tuple[float, float]] = []

    if not crosses_continent and abs(lon_diff) < 45.0:
        # Direct Great-Circle Corridor with subtle objective curvature
        num_corridor_steps = 24
        for step in range(num_corridor_steps + 1):
            f = step / float(num_corridor_steps)
            c_lat = orig_lat + f * (dest_lat - orig_lat)
            c_lon = normalize_lon(orig_lon + f * lon_diff)
            # Add subtle outward deflection away from the pole in mid-voyage
            if -68.0 < c_lat < -35.0:
                deflection = math.sin(f * math.pi) * lat_safety_offset
                c_lat = min(c_lat + deflection, -30.0)
            corridor_pts.append((c_lat, c_lon))
    else:
        # Multi-stage circumpolar maritime voyage
        # Stage A: Departure to Open-Ocean Entry
        entry_lat = min(orig_lat + 2.0, transit_lat) if orig_lat < transit_lat else transit_lat
        entry_lon = orig_lon

        # If origin is near South America, ensure route passes through Drake Passage (-57.0, -66.0)
        drake_pt = (-57.0, -66.0)
        needs_drake = (-75.0 <= orig_lon <= -53.0 and orig_lat < -45.0) or (-75.0 <= dest_lon <= -53.0 and dest_lat < -45.0)

        # Stage B: Target destination ocean approach
        exit_lat = transit_lat
        exit_lon = dest_lon

        # Assemble key maritime waypoints
        key_nodes = [(orig_lat, orig_lon)]
        if orig_lat < transit_lat:
            key_nodes.append((transit_lat, orig_lon))
        
        # If rounding Antarctic Peninsula, route through Drake Passage
        if -75.0 <= orig_lon <= -53.0 and not (-75.0 <= dest_lon <= -53.0):
            key_nodes.append(drake_pt)
        
        # Intermediate circumpolar arc points along transit_lat
        arc_diff = shortest_lon_diff(key_nodes[-1][1], exit_lon)
        num_arc_steps = max(6, int(abs(arc_diff) / 15.0))
        start_lon = key_nodes[-1][1]
        for s in range(1, num_arc_steps):
            frac = s / float(num_arc_steps)
            arc_lon = normalize_lon(start_lon + frac * arc_diff)
            # Ensure safe clearance past Drake Passage if passing Peninsula
            arc_lat = transit_lat
            if -72.0 <= arc_lon <= -53.0:
                arc_lat = max(arc_lat, -57.5) # Force north of Peninsula
            key_nodes.append((arc_lat, arc_lon))

        if not (-75.0 <= orig_lon <= -53.0) and (-75.0 <= dest_lon <= -53.0):
            key_nodes.append(drake_pt)

        if dest_lat < transit_lat:
            key_nodes.append((transit_lat, dest_lon))
        key_nodes.append((dest_lat, dest_lon))

        # Densify segments between key nodes
        for k in range(len(key_nodes) - 1):
            n0_lat, n0_lon = key_nodes[k]
            n1_lat, n1_lon = key_nodes[k + 1]
            seg_diff = shortest_lon_diff(n0_lon, n1_lon)
            seg_dist = haversine_distance_nm(n0_lat, n0_lon, n1_lat, n1_lon)
            sub_steps = max(1, int(seg_dist / 60.0))
            for ss in range(sub_steps):
                frac = ss / float(sub_steps)
                s_lat = n0_lat + frac * (n1_lat - n0_lat)
                s_lon = normalize_lon(n0_lon + frac * seg_diff)
                corridor_pts.append((round(s_lat, 4), round(s_lon, 4)))
        corridor_pts.append((dest_lat, dest_lon))

    # Evaluate physical progression along waypoints
    waypoints = []
    curr_time = departure_time
    cum_dist = 0.0
    cum_fuel = 0.0
    risk_values = []
    ice_hazard_exposures = []
    total_ice_nm = 0.0

    prev_lat, prev_lon = corridor_pts[0]
    for idx, (w_lat, w_lon) in enumerate(corridor_pts):
        pt = GeoPoint(latitude=w_lat, longitude=w_lon)
        env = env_prov.get_point_environment(pt, curr_time)

        sic = float(env.get("sea_ice_concentration", 0.0))
        depth = float(env.get("bathymetry_depth_m", 3000.0))
        wave_h = float(env.get("wave_height_m", 2.0))
        wind_spd = float(env.get("wind_speed_ms", 8.0))
        curr_u = float(env.get("current_u_ms", 0.0))
        curr_v = float(env.get("current_v_ms", 0.0))

        if idx == 0:
            leg_dist = 0.0
            heading = 0.0
            eff_speed = desired_speed
            dt_hours = 0.0
            leg_fuel = 0.0
        else:
            leg_dist = haversine_distance_nm(prev_lat, prev_lon, w_lat, w_lon)
            d_lon = shortest_lon_diff(prev_lon, w_lon)
            heading = math.degrees(math.atan2(d_lon * math.cos(math.radians((prev_lat + w_lat) / 2.0)), w_lat - prev_lat)) % 360.0

            speed_res = speed_model.calculate_segment_speed(
                vessel=vessel,
                distance_nm=leg_dist,
                heading_deg=heading,
                sic=sic,
                wave_height_m=wave_h,
                wind_speed_ms=wind_spd,
                current_u_ms=curr_u,
                current_v_ms=curr_v,
                desired_speed_knots=desired_speed,
            )
            eff_speed = speed_res.effective_speed_knots if speed_res.is_passable else 2.5
            dt_hours = leg_dist / max(0.5, eff_speed)
            curr_time += timedelta(hours=dt_hours)

            leg_fuel = fuel_model.estimate_leg_fuel(
                vessel=vessel,
                distance_nm=leg_dist,
                speed_knots=eff_speed,
                sic=sic,
                wave_height_m=wave_h,
            )
            cum_dist += leg_dist
            cum_fuel += leg_fuel

            if sic > 0.10:
                total_ice_nm += leg_dist

        # Compute risk at point
        iceberg_hz = 0.35 * sic + (0.15 if -68.0 <= w_lat <= -55.0 and -60.0 <= w_lon <= 0.0 else 0.05)
        local_risk = min(0.95, 0.05 + 0.55 * sic + 0.20 * (wave_h / 6.0) + 0.20 * iceberg_hz)
        risk_values.append(local_risk)
        ice_hazard_exposures.append(iceberg_hz)

        waypoints.append({
            "sequence": idx,
            "point": {"latitude": w_lat, "longitude": w_lon},
            "eta": curr_time.isoformat(),
            "speed_knots": round(eff_speed, 2),
            "leg_distance_nm": round(leg_dist, 2),
            "cumulative_distance_nm": round(cum_dist, 1),
            "leg_fuel_tonnes": round(leg_fuel, 3),
            "cumulative_fuel_tonnes": round(cum_fuel, 2),
            "local_risk": round(local_risk, 3),
            "ice_concentration": round(sic, 3),
            "bathymetry_depth_m": round(depth, 1)
        })

        prev_lat, prev_lon = w_lat, w_lon

    total_hours = (curr_time - departure_time).total_seconds() / 3600.0
    mean_risk = sum(risk_values) / max(1, len(risk_values))
    max_risk = max(risk_values) if risk_values else 0.05
    mean_iceberg_hazard = sum(ice_hazard_exposures) / max(1, len(ice_hazard_exposures))

    return {
        "objective": objective.value if hasattr(objective, "value") else str(objective),
        "waypoints": waypoints,
        "metrics": {
            "distance_nm": round(cum_dist, 1),
            "duration_hours": round(total_hours, 1),
            "duration_days": round(total_hours / 24.0, 2),
            "estimated_fuel_mt": round(cum_fuel, 1),
            "mean_risk": round(mean_risk, 3),
            "max_risk": round(max_risk, 3),
            "iceberg_hazard_exposure": round(mean_iceberg_hazard, 3),
            "sea_ice_exposure_percent": round((total_ice_nm / max(1.0, cum_dist)) * 100.0, 1)
        }
    }

# Test with difficult pairs
v = VesselProfile()
t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

test_cases = [
    ("punta-arenas", GeoPoint(latitude=-53.16, longitude=-70.92), "bharati", GeoPoint(latitude=-69.41, longitude=76.19)),
    ("mcmurdo", GeoPoint(latitude=-77.84, longitude=166.69), "punta-arenas", GeoPoint(latitude=-53.16, longitude=-70.92)),
    ("cape-town", GeoPoint(latitude=-33.92, longitude=18.42), "bharati", GeoPoint(latitude=-69.41, longitude=76.19)),
    ("hobart", GeoPoint(latitude=-42.88, longitude=147.33), "mcmurdo", GeoPoint(latitude=-77.84, longitude=166.69)),
]

for name1, p1, name2, p2 in test_cases:
    res = plan_maritime_voyage(p1, p2, t0, v, RouteObjective.FASTEST)
    wps = res["waypoints"]
    coords = [[w["point"]["longitude"], w["point"]["latitude"]] for w in wps]
    # Check land collision
    land_hits = 0
    for lon, lat in coords:
        lim = get_antarctic_land_limit_lat(lon)
        if lat < lim - 0.5:
            land_hits += 1
    print(f"\nVoyage {name1} -> {name2}:")
    print(f"  Waypoints: {len(wps)}, Distance: {res['metrics']['distance_nm']} NM, Duration: {res['metrics']['duration_days']} days, Fuel: {res['metrics']['estimated_fuel_mt']} MT")
    print(f"  Start: {coords[0]}")
    print(f"  Mid:   {coords[len(coords)//2]}")
    print(f"  End:   {coords[-1]}")
print("\n=== MULTI-OBJECTIVE COMPARISON: Cape Town -> Bharati ===")
for obj in [RouteObjective.FASTEST, RouteObjective.SHORTEST, RouteObjective.SAFEST, RouteObjective.FUEL_EFFICIENT, RouteObjective.BALANCED]:
    res = plan_maritime_voyage(GeoPoint(latitude=-33.92, longitude=18.42), GeoPoint(latitude=-69.41, longitude=76.19), t0, v, obj)
    m = res["metrics"]
    print(f"{obj.name:15s}: Dist={m['distance_nm']:6.1f} NM | Dur={m['duration_days']:5.2f}d | Fuel={m['estimated_fuel_mt']:5.1f} MT | MeanRisk={m['mean_risk']:.3f} | MaxRisk={m['max_risk']:.3f}")
