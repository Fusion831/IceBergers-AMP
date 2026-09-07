"""
Route Risk Aggregator for AMIP.
Calculates time-weighted risk integrals, tail percentiles (P90, P95, P99),
component exposures, and multi-iceberg encounter metrics along a trajectory.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from risk_engine.models import RiskProfile, RouteRiskProfile


def aggregate_route_risk(
    evaluations: List[Union[RiskProfile, Dict[str, Any]]],
    segment_durations_hours: Optional[List[float]] = None,
    policy_name: str = "AMIP_POC_BASELINE",
    policy_version: str = "1.0.0",
) -> RouteRiskProfile:
    """
    Aggregates a sequence of evaluated states/transitions into a canonical RouteRiskProfile.
    """
    if not evaluations:
        raise ValueError("Cannot aggregate risk for an empty route.")

    profiles: List[RiskProfile] = []
    for item in evaluations:
        if isinstance(item, RiskProfile):
            profiles.append(item)
        elif isinstance(item, dict):
            profiles.append(RiskProfile.model_validate(item))
        else:
            raise TypeError(f"Expected RiskProfile or dict, got {type(item)}")

    n_segments = len(profiles)

    # Determine durations for each segment
    durations: List[float] = []
    if segment_durations_hours and len(segment_durations_hours) == n_segments:
        durations = [max(0.001, float(d)) for d in segment_durations_hours]
    else:
        # Default 1.0 hour per segment if not specified
        durations = [1.0] * n_segments

    total_duration_hours = sum(durations)
    weights = np.array(durations) / max(0.001, total_duration_hours)

    comp_risks = np.array([p.composite_risk for p in profiles])
    conf_scores = np.array([p.confidence_score for p in profiles])

    # 1. Composite & Tail Risk
    mean_risk = float(np.mean(comp_risks))
    max_risk = float(np.max(comp_risks))
    time_weighted_mean_risk = float(np.sum(comp_risks * weights))
    risk_integral = float(np.sum(comp_risks * np.array(durations)))

    # Tail risk percentiles (descriptive statistics over time or segments)
    p90_risk = float(np.percentile(comp_risks, 90))
    p95_risk = float(np.percentile(comp_risks, 95))
    p99_risk = float(np.percentile(comp_risks, 99))

    high_risk_hours = float(sum(d for r, d in zip(comp_risks, durations) if r > 0.60))
    crit_risk_hours = float(sum(d for r, d in zip(comp_risks, durations) if r > 0.80))
    hard_blocks = sum(1 for p in profiles if p.hard_blocked)

    # 2. Component Exposures (Time-weighted integrals in component*hours)
    dur_arr = np.array(durations)
    sea_ice_exposure = float(np.sum([p.sea_ice_risk for p in profiles] * dur_arr))
    iceberg_exposure = float(np.sum([p.iceberg_risk for p in profiles] * dur_arr))
    wave_exposure = float(np.sum([p.wave_risk for p in profiles] * dur_arr))
    wind_exposure = float(np.sum([p.wind_risk for p in profiles] * dur_arr))
    current_exposure = float(np.sum([p.current_risk for p in profiles] * dur_arr))
    bathy_exposure = float(np.sum([p.bathymetric_risk for p in profiles] * dur_arr))

    # 3. Iceberg Hazard Specific Metrics
    hazards = np.array([p.iceberg_hazard for p in profiles])
    total_iceberg_hazard_exposure = float(np.sum(hazards * dur_arr))
    max_iceberg_hazard = float(np.max(hazards))
    time_above_hazard_threshold = float(sum(d for h, d in zip(hazards, durations) if h > 0.10))

    distinct_bergs_set = set()
    for p in profiles:
        distinct_bergs_set.update(p.contributing_iceberg_ids)
    distinct_bergs_list = sorted(list(distinct_bergs_set))
    distinct_count = len(distinct_bergs_list)

    # 4. Confidence Metrics
    mean_confidence = float(np.sum(conf_scores * weights))
    min_confidence = float(np.min(conf_scores))
    low_conf_hours = float(sum(d for c, d in zip(conf_scores, durations) if c < 0.50))

    # 5. Warning Summary
    all_warnings = []
    warn_summary: Dict[str, int] = {}
    for p in profiles:
        for code in p.warning_codes:
            warn_summary[code] = warn_summary.get(code, 0) + 1
            all_warnings.append(code)

    return RouteRiskProfile(
        total_duration_hours=round(total_duration_hours, 2),
        segment_count=n_segments,
        hard_block_count=hard_blocks,
        mean_risk=round(mean_risk, 4),
        max_risk=round(max_risk, 4),
        risk_integral=round(risk_integral, 4),
        time_weighted_mean_risk=round(time_weighted_mean_risk, 4),
        p90_risk=round(p90_risk, 4),
        p95_risk=round(p95_risk, 4),
        p99_risk=round(p99_risk, 4),
        high_risk_exposure_hours=round(high_risk_hours, 2),
        critical_exposure_hours=round(crit_risk_hours, 2),
        sea_ice_exposure=round(sea_ice_exposure, 4),
        iceberg_exposure=round(iceberg_exposure, 4),
        wave_exposure=round(wave_exposure, 4),
        wind_exposure=round(wind_exposure, 4),
        current_exposure=round(current_exposure, 4),
        bathymetric_exposure=round(bathy_exposure, 4),
        total_iceberg_hazard_exposure=round(total_iceberg_hazard_exposure, 4),
        max_iceberg_hazard=round(max_iceberg_hazard, 4),
        time_above_hazard_threshold_hours=round(time_above_hazard_threshold, 2),
        distinct_icebergs_encountered=distinct_bergs_list,
        distinct_iceberg_count=distinct_count,
        mean_confidence=round(mean_confidence, 4),
        minimum_confidence=round(min_confidence, 4),
        low_confidence_exposure_hours=round(low_conf_hours, 2),
        total_warnings_count=len(all_warnings),
        warning_code_summary=warn_summary,
        policy_name=policy_name,
        policy_version=policy_version,
    )
