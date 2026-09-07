"""
Route-Level Physical and Environmental Metrics Aggregator.
Aggregates a sequence of EdgeEvaluations into a comprehensive route summary.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from vessel.evaluator import EdgeEvaluation
from vessel.models import VesselProfile


class RoutePerformanceSummary(BaseModel):
    """
    Physical and operational summary of an evaluated route.
    Supplies physical measurements to the Router and Risk Engine.
    """
    # Core Trajectory Metrics
    total_distance_m: float = Field(..., description="Total route distance in meters")
    total_distance_nm: float = Field(..., description="Total route distance in nautical miles")
    total_time_hours: float = Field(..., description="Total voyage duration in hours")
    total_time_days: float = Field(..., description="Total voyage duration in decimal days")
    departure_time: str
    eta: str = Field(..., description="Estimated Time of Arrival (ISO 8601 UTC)")

    # Fuel & Endurance Checks
    total_fuel_mt: float = Field(..., description="Estimated total MGO fuel consumed in metric tonnes")
    total_fuel_m3: float = Field(..., description="Estimated total MGO fuel consumed in cubic meters")
    fuel_capacity_margin_pct: float = Field(..., description="Remaining bunker capacity percentage")
    fuel_capacity_exceeded: bool = Field(default=False)
    endurance_margin_days: float = Field(..., description="Remaining unassisted endurance days")
    endurance_exceeded: bool = Field(default=False)

    # Speed Statistics (Knots)
    mean_speed_kn: float
    min_speed_kn: float
    max_speed_kn: float

    # Environmental Extremes & Means
    max_sic: float = Field(..., description="Maximum sea ice concentration encountered [0.0, 1.0]")
    mean_sic: float = Field(..., description="Mean sea ice concentration encountered [0.0, 1.0]")
    max_wave_height_m: float = Field(..., description="Maximum significant wave height Hs encountered (m)")
    mean_wave_height_m: float = Field(..., description="Mean significant wave height Hs encountered (m)")
    max_wind_speed_ms: float = Field(..., description="Maximum wind speed encountered (m/s)")
    mean_wind_speed_ms: float = Field(..., description="Mean wind speed encountered (m/s)")

    # Currents
    total_current_assistance_hours: float = Field(..., description="Hours where current assisted along-track progression")
    total_current_penalty_hours: float = Field(..., description="Hours where current opposed progression")

    # Bathymetry & Under-Keel Clearance
    min_depth_m: Optional[float] = None
    min_clearance_m: Optional[float] = None

    # Hazards & Overall Feasibility
    iceberg_hazard_exposure: float = Field(default=0.0, description="Cumulative or peak iceberg hazard index")
    feasible: bool = Field(..., description="True if every constituent leg is physically feasible")
    infeasible_reasons: List[str] = Field(default_factory=list)
    all_warnings: List[str] = Field(default_factory=list)


def aggregate_route_metrics(
    evaluations: List[EdgeEvaluation],
    vessel: VesselProfile,
) -> RoutePerformanceSummary:
    """
    Computes comprehensive route-level metrics from a list of sequential edge evaluations.
    """
    if not evaluations:
        raise ValueError("Cannot aggregate empty route evaluations.")

    total_dist_m = sum(e.distance_m for e in evaluations)
    total_dist_nm = sum(e.distance_nm for e in evaluations)
    total_time_h = sum(e.travel_time_hours for e in evaluations)
    total_time_days = total_time_h / 24.0

    dep_time = evaluations[0].departure_time
    arr_time = evaluations[-1].arrival_time

    total_fuel_mt = sum(e.fuel_used for e in evaluations)
    total_fuel_m3 = sum(e.fuel_used_m3 for e in evaluations)

    # Endurance & Fuel margins
    max_bunker_m3 = vessel.fuel_capacity_m3
    fuel_margin_pct = max(0.0, ((max_bunker_m3 - total_fuel_m3) / max_bunker_m3) * 100.0)
    fuel_exceeded = total_fuel_m3 > max_bunker_m3

    max_endurance_d = vessel.endurance_days
    endurance_margin_d = max_endurance_d - total_time_days
    endurance_exceeded = total_time_days > max_endurance_d

    # Speed statistics
    speeds = [e.ground_speed_kn for e in evaluations]
    mean_spd = sum(speeds) / len(speeds) if speeds else 0.0
    min_spd = min(speeds) if speeds else 0.0
    max_spd = max(speeds) if speeds else 0.0

    # Sea ice
    sics = [e.sic for e in evaluations if e.sic is not None]
    max_sic = max(sics) if sics else 0.0
    mean_sic = sum(sics) / len(sics) if sics else 0.0

    # Waves
    waves = [e.wave_height for e in evaluations if e.wave_height is not None]
    max_wave = max(waves) if waves else 0.0
    mean_wave = sum(waves) / len(waves) if waves else 0.0

    # Wind
    winds = [e.wind_speed_ms for e in evaluations if e.wind_speed_ms is not None]
    max_wind = max(winds) if winds else 0.0
    mean_wind = sum(winds) / len(winds) if winds else 0.0

    # Currents assistance / penalty hours
    assist_h = sum(e.travel_time_hours for e in evaluations if e.current_assistance_kn > 0.0)
    oppose_h = sum(e.travel_time_hours for e in evaluations if e.current_assistance_kn < 0.0)

    # Bathymetry & clearance
    depths = [e.bathymetry_depth for e in evaluations if e.bathymetry_depth is not None]
    min_depth = min(depths) if depths else None
    clearances = [e.clearance for e in evaluations if e.clearance is not None]
    min_clear = min(clearances) if clearances else None

    # Feasibility
    is_feasible = all(e.feasible for e in evaluations) and not fuel_exceeded and not endurance_exceeded
    reasons = [e.reason for e in evaluations if not e.feasible and e.reason]
    if fuel_exceeded:
        reasons.append(f"Route exceeds bunker capacity ({total_fuel_m3:.1f}m3 > {max_bunker_m3:.1f}m3)")
    if endurance_exceeded:
        reasons.append(f"Route exceeds endurance limit ({total_time_days:.1f}d > {max_endurance_d}d)")

    # Deduplicate warnings
    seen_warnings = set()
    warnings = []
    for e in evaluations:
        for w in e.warnings:
            if w not in seen_warnings:
                seen_warnings.add(w)
                warnings.append(w)

    return RoutePerformanceSummary(
        total_distance_m=round(total_dist_m, 1),
        total_distance_nm=round(total_dist_nm, 2),
        total_time_hours=round(total_time_h, 3),
        total_time_days=round(total_time_days, 2),
        departure_time=dep_time,
        eta=arr_time,
        total_fuel_mt=round(total_fuel_mt, 3),
        total_fuel_m3=round(total_fuel_m3, 3),
        fuel_capacity_margin_pct=round(fuel_margin_pct, 1),
        fuel_capacity_exceeded=fuel_exceeded,
        endurance_margin_days=round(endurance_margin_d, 1),
        endurance_exceeded=endurance_exceeded,
        mean_speed_kn=round(mean_spd, 2),
        min_speed_kn=round(min_spd, 2),
        max_speed_kn=round(max_spd, 2),
        max_sic=round(max_sic, 3),
        mean_sic=round(mean_sic, 3),
        max_wave_height_m=round(max_wave, 2),
        mean_wave_height_m=round(mean_wave, 2),
        max_wind_speed_ms=round(max_wind, 2),
        mean_wind_speed_ms=round(mean_wind, 2),
        total_current_assistance_hours=round(assist_h, 2),
        total_current_penalty_hours=round(oppose_h, 2),
        min_depth_m=round(min_depth, 1) if min_depth is not None else None,
        min_clearance_m=round(min_clear, 1) if min_clear is not None else None,
        feasible=is_feasible,
        infeasible_reasons=reasons,
        all_warnings=warnings,
    )
