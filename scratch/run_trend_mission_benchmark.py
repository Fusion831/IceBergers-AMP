import sys
sys.path.extend([
    'packages/core/src', 'packages/domain/src', 'packages/data_access/src',
    'packages/models/src', 'packages/iceberg_physics/src', 'packages/risk_engine/src',
    'packages/routing/src', 'packages/services/src', '.'
])
from datetime import datetime, timezone
import numpy as np
from routing.mission_planner import MissionPlanner
from domain.enums import RouteObjective
from data_access.sea_ice_provider import get_sea_ice_provider

t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

def evaluate_objectives(scenario_name="historical_trend_normal"):
    print("=" * 110)
    print(f"EVALUATING CANONICAL NCPOR EXPEDITION UNDER SCENARIO: {scenario_name}")
    print("=" * 110)
    
    prov = get_sea_ice_provider(source="synthetic_trend", scenario=scenario_name)
    planner = MissionPlanner()
    planner.router.env.sea_ice_provider = prov
    
    objectives = [
        RouteObjective.SHORTEST,
        RouteObjective.FASTEST,
        RouteObjective.SAFEST,
        RouteObjective.FUEL_EFFICIENT,
        RouteObjective.BALANCED,
    ]
    
    results = []
    
    for obj in objectives:
        route = planner.plan_canonical_ncpor_mission(departure_time=t0, objective=obj)
        m = route.metrics
        
        # Calculate speeds & SOG
        speeds = [wp.speed_knots for wp in route.waypoints if wp.speed_knots is not None and wp.speed_knots > 0]
        sog_avg = float(np.mean(speeds)) if speeds else 0.0
        sog_min = float(np.min(speeds)) if speeds else 0.0
        sog_max = float(np.max(speeds)) if speeds else 0.0
        
        # Station visits and dwell
        # Waypoints: Bharati is target 1, Maitri is target 2, Cape Town return is target 3
        # Look for the station arrival waypoints
        bharati_wp = None
        maitri_wp = None
        for wp in route.waypoints:
            if abs(wp.point.latitude - (-69.40)) < 0.2 and abs(wp.point.longitude - 76.19) < 0.5:
                if bharati_wp is None:
                    bharati_wp = wp
            if abs(wp.point.latitude - (-69.95)) < 0.2 and abs(wp.point.longitude - 11.73) < 0.5:
                if maitri_wp is None:
                    maitri_wp = wp
                    
        return_wp = route.waypoints[-1]
        
        res = {
            "objective": obj.value,
            "success": True,
            "feasible": m.is_feasible,
            "distance_nm": m.distance_nm,
            "duration_days": m.duration_days,
            "duration_hours": m.duration_hours,
            "eta": return_wp.eta.strftime("%Y-%m-%d %H:%M UTC"),
            "fuel_mt": m.estimated_fuel_tonnes,
            "mean_risk": m.mean_risk_score,
            "max_risk": m.max_risk_score,
            "h3_cells": len(route.cells),
            "segments": len(route.segments) if route.segments else len(route.waypoints) - 1,
            "sog_avg": round(sog_avg, 2),
            "sog_min": round(sog_min, 2),
            "sog_max": round(sog_max, 2),
            "bharati_arr": bharati_wp.eta.strftime("%Y-%m-%d %H:%M") if bharati_wp else "N/A",
            "maitri_arr": maitri_wp.eta.strftime("%Y-%m-%d %H:%M") if maitri_wp else "N/A",
            "return_arr": return_wp.eta.strftime("%Y-%m-%d %H:%M"),
        }
        results.append(res)
        
        print(f"Objective: {obj.value:<15} | Dist: {m.distance_nm:6.1f} NM | Dur: {m.duration_days:5.2f} d ({m.duration_hours:6.1f} h) | Fuel: {m.estimated_fuel_tonnes:6.1f} MT | Risk: {m.mean_risk_score:.3f} (max {m.max_risk_score:.3f}) | SOG: {sog_avg:4.2f} kt (min {sog_min:4.2f}, max {sog_max:4.2f}) | H3 Cells: {len(route.cells)}")
        
    return results

if __name__ == "__main__":
    normal_res = evaluate_objectives("historical_trend_normal")
    low_res = evaluate_objectives("historical_trend_low_ice")
    high_res = evaluate_objectives("historical_trend_high_ice")
