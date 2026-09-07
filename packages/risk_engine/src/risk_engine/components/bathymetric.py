"""
Bathymetric Risk and Under-Keel Clearance (UKC) Evaluator using GEBCO depth.
Distinguishes shallow water warnings from hard grounding violations without inventing official safety standards.
"""

from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_bathymetric_risk(
    depth_m: Optional[float],
    draft_m: float = 5.6,
    policy: Optional[Any] = None,
    vessel: Optional[Any] = None,
) -> Tuple[float, bool, Optional[str], Optional[str], str, Optional[float], List[RiskWarning]]:
    """
    Evaluates bathymetric clearance and grounding constraints.
    Returns:
        bathymetric_risk: float in [0.0, 1.0]
        hard_blocked: bool
        block_reason: Optional[str]
        blocking_rule: Optional[str]
        status: str (SAFE, WARNING, CRITICAL, HARD_BLOCK, UNKNOWN)
        clearance_m: Optional[float]
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []

    if depth_m is None:
        return 0.0, False, None, None, "UNKNOWN", None, warnings

    effective_draft = draft_m
    if vessel:
        effective_draft = getattr(vessel, "draft_m", getattr(vessel, "draft_meters", draft_m))

    clearance_m = depth_m - effective_draft

    # Threshold configurations from policy
    warn_margin = 10.0
    crit_margin = 3.0
    ukc_rule = "HARD_BLOCK"

    if policy and hasattr(policy, "thresholds"):
        bathy_thresh = policy.thresholds.get("bathymetry", {})
        if bathy_thresh:
            warn_margin = bathy_thresh.get("warning_depth_margin_m", {}).value or warn_margin
            crit_margin = bathy_thresh.get("critical_depth_margin_m", {}).value or crit_margin
    if vessel and hasattr(vessel, "environmental_operational_limits"):
        limits = vessel.environmental_operational_limits
        if hasattr(limits, "safety_under_keel_clearance_m"):
            crit_margin = float(limits.safety_under_keel_clearance_m.value)
        if hasattr(limits, "under_keel_rule"):
            ukc_rule = str(limits.under_keel_rule.value).upper()

    # 1. Grounding Violation: Water depth <= draft
    if clearance_m <= 0.0:
        reason = f"Vessel bathymetric grounding: water depth ({depth_m:.1f}m) is less than operating draft ({effective_draft:.1f}m)"
        rule = "BATHYMETRIC_GROUNDING"
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.BATHYMETRIC_GROUNDING,
                message=reason,
                severity="CRITICAL",
                variable="bathymetry_depth_m",
                value=depth_m,
                threshold=effective_draft,
            )
        )
        return 1.0, True, reason, rule, "HARD_BLOCK", clearance_m, warnings

    # 2. Critical Clearance Violation (clearance < critical safety margin)
    if clearance_m < crit_margin:
        if ukc_rule == "HARD_BLOCK":
            reason = f"Inadequate under-keel clearance: clearance {clearance_m:.1f}m < safety margin {crit_margin:.1f}m"
            rule = "UNDER_KEEL_CLEARANCE_VIOLATION"
            warnings.append(
                RiskWarning(
                    code=RiskWarningCode.SHALLOW_WATER,
                    message=reason,
                    severity="CRITICAL",
                    variable="clearance_m",
                    value=clearance_m,
                    threshold=crit_margin,
                )
            )
            return 1.0, True, reason, rule, "HARD_BLOCK", clearance_m, warnings
        else:
            # Soft critical risk
            risk = 0.70 + 0.25 * ((crit_margin - clearance_m) / crit_margin)
            warnings.append(
                RiskWarning(
                    code=RiskWarningCode.SHALLOW_WATER,
                    message=f"Critical under-keel clearance: {clearance_m:.1f}m",
                    severity="WARNING",
                    variable="clearance_m",
                    value=clearance_m,
                    threshold=crit_margin,
                )
            )
            return min(0.95, risk), False, None, None, "CRITICAL", clearance_m, warnings

    # 3. Shallow Water Warning (critical margin <= clearance < warning margin)
    if clearance_m < warn_margin:
        ratio = (warn_margin - clearance_m) / max(0.1, warn_margin - crit_margin)
        risk = 0.20 + 0.45 * ratio
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.SHALLOW_WATER,
                message=f"Shallow water approach: under-keel clearance is {clearance_m:.1f}m",
                severity="INFO",
                variable="clearance_m",
                value=clearance_m,
                threshold=warn_margin,
            )
        )
        return min(0.65, risk), False, None, None, "WARNING", clearance_m, warnings

    # 4. Safe Deep Water
    return 0.0, False, None, None, "SAFE", clearance_m, warnings
