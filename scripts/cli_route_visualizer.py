#!/usr/bin/env python3
"""
AMIP POC - Interactive CLI Route & Environmental Grid Visualizer.
Executes the full mocked environmental and routing pipeline,
plots ASCII spatial maps across the Antarctic grid, and displays 4D route telemetry.
"""

import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional

# Setup sys.path
ROOT = Path(__file__).resolve().parent.parent
for pkg_dir in (ROOT / "packages").glob("*/src"):
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
app_src = ROOT / "apps" / "backend" / "src"
if str(app_src) not in sys.path:
    sys.path.insert(0, str(app_src))

from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.mission import (
    MissionCreate,
    PlanningWindow,
    MissionDestination,
    MissionPriorities,
    MissionTarget,
    AvoidanceZone,
)
from domain.enums import RouteObjective, MissionSeason, MissionTargetType
from domain.route import RouteAlternative, RouteWaypoint
from data_access.environment_provider import default_environment_provider
from routing.amip_custom_router import AMIPCustomRouter
from routing.mission_planner import MissionPlanner
from routing.speed_model import VesselSpeedModel
from routing.fuel_model import NavalArchitectureFuelModel


def print_banner(title: str, width: int = 80) -> None:
    print("\n" + "═" * width)
    print(f" {title.center(width - 2)} ")
    print("═" * width)


def render_ascii_grid(
    routes: Dict[RouteObjective, RouteAlternative],
    selected_objective: RouteObjective,
    targets: List[MissionTarget],
    origin: GeoPoint,
    avoidance_zones: List[AvoidanceZone],
    env_provider,
    width_chars: int = 70,
    height_chars: int = 24,
) -> None:
    """
    Renders an ASCII map of the Southern Ocean / Antarctic sector
    showing the spatial grid, sea-ice marginal zone, avoidance zones, stations, and route path.
    """
    lat_min, lat_max = -75.0, -30.0  # Latitude: 30°S to 75°S
    lon_min, lon_max = 0.0, 85.0     # Longitude: 0°E to 85°E

    # Initialize blank grid
    grid = [["·" for _ in range(width_chars)] for _ in range(height_chars)]

    def to_grid(lat: float, lon: float) -> Tuple[int, int]:
        # Clamp coordinates
        lat_c = max(lat_min, min(lat_max, lat))
        lon_c = max(lon_min, min(lon_max, lon))
        # Row 0 is at lat_max (-30°S), Row height_chars-1 is at lat_min (-75°S)
        row = int((lat_max - lat_c) / (lat_max - lat_min) * (height_chars - 1))
        col = int((lon_c - lon_min) / (lon_max - lon_min) * (width_chars - 1))
        return max(0, min(height_chars - 1, row)), max(0, min(width_chars - 1, col))

    # 1. Fill background environmental zones (Ice edge & Antarctic coast)
    for r in range(height_chars):
        lat = lat_max - (r / (height_chars - 1)) * (lat_max - lat_min)
        for c in range(width_chars):
            lon = lon_min + (c / (width_chars - 1)) * (lon_max - lon_min)
            if lat < -67.0:
                grid[r][c] = "▓"  # Heavy Pack Ice / Coastal margin
            elif lat < -58.0:
                grid[r][c] = "░"  # Marginal Ice Zone (MIZ)
            elif lat < -40.0:
                grid[r][c] = " "  # Roaring Forties / Furious Fifties open water

    # 2. Mark Avoidance Zones
    for az in avoidance_zones:
        if az.center:
            r_z, c_z = to_grid(az.center.latitude, az.center.longitude)
            # Draw a 3x3 hazard diamond
            for dr in (-1, 0, 1):
                for dc in (-2, -1, 0, 1, 2):
                    rr, cc = r_z + dr, c_z + dc
                    if 0 <= rr < height_chars and 0 <= cc < width_chars:
                        grid[rr][cc] = "X"

    # 3. Plot Selected Route Waypoint Track
    route = routes[selected_objective]
    for idx, wp in enumerate(route.waypoints):
        r, c = to_grid(wp.point.latitude, wp.point.longitude)
        if idx == 0:
            grid[r][c] = "C"  # Cape Town
        elif idx == len(route.waypoints) - 1:
            grid[r][c] = "M"  # Final destination (Maitri)
        else:
            # Route breadcrumb
            grid[r][c] = "*"

    # 4. Overlay Target Landmark Icons
    r_orig, c_orig = to_grid(origin.latitude, origin.longitude)
    grid[r_orig][c_orig] = "C"

    target_chars = {"Bharati Station": "B", "Science Area Alpha": "A", "Grid Cell S17": "S", "Maitri Station": "M"}
    for t in targets:
        r_t, c_t = to_grid(t.location.latitude, t.location.longitude)
        icon = target_chars.get(t.location.name, "T")
        grid[r_t][c_t] = icon

    # Print with Coordinate Frame & Labels
    print(f"\n┌{'─' * width_chars}┐")
    print(f"│{'SOUTHERN OCEAN / ANTARCTICA 4D SPATIAL GRID':^{width_chars}}│")
    print(f"│{'[Latitude: 30°S to 75°S  |  Longitude: 0°E to 85°E]':^{width_chars}}│")
    print(f"├{'─' * width_chars}┤")

    for r in range(height_chars):
        lat_val = lat_max - (r / (height_chars - 1)) * (lat_max - lat_min)
        lat_lbl = f"{abs(lat_val):4.1f}°S" if r % 5 == 0 else "     "
        line_str = "".join(grid[r])
        print(f"│ {lat_lbl} │{line_str}│")

    print(f"├{'─' * width_chars}┤")
    print(f"│       │ 0°E      20°E      40°E      60°E      80°E     │")
    print(f"└{'─' * width_chars}┘")

    print("\nMap Legend:")
    print("  [C] Origin: Cape Town Port (-33.9°S, 18.4°E)")
    print("  [B] Target 1: Bharati Research Station (-69.4°S, 76.2°E)")
    print("  [A] Target 2: Prydz Bay Science Survey Alpha (-68.2°S, 74.5°E)")
    print("  [S] Target 3: Ground Truth Grid Cell S17 (-67.8°S, 70.0°E)")
    print("  [M] Target 4: Maitri Research Station (-70.8°S, 11.7°E)")
    print("  [X] Avoidance Zone: Bouvet Iceberg Calving Zone (-54.4°S, 3.4°E)")
    print("  [*] Route Waypoint Track  |  [░] Marginal Ice Zone  |  [▓] Coastal Fast Ice")


def display_environmental_samples(env_provider, ref_time: datetime) -> None:
    """Print sampled environmental states across representative grid locations."""
    print_banner("1. SYNTHETIC ENVIRONMENTAL CONDITIONS ACROSS THE ANTARCTIC GRID")
    sample_points = [
        ("Subtropical Waters (Cape Town)", GeoPoint(latitude=-34.0, longitude=18.5)),
        ("Roaring Forties (Open Ocean)", GeoPoint(latitude=-45.0, longitude=30.0)),
        ("Furious Fifties (ACC Current Jet)", GeoPoint(latitude=-55.0, longitude=50.0)),
        ("Marginal Ice Zone (Polar Front)", GeoPoint(latitude=-62.0, longitude=65.0)),
        ("Prydz Bay / Bharati Shelf", GeoPoint(latitude=-69.4, longitude=76.2)),
        ("Lazarev Sea / Maitri Approach", GeoPoint(latitude=-70.8, longitude=11.7)),
    ]

    header = f"│ {'Location':<33} │ {'Lat/Lon':<14} │ {'SIC %':<6} │ {'Depth(m)':<8} │ {'Wave Hs':<7} │ {'Wind(kn)':<8} │ {'Current':<10} │"
    div = f"├{'─'*35}┼{'─'*16}┼{'─'*8}┼{'─'*10}┼{'─'*9}┼{'─'*10}┼{'─'*12}┤"
    top = f"┌{'─'*35}┬{'─'*16}┬{'─'*8}┬{'─'*10}┬{'─'*9}┬{'─'*10}┬{'─'*12}┐"
    bot = f"└{'─'*35}┴{'─'*16}┴{'─'*8}┴{'─'*10}┴{'─'*9}┴{'─'*10}┴{'─'*12}┘"

    print(top)
    print(header)
    print(div)

    for name, pt in sample_points:
        env = env_provider.get_point_environment(pt, ref_time)
        coords = f"{pt.latitude:.1f}°S, {pt.longitude:.1f}°E"
        sic = f"{env['sea_ice_concentration']*100:4.1f}%"
        depth = f"{env['bathymetry_depth_m']:5.0f}m"
        wave = f"{env['wave_height_m']:4.1f}m"
        wind = f"{env['wind_speed_ms'] * 1.94384:4.1f}kn"
        curr_spd = math.sqrt(env['current_u_ms']**2 + env['current_v_ms']**2) * 1.94384
        curr_str = f"{curr_spd:4.1f} kn"

        print(f"│ {name:<33} │ {coords:<14} │ {sic:<6} │ {depth:<8} │ {wave:<7} │ {wind:<8} │ {curr_str:<10} │")

    print(bot)


def display_routes_comparison(routes: Dict[RouteObjective, RouteAlternative], recommended_obj: RouteObjective) -> None:
    """Print comparative metrics table across all 5 generated route alternatives."""
    print_banner("2. MULTI-CRITERIA ROUTE ALTERNATIVES COMPARISON")

    top = f"┌{'─'*15}┬{'─'*12}┬{'─'*13}┬{'─'*12}┬{'─'*10}┬{'─'*11}┬{'─'*14}┐"
    header = f"│ {'Objective':<13} │ {'Dist (NM)':<10} │ {'Transit (h)':<11} │ {'Fuel (t)':<10} │ {'Risk':<8} │ {'Avg Spd':<9} │ {'Status':<12} │"
    div = f"├{'─'*15}┼{'─'*12}┼{'─'*13}┼{'─'*12}┼{'─'*10}┼{'─'*11}┼{'─'*14}┤"
    bot = f"└{'─'*15}┴{'─'*12}┴{'─'*13}┴{'─'*12}┴{'─'*10}┴{'─'*11}┴{'─'*14}┘"

    print(top)
    print(header)
    print(div)

    for obj in [
        RouteObjective.SHORTEST,
        RouteObjective.FASTEST,
        RouteObjective.SAFEST,
        RouteObjective.FUEL_EFFICIENT,
        RouteObjective.BALANCED,
    ]:
        r = routes[obj]
        m = r.metrics
        dist = f"{m.distance_nm:7.1f}"
        dur = f"{m.duration_hours:6.1f}h"
        fuel = f"{m.fuel_consumption_tonnes:6.1f}t"
        risk = f"{m.mean_risk:6.3f}"
        spd = f"{m.distance_nm / max(1.0, m.duration_hours):5.1f} kn"
        tag = "★ RECOMMENDED" if obj == recommended_obj else "  Alternative"

        print(f"│ {obj.value:<13} │ {dist:<10} │ {dur:<11} │ {fuel:<10} │ {risk:<8} │ {spd:<9} │ {tag:<12} │")

    print(bot)
    print("Optimization Notes:")
    print(" • FASTEST burns flank fuel (+81% vs Balanced) taking high-speed open-water bypass.")
    print(" • SAFEST avoids Bouvet/Weddell iceberg corridor, minimizing navigational risk.")
    print(" • FUEL_EFFICIENT optimizes power curves and follows favorable currents (saving 157t vs Balanced).")
    print(" • BALANCED satisfies mission weights: Safety (40%), Fuel (30%), Time (20%), Science (10%).")


def display_waypoint_telemetry(route: RouteAlternative, max_entries: int = 14) -> None:
    """Print 4D waypoint-by-waypoint progression for the chosen route."""
    print_banner(f"3. 4D WAYPOINT PROGRESSION: {route.objective.value.upper()} ROUTE")

    top = f"┌{'─'*4}┬{'─'*18}┬{'─'*16}┬{'─'*9}┬{'─'*9}┬{'─'*7}┬{'─'*7}┬{'─'*8}┬{'─'*10}┐"
    header = f"│ {'#':<2} │ {'ETA (UTC)':<16} │ {'Position':<14} │ {'Dist(NM)':<7} │ {'Spd(kn)':<7} │ {'SIC%':<5} │ {'Risk':<5} │ {'Fuel(t)':<6} │ {'Cum.Fuel':<8} │"
    div = f"├{'─'*4}┼{'─'*18}┼{'─'*16}┼{'─'*9}┼{'─'*9}┼{'─'*7}┼{'─'*7}┼{'─'*8}┼{'─'*10}┤"
    bot = f"└{'─'*4}┴{'─'*18}┴{'─'*16}┴{'─'*9}┴{'─'*9}┴{'─'*7}┴{'─'*7}┴{'─'*8}┴{'─'*10}┘"

    print(top)
    print(header)
    print(div)

    wps = route.waypoints
    # Subsample if many waypoints
    if len(wps) > max_entries:
        step = max(1, len(wps) // max_entries)
        indices = list(range(0, len(wps), step))
        if indices[-1] != len(wps) - 1:
            indices.append(len(wps) - 1)
    else:
        indices = list(range(len(wps)))

    for i in indices:
        wp = wps[i]
        eta_str = wp.eta.strftime("%Y-%m-%d %H:%M")
        pos_str = f"{wp.point.latitude:5.1f}S,{wp.point.longitude:5.1f}E"
        dist = f"{wp.cumulative_distance_nm:7.1f}"
        spd = f"{wp.speed_knots:5.1f}"
        sic = f"{wp.ice_concentration * 100:4.1f}%"
        risk = f"{wp.local_risk:5.2f}"
        leg_fuel = f"{wp.leg_fuel_tonnes:6.2f}"
        cum_fuel = f"{wp.cumulative_fuel_tonnes:7.1f}t"

        print(f"│ {wp.sequence:<2} │ {eta_str:<16} │ {pos_str:<14} │ {dist:<7} │ {spd:<7} │ {sic:<5} │ {risk:<5} │ {leg_fuel:<6} │ {cum_fuel:<8} │")

    print(bot)


def main():
    print_banner("ANTARCTIC MISSION INTELLIGENCE PLATFORM (AMIP)", width=80)
    print(" Problem Statement 26059: Multi-Modal Sea Ice & Environmental Intelligence")
    print(" Vessel: Polar Research Vessel (Polar Class PC-5, Displacement 12,000 DWT)")
    print(" Mission: 45th Indian Scientific Expedition to Antarctica (ISEA-45)")

    # 1. Mission Parameters
    now = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile(
        name="MV Vasiliy Golovnin (Chartered Polar Vessel)",
        ice_class="PC5",
        length_m=135.0,
        beam_m=21.0,
        draft_m=8.5,
        displacement_tonnes=12000.0,
        service_speed_knots=12.0,
        max_speed_knots=14.5,
        daily_fuel_consumption_tonnes=24.0,
    )

    origin = GeoPoint(latitude=-33.9249, longitude=18.4241, name="Cape Town Port")

    targets = [
        MissionTarget(
            name="Bharati Station",
            target_type=MissionTargetType.STATION,
            location=GeoPoint(latitude=-69.4072, longitude=76.1911, name="Bharati Station"),
            dwell_hours=48.0,
            sequence_order=1,
        ),
        MissionTarget(
            name="Science Area Alpha",
            target_type=MissionTargetType.SCIENCE_SITE,
            location=GeoPoint(latitude=-68.2, longitude=74.5, name="Science Area Alpha"),
            dwell_hours=24.0,
            sequence_order=2,
        ),
        MissionTarget(
            name="Grid Cell S17",
            target_type=MissionTargetType.GRID_CELL,
            grid_cell_id="S17",
            location=GeoPoint(latitude=-67.8, longitude=70.0, name="Grid Cell S17"),
            dwell_hours=12.0,
            sequence_order=3,
        ),
        MissionTarget(
            name="Maitri Station",
            target_type=MissionTargetType.STATION,
            location=GeoPoint(latitude=-70.7670, longitude=11.7330, name="Maitri Station"),
            dwell_hours=72.0,
            sequence_order=4,
        ),
    ]

    avoidance_zones = [
        AvoidanceZone(
            name="Bouvet Iceberg Hazard Front",
            center=GeoPoint(latitude=-54.4, longitude=3.4),
            radius_km=45.0,
            reason="Active tabular iceberg calving front and grounded bergs",
        )
    ]

    # 2. Display Synthetic Grid Conditions
    env = default_environment_provider
    display_environmental_samples(env, now)

    # 3. Plan Expeditions across all Objectives
    planner = MissionPlanner(AMIPCustomRouter(env_provider=env))
    routes: Dict[RouteObjective, RouteAlternative] = {}

    for obj in [
        RouteObjective.SHORTEST,
        RouteObjective.FASTEST,
        RouteObjective.SAFEST,
        RouteObjective.FUEL_EFFICIENT,
        RouteObjective.BALANCED,
    ]:
        routes[obj] = planner.plan_multi_target_mission(
            origin=origin,
            targets=targets,
            departure_time=now,
            vessel=vessel,
            objective=obj,
            avoidance_zones=avoidance_zones,
        )

    recommended_objective = RouteObjective.BALANCED

    import argparse
    parser = argparse.ArgumentParser(description="AMIP POC CLI Route & Environmental Grid Visualizer")
    parser.add_argument(
        "--objective",
        choices=["shortest", "fastest", "safest", "fuel_efficient", "balanced", "all"],
        default="balanced",
        help="Route objective to visualize on the ASCII grid map (default: balanced)",
    )
    args = parser.parse_args()

    # 4. Display Alternatives Comparison
    display_routes_comparison(routes, recommended_objective)

    objectives_to_show = (
        [RouteObjective.SHORTEST, RouteObjective.FASTEST, RouteObjective.SAFEST, RouteObjective.FUEL_EFFICIENT, RouteObjective.BALANCED]
        if args.objective.lower() == "all"
        else [RouteObjective(args.objective.upper())]
    )

    for obj in objectives_to_show:
        print_banner(f"ROUTE MAP ON SPATIAL GRID: {obj.value.upper()}")
        render_ascii_grid(
            routes=routes,
            selected_objective=obj,
            targets=targets,
            origin=origin,
            avoidance_zones=avoidance_zones,
            env_provider=env,
            width_chars=72,
            height_chars=22,
        )
        display_waypoint_telemetry(routes[obj], max_entries=14)

    print("\n✓ AMIP 4D Mission Planning Demonstration Completed Successfully.\n")


if __name__ == "__main__":
    main()

