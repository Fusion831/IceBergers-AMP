"""
Iceberg Risk Evaluator based on H3 73-Iceberg Ensemble Occupancy Hazard.
Distinguishes raw ensemble occupancy hazard from certified collision probability.
"""

from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_iceberg_risk(
    iceberg_hazard: float = 0.0,
    distinct_iceberg_count: int = 0,
    contributing_iceberg_ids: Optional[List[str]] = None,
    ensemble_count: Optional[int] = None,
    policy: Optional[Any] = None,
) -> Tuple[float, str, List[RiskWarning], int, List[str]]:
    """
    Evaluates iceberg navigation risk from ensemble occupancy density.
    CRITICAL: Does NOT conflate ensemble occupancy samples with independent icebergs,
    nor does it claim to compute certified collision probability.
    Returns:
        iceberg_risk: float in [0.0, 1.0]
        status: str (SAFE, LOW, ELEVATED, HIGH, CRITICAL)
        warnings: List[RiskWarning]
        distinct_count: int
        contributing_ids: List[str]
    """
    warnings: List[RiskWarning] = []
    contributing_ids = contributing_iceberg_ids or []
    distinct_count = distinct_iceberg_count or len(contributing_ids)

    # Thresholds from policy
    safe_h = 0.02
    elev_h = 0.10
    high_h = 0.30
    crit_h = 0.60

    if policy and hasattr(policy, "thresholds"):
        berg_th = policy.thresholds.get("iceberg", {})
        if berg_th:
            safe_h = berg_th.get("safe_hazard", {}).value or safe_h
            elev_h = berg_th.get("elevated_hazard", {}).value or elev_h
            high_h = berg_th.get("high_hazard", {}).value or high_h
            crit_h = berg_th.get("critical_hazard", {}).value or crit_h

    raw_hazard = max(0.0, min(1.0, float(iceberg_hazard)))

    # Monotonic mapping from ensemble occupancy hazard proxy to risk
    if raw_hazard <= safe_h:
        base_risk = 0.0
        status = "SAFE"
    elif raw_hazard <= elev_h:
        base_risk = 0.20 * ((raw_hazard - safe_h) / max(0.001, elev_h - safe_h))
        status = "LOW"
    elif raw_hazard <= high_h:
        base_risk = 0.20 + 0.35 * ((raw_hazard - elev_h) / max(0.001, high_h - elev_h))
        status = "ELEVATED"
    elif raw_hazard <= crit_h:
        base_risk = 0.55 + 0.30 * ((raw_hazard - high_h) / max(0.001, crit_h - high_h))
        status = "HIGH"
    else:
        base_risk = 0.85 + 0.15 * min(1.0, (raw_hazard - crit_h) / max(0.001, 1.0 - crit_h))
        status = "CRITICAL"

    # Multi-iceberg confluence modulation: multiple distinct icebergs add operational vigilance cost
    if distinct_count > 1 and raw_hazard > safe_h:
        # Subtle non-linear bump for multi-iceberg proximity (max +0.10)
        multi_berg_factor = min(0.10, 0.03 * (distinct_count - 1))
        effective_risk = min(1.0, base_risk + multi_berg_factor)
    else:
        effective_risk = base_risk

    # Machine-readable warnings
    if status == "CRITICAL":
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.CRITICAL_ICEBERG_HAZARD,
                message=(
                    f"Critical predicted iceberg presence (hazard proxy={raw_hazard:.2f}) "
                    f"from {distinct_count} distinct iceberg(s): {', '.join(contributing_ids[:3])}"
                ),
                severity="CRITICAL",
                variable="iceberg_hazard",
                value=raw_hazard,
                threshold=crit_h,
            )
        )
    elif status == "HIGH":
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.HIGH_ICEBERG_HAZARD,
                message=(
                    f"High predicted iceberg occupancy (hazard proxy={raw_hazard:.2f}) "
                    f"from {distinct_count} distinct iceberg(s)"
                ),
                severity="WARNING",
                variable="iceberg_hazard",
                value=raw_hazard,
                threshold=high_h,
            )
        )

    return round(effective_risk, 4), status, warnings, distinct_count, contributing_ids
