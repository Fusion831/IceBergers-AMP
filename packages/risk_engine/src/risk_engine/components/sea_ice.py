"""
Sea-Ice Risk Evaluator based on SIC, SIC Uncertainty, and Vessel Operating Policy.
Monotonically maps sea-ice concentration to risk while tracking provenance and mock status.
"""

from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_sea_ice_risk(
    sic: Optional[float],
    sic_uncertainty: Optional[float] = None,
    sic_source: str = "OBSERVED",
    policy: Optional[Any] = None,
    vessel: Optional[Any] = None,
) -> Tuple[float, bool, Optional[str], Optional[str], str, float, List[RiskWarning]]:
    """
    Evaluates sea-ice risk monotonically against configured thresholds and vessel limits.
    Returns:
        sea_ice_risk: float in [0.0, 1.0]
        hard_blocked: bool
        block_reason: Optional[str]
        blocking_rule: Optional[str]
        status: str (SAFE, ELEVATED, HIGH, CRITICAL, UNKNOWN)
        confidence_factor: float in [0.0, 1.0]
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []

    if sic is None:
        return 0.0, False, None, None, "UNKNOWN", 0.0, warnings

    # Normalize SIC to fraction [0.0, 1.0] if provided as percentage
    sic_fraction = sic / 100.0 if sic > 1.0 else max(0.0, float(sic))
    unc_fraction = (sic_uncertainty / 100.0 if sic_uncertainty > 1.0 else float(sic_uncertainty)) if sic_uncertainty is not None else 0.05

    # Check provenance
    if str(sic_source).upper() in {"MOCK", "SYNTHETIC"}:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.MOCK_SIC,
                message="Sea ice concentration is derived from mock/synthetic provider; not verified observed/ML data",
                severity="INFO",
                variable="sic_source",
            )
        )

    # Thresholds from policy
    safe_thresh = 0.0
    elevated_thresh = 0.05
    high_thresh = 0.15
    crit_thresh = 0.40
    unc_scale = 0.50

    if policy and hasattr(policy, "thresholds"):
        ice_th = policy.thresholds.get("sea_ice", {})
        if ice_th:
            safe_thresh = ice_th.get("safe_fraction", {}).value or safe_thresh
            elevated_thresh = ice_th.get("elevated_fraction", {}).value or elevated_thresh
            high_thresh = ice_th.get("high_fraction", {}).value or high_thresh
            crit_thresh = ice_th.get("critical_fraction", {}).value or crit_thresh
            unc_scale = ice_th.get("uncertainty_penalty_scaling", {}).value or unc_scale

    # Vessel operational limit (e.g. Sagar Kanya conservative 15% open-pack limit)
    vessel_sic_limit: Optional[float] = None
    if vessel:
        vessel_sic_limit = getattr(vessel, "max_navigable_sic", None)

    enforce_vessel_sic = True
    if policy and hasattr(policy, "hard_constraints"):
        sic_rule = policy.hard_constraints.get("enforce_vessel_sic_limit")
        if sic_rule and sic_rule.value is not None:
            enforce_vessel_sic = bool(sic_rule.value)

    # 1. Hard Block Evaluation against Vessel Limit
    if vessel_sic_limit is not None and sic_fraction > vessel_sic_limit and enforce_vessel_sic:
        reason = (
            f"Sea ice concentration ({sic_fraction*100:.1f}%) exceeds vessel maximum operational limit "
            f"({vessel_sic_limit*100:.1f}%)"
        )
        rule = "VESSEL_SEA_ICE_CAPABILITY_EXCEEDED"
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.CRITICAL_SEA_ICE,
                message=reason,
                severity="CRITICAL",
                variable="sea_ice_concentration",
                value=sic_fraction,
                threshold=vessel_sic_limit,
            )
        )
        return 1.0, True, reason, rule, "CRITICAL", max(0.2, 1.0 - unc_fraction), warnings

    # 2. Monotonic Risk Calculation
    # Piecewise linear and smooth quadratic growth
    if sic_fraction <= safe_thresh:
        base_risk = 0.0
        status = "SAFE"
    elif sic_fraction <= elevated_thresh:
        base_risk = 0.15 * ((sic_fraction - safe_thresh) / max(0.01, elevated_thresh - safe_thresh))
        status = "LOW"
    elif sic_fraction <= high_thresh:
        base_risk = 0.15 + 0.35 * ((sic_fraction - elevated_thresh) / max(0.01, high_thresh - elevated_thresh))
        status = "ELEVATED"
    elif sic_fraction <= crit_thresh:
        base_risk = 0.50 + 0.35 * ((sic_fraction - high_thresh) / max(0.01, crit_thresh - high_thresh))
        status = "HIGH"
    else:
        base_risk = 0.85 + 0.15 * min(1.0, (sic_fraction - crit_thresh) / 0.60)
        status = "CRITICAL"

    # Uncertainty modulation: High uncertainty increases risk margin slightly
    effective_risk = min(1.0, base_risk + (unc_fraction * unc_scale * 0.2))

    # Warnings based on status
    if status in {"HIGH", "CRITICAL"}:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.HIGH_SEA_ICE,
                message=f"Elevated sea ice concentration: {sic_fraction*100:.1f}% ({status})",
                severity="WARNING" if status == "HIGH" else "CRITICAL",
                variable="sea_ice_concentration",
                value=sic_fraction,
                threshold=high_thresh,
            )
        )

    if unc_fraction > 0.20:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.HIGH_SIC_UNCERTAINTY,
                message=f"High sea ice concentration uncertainty: ±{unc_fraction*100:.1f}%",
                severity="WARNING",
                variable="sea_ice_uncertainty",
                value=unc_fraction,
                threshold=0.20,
            )
        )

    confidence_factor = max(0.1, 1.0 - unc_fraction)
    return round(effective_risk, 4), False, None, None, status, round(confidence_factor, 3), warnings
