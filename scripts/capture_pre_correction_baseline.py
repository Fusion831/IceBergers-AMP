"""
Script to run the current backend exactly as-is and save the pre-correction baseline
for all five objectives: FASTEST, SHORTEST, SAFEST, FUEL_EFFICIENT, BALANCED.
"""

import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', '.'
])

import json
from datetime import datetime, timezone
from pathlib import Path

from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective

OUTPUT_PATH = Path("data/antarctica/poc/pre_correction_baseline.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

T0 = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
planner = MissionPlanner()

objectives = [
    (RouteObjective.FASTEST, "FASTEST"),
    (RouteObjective.SHORTEST, "SHORTEST"),
    (RouteObjective.SAFEST, "SAFEST"),
    (RouteObjective.FUEL_EFFICIENT, "FUEL_EFFICIENT"),
    (RouteObjective.BALANCED, "BALANCED"),
]

baseline_results = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "departure_time": T0.isoformat(),
    "description": "Pre-correction baseline run of AMIP router for all 5 canonical mission objectives before audit adjustments.",
    "routes": {}
}

for obj_enum, obj_name in objectives:
    print(f"Running baseline for {obj_name}...", flush=True)
    route = planner.plan_canonical_ncpor_mission(departure_time=T0, objective=obj_enum)
    m = route.metrics
    baseline_results["routes"][obj_name] = {
        "route_id": route.route_id,
        "objective": obj_name,
        "metrics": {
            "distance_nm": m.distance_nm,
            "duration_hours": m.duration_hours,
            "duration_days": m.duration_days,
            "estimated_fuel_tonnes": m.estimated_fuel_tonnes,
            "mean_risk_score": m.mean_risk_score,
            "max_risk_score": m.max_risk_score,
            "sea_ice_exposure_percent": m.sea_ice_exposure_percent,
            "iceberg_hazard_exposure": m.iceberg_hazard_exposure,
            "is_feasible": m.is_feasible,
        },
        "waypoints_count": len(route.waypoints),
        "cells_count": len(route.cells),
        "segments_count": len(route.segments),
        "explanation": route.explanation,
        "diagnostics": route.diagnostics,
    }

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(baseline_results, f, indent=2)

print(f"Pre-correction baseline successfully saved to {OUTPUT_PATH}")
