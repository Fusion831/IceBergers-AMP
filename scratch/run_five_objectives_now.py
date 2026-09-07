import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', '.'
])
import json
import math
from datetime import datetime, timezone
import numpy as np
from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective
from data_access.sea_ice_provider import get_sea_ice_provider

t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
planner = MissionPlanner()

objectives = [
    RouteObjective.SHORTEST,
    RouteObjective.FASTEST,
    RouteObjective.SAFEST,
    RouteObjective.FUEL_EFFICIENT,
    RouteObjective.BALANCED,
]

results = []

for obj in objectives:
    print(f"Executing canonical mission for objective: {obj.value}...", flush=True)
    t_start = datetime.now()
    route = planner.plan_canonical_ncpor_mission(departure_time=t0, objective=obj)
    t_calc = (datetime.now() - t_start).total_seconds()
    m = route.metrics

    # Speeds and SOG analysis across segments
    sogs = []
    vessel_speeds = []
    segment_durations = []
    
    for i in range(1, len(route.waypoints)):
        p = route.waypoints[i-1]
        c = route.waypoints[i]
        d = c.leg_distance_nm or 0.0
        dt = (c.eta - p.eta).total_seconds() / 3600.0
        sog = c.speed_knots or (d / dt if dt > 0 else 0.0)
        sogs.append(sog)
        segment_durations.append(dt)
        
        # Calculate speed through water (vessel speed) by removing along-track current
        u = c.current_u_ms or 0.0
        v = c.current_v_ms or 0.0
        d_lat = c.point.latitude - p.point.latitude
        d_lon = c.point.longitude - p.point.longitude
        hdg = (math.degrees(math.atan2(d_lon, d_lat)) + 360.0) % 360.0
        rad = math.radians(hdg)
        along_track_current_kt = (u * math.sin(rad) + v * math.cos(rad)) * 1.94384
        v_stw = max(0.5, sog - along_track_current_kt)
        vessel_speeds.append(v_stw)

    # Waypoints: Bharati, Maitri, Cape Town
    bharati_arr = None
    maitri_arr = None
    for wp in route.waypoints:
        if abs(wp.point.latitude - (-69.40)) < 0.2 and abs(wp.point.longitude - 76.19) < 0.5:
            if bharati_arr is None:
                bharati_arr = wp.eta
        if abs(wp.point.latitude - (-69.95)) < 0.2 and abs(wp.point.longitude - 11.73) < 0.5:
            if maitri_arr is None:
                maitri_arr = wp.eta

    dep_time = route.waypoints[0].eta
    ret_time = route.waypoints[-1].eta

    record = {
        "objective": obj.value,
        "route_success": True,
        "feasible": m.is_feasible,
        "distance_nm": round(m.distance_nm, 1),
        "total_duration_hours": round(m.duration_hours, 1),
        "total_duration_days": round(m.duration_days, 2),
        "departure_time": dep_time.isoformat(),
        "arrival_time": ret_time.isoformat(),
        "eta": ret_time.strftime("%Y-%m-%d %H:%M UTC"),
        "fuel_estimate_tonnes": round(m.estimated_fuel_tonnes, 1),
        "mean_risk": round(m.mean_risk_score, 3),
        "max_risk": round(m.max_risk_score, 3),
        "h3_cell_count": len(route.cells),
        "segment_count": len(route.waypoints) - 1,
        "bharati_arrival": bharati_arr.isoformat() if bharati_arr else "N/A",
        "bharati_dwell_hours": 48.0,
        "maitri_arrival": maitri_arr.isoformat() if maitri_arr else "N/A",
        "maitri_dwell_hours": 72.0,
        "cape_town_return": ret_time.isoformat(),
        "mean_vessel_speed_stw": round(float(np.mean(vessel_speeds)), 2) if vessel_speeds else 0.0,
        "mean_sog": round(float(np.mean(sogs)), 2) if sogs else 0.0,
        "min_sog": round(float(np.min(sogs)), 2) if sogs else 0.0,
        "max_sog": round(float(np.max(sogs)), 2) if sogs else 0.0,
        "min_segment_speed": round(float(np.min(sogs)), 2) if sogs else 0.0,
        "max_segment_speed": round(float(np.max(sogs)), 2) if sogs else 0.0,
        "calculation_duration_seconds": round(t_calc, 2),
    }
    results.append(record)
    print(f" -> {obj.value}: Dist={record['distance_nm']} NM, Days={record['total_duration_days']} d, Fuel={record['fuel_estimate_tonnes']} MT, MeanRisk={record['mean_risk']}, MeanSOG={record['mean_sog']} kt, Cells={record['h3_cell_count']}", flush=True)

with open("scratch/canonical_five_objectives_benchmark.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nALL FIVE OBJECTIVES COMPLETED SUCCESSFULLY!", flush=True)
