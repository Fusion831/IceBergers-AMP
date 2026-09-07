import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', '.'
])
import json
from datetime import datetime, timezone
from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective

t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
planner = MissionPlanner()

data = {}

for obj in [RouteObjective.FASTEST, RouteObjective.SHORTEST, RouteObjective.SAFEST, RouteObjective.FUEL_EFFICIENT, RouteObjective.BALANCED]:
    print(f"Exporting {obj.value}...")
    route = planner.plan_canonical_ncpor_mission(departure_time=t0, objective=obj)
    m = route.metrics
    
    waypoints_data = []
    for wp in route.waypoints:
        waypoints_data.append({
            "sequence": wp.sequence,
            "coords": [round(wp.point.longitude, 4), round(wp.point.latitude, 4)],
            "name": wp.point.name or f"WP-{wp.sequence}",
            "gridCellId": wp.grid_cell_id or f"CELL-{wp.sequence}",
            "distanceFromStartNM": wp.cumulative_distance_nm or 0.0,
            "legDistanceNM": wp.leg_distance_nm or 0.0,
            "eta": wp.eta.isoformat(),
            "speedKnots": round(wp.speed_knots, 2) if wp.speed_knots else 0.0,
            "fuelTonnes": round(wp.leg_fuel_tonnes, 2) if wp.leg_fuel_tonnes else 0.0,
            "cumulativeFuelTonnes": round(wp.cumulative_fuel_tonnes, 2) if wp.cumulative_fuel_tonnes else 0.0,
            "riskScore": round(wp.local_risk, 3) if wp.local_risk else 0.0,
            "iceConcentration": round(wp.ice_concentration * 100.0, 1) if wp.ice_concentration else 0.0,
            "depthM": wp.bathymetry_depth_m or 4200.0,
            "currentU": round(wp.current_u_ms, 2) if wp.current_u_ms else 0.0,
            "currentV": round(wp.current_v_ms, 2) if wp.current_v_ms else 0.0,
            "windSpeed": round(wp.wind_speed_ms, 1) if wp.wind_speed_ms else 0.0,
            "waveHeight": round(wp.wave_height_m, 1) if wp.wave_height_m else 0.0,
        })
        
    segments_data = []
    for i in range(1, len(route.waypoints)):
        p = route.waypoints[i-1]
        c = route.waypoints[i]
        segments_data.append({
            "segment_idx": i,
            "from_h3": p.grid_cell_id or f"CELL-{i-1}",
            "to_h3": c.grid_cell_id or f"CELL-{i}",
            "from_coords": [round(p.point.longitude, 4), round(p.point.latitude, 4)],
            "to_coords": [round(c.point.longitude, 4), round(c.point.latitude, 4)],
            "distance_nm": c.leg_distance_nm or 0.0,
            "sog": round(c.speed_knots, 2) if c.speed_knots else 0.0,
            "dt_hours": round((c.eta - p.eta).total_seconds() / 3600.0, 1),
            "sic_pct": round((c.ice_concentration or 0.0) * 100.0, 1),
            "current_u": round(c.current_u_ms or 0.0, 2),
            "current_v": round(c.current_v_ms or 0.0, 2),
            "wind_ms": round(c.wind_speed_ms or 0.0, 1),
            "wave_m": round(c.wave_height_m or 0.0, 1),
            "risk": round(c.local_risk or 0.0, 3),
            "fuel_mt": round(c.leg_fuel_tonnes or 0.0, 2),
            "cumulative_fuel_mt": round(c.cumulative_fuel_tonnes or 0.0, 2),
            "depth_m": c.bathymetry_depth_m or 4200.0,
            "eta_start": p.eta.isoformat(),
            "eta_end": c.eta.isoformat(),
        })
        
    data[obj.value] = {
        "id": obj.value.lower(),
        "objective": obj.value,
        "name": f"{obj.value.replace('_', ' ').title()} Mission Route",
        "distanceNM": m.distance_nm,
        "durationDays": m.duration_days,
        "durationHours": m.duration_hours,
        "estimatedFuelMT": m.estimated_fuel_tonnes,
        "meanRisk": m.mean_risk_score,
        "maxRisk": m.max_risk_score,
        "isFeasible": m.is_feasible,
        "h3CellsCount": len(route.cells),
        "waypointsCount": len(route.waypoints),
        "cells": route.cells,
        "waypoints": [[round(wp.point.longitude, 4), round(wp.point.latitude, 4)] for wp in route.waypoints],
        "waypointsDetail": waypoints_data,
        "segments": segments_data,
        "departureTime": route.waypoints[0].eta.isoformat(),
        "bharatiArrival": route.waypoints[16].eta.isoformat() if len(route.waypoints) > 16 else route.waypoints[-1].eta.isoformat(),
        "maitriArrival": route.waypoints[32].eta.isoformat() if len(route.waypoints) > 32 else route.waypoints[-1].eta.isoformat(),
        "capeTownReturn": route.waypoints[-1].eta.isoformat(),
    }

with open("frontend/src/data/canonical_routes.json", "w") as f:
    json.dump(data, f, indent=2)

print("Exported all 5 canonical routes successfully!")
