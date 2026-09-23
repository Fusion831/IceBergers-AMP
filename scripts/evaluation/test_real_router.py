"""Test the actual routing engine to understand its output."""
import sys
from pathlib import Path

root = Path(".").resolve()
for p in [
    "packages/core/src",
    "packages/domain/src",
    "packages/data_access/src",
    "packages/models/src",
    "packages/iceberg_physics/src",
    "packages/risk_engine/src",
    "packages/routing/src",
    "packages/services/src",
]:
    sys.path.insert(0, str(root / p))

# vessel module is at root level
sys.path.insert(0, str(root))

from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective
from datetime import datetime, timezone

T0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

from vessel.config import SAGAR_KANYA_VESSEL

print(f"Service speed: {SAGAR_KANYA_VESSEL.service_speed_knots} kt")
print(f"Max speed: {getattr(SAGAR_KANYA_VESSEL, 'max_speed_knots', 'N/A')}")
print(f"Balanced target: {getattr(SAGAR_KANYA_VESSEL, 'configured_balanced_target_speed_kt', 'N/A')}")
print()

planner = MissionPlanner()

for obj in [RouteObjective.SHORTEST, RouteObjective.FASTEST]:
    try:
        r = planner.plan_canonical_ncpor_mission(departure_time=T0, objective=obj)
        m = r.metrics
        segs = r.segments or []
        sog_vals = [s.get("speed_over_ground_knots", s.get("sog_kt", 0)) for s in segs]
        mean_sog = sum(sog_vals) / len(sog_vals) if sog_vals else 0
        sum_dist = sum(s.get("distance_nm", 0) for s in segs)
        sum_dur = sum(s.get("transit_duration_hours", s.get("segment_duration_hours", 0)) for s in segs)
        print(f"{obj.value}:")
        print(f"  Stored distance: {m.distance_nm} NM, sum_seg_dist: {sum_dist:.1f} NM")
        print(f"  Stored duration: {m.duration_hours:.1f}h ({m.duration_hours/24:.2f}d)")
        print(f"  Sum seg duration: {sum_dur:.1f}h ({sum_dur/24:.2f}d)")
        print(f"  Mean SOG from segments: {mean_sog:.2f} kt")
        print(f"  Derived SOG (dist/dur): {(sum_dist/sum_dur if sum_dur > 0 else 0):.2f} kt")
        print(f"  Fuel: {m.estimated_fuel_tonnes} MT")
        print(f"  Waypoints: {len(r.waypoints)}, Segments: {len(segs)}")
        if r.waypoints:
            print(f"  First wp: {r.waypoints[0].point.latitude:.2f},{r.waypoints[0].point.longitude:.2f}")
            print(f"  Last wp: {r.waypoints[-1].point.latitude:.2f},{r.waypoints[-1].point.longitude:.2f}")
        print()
    except Exception as e:
        print(f"{obj.value}: ERROR - {e}")
        import traceback
        traceback.print_exc()
        print()
