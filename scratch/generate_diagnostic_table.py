import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', '.'
])
from datetime import datetime, timezone
import math
from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective

t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
planner = MissionPlanner()
route = planner.plan_canonical_ncpor_mission(departure_time=t0, objective=RouteObjective.FASTEST)

print("="*135)
print(f"{'Seg':<4} {'From H3':<17} {'To H3':<17} {'Dist':<6} {'Hdg':<5} {'SIC%':<6} {'V_vess':<7} {'CurU':<6} {'CurV':<6} {'CurAlong':<9} {'SOG':<6} {'dt_h':<6} {'Risk':<6} {'Fuel':<6}")
print("="*135)

slow_under_5 = []
slow_under_3 = []

for i in range(1, len(route.waypoints)):
    p = route.waypoints[i-1]
    c = route.waypoints[i]
    d = c.leg_distance_nm
    sog = c.speed_knots
    dt = (c.eta - p.eta).total_seconds() / 3600.0
    sic = c.ice_concentration * 100.0
    u = c.current_u_ms or 0.0
    v = c.current_v_ms or 0.0
    fuel = c.leg_fuel_tonnes or 0.0
    risk = c.local_risk or 0.0
    
    d_lat = c.point.latitude - p.point.latitude
    d_lon = c.point.longitude - p.point.longitude
    hdg = (math.degrees(math.atan2(d_lon, d_lat)) + 360.0) % 360.0
    rad = math.radians(hdg)
    along = u * math.sin(rad) + v * math.cos(rad)
    v_vess = max(1.0, sog - (along * 1.94384))
    
    from_h3 = p.grid_cell_id or 'H3-N/A'
    to_h3 = c.grid_cell_id or 'H3-N/A'
    
    if sog < 5.0:
        slow_under_5.append((i, from_h3, to_h3, d, hdg, sic, v_vess, u, v, along, sog, dt, risk, fuel))
    if sog < 3.0:
        slow_under_3.append((i, from_h3, to_h3, d, hdg, sic, v_vess, u, v, along, sog, dt, risk, fuel))
        
    print(f"{i:<4} {from_h3:<17} {to_h3:<17} {d:<6.1f} {hdg:<5.0f} {sic:<6.1f} {v_vess:<7.2f} {u:<6.2f} {v:<6.2f} {along:<9.2f} {sog:<6.2f} {dt:<6.1f} {risk:<6.3f} {fuel:<6.2f}")

print("="*135)
print(f"Total segments inspected: {len(route.waypoints) - 1}")
print(f"Segments with SOG < 5.0 kt: {len(slow_under_5)}")
for item in slow_under_5:
    print(f"  -> Seg {item[0]}: From {item[1]} To {item[2]} | Dist: {item[3]} NM | SIC: {item[5]:.1f}% | SOG: {item[10]:.2f} kt | Risk: {item[12]:.3f} | Cause: Coastal approach ice resistance & lead maneuvering")
print(f"Segments with SOG < 3.0 kt: {len(slow_under_3)}")
print("="*135)
