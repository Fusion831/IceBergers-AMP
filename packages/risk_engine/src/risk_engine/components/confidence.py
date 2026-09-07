"""
Data Quality and Confidence Evaluator for Multi-Hazard States.
Strictly distinguishes environmental risk severity from observation confidence.
"""

from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_data_quality(
    missing_variables: Optional[List[str]] = None,
    quality_status: str = "OBSERVED",
    sic_uncertainty: Optional[float] = None,
    sic_source: str = "OBSERVED",
    lead_time_days: int = 0,
    policy: Optional[Any] = None,
) -> Tuple[float, str, float, List[RiskWarning]]:
    """
    Evaluates data quality and epistemic confidence.
    Returns:
        confidence_score: float in [0.0, 1.0]
        confidence_class: str (HIGH, MEDIUM, LOW, UNKNOWN)
        data_quality_risk: float in [0.0, 1.0]
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []
    missing = missing_variables or []

    base_conf = 1.0

    # Policy rules
    missing_pen = 0.15
    mock_pen = 0.25
    ext_proj_pen = 0.20
    min_floor = 0.05

    if policy and hasattr(policy, "confidence_rules"):
        c_rules = policy.confidence_rules
        missing_pen = c_rules.get("missing_variable_penalty", {}).value or missing_pen
        mock_pen = c_rules.get("mock_data_penalty", {}).value or mock_pen
        ext_proj_pen = c_rules.get("extended_projection_penalty", {}).value or ext_proj_pen
        min_floor = c_rules.get("min_confidence_floor", {}).value or min_floor

    # 1. Missing Variables Penalty
    if missing:
        penalty = min(0.60, len(missing) * missing_pen)
        base_conf -= penalty
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.MISSING_VARIABLES,
                message=f"Missing environmental variables: {', '.join(missing)}",
                severity="WARNING" if len(missing) > 1 else "INFO",
            )
        )

    # 2. Mock Data Penalty
    q_status_upper = str(quality_status).upper()
    s_source_upper = str(sic_source).upper()

    if "MOCK" in q_status_upper or "MOCK" in s_source_upper or "SYNTHETIC" in q_status_upper:
        base_conf -= mock_pen

    # 3. Extended Projection / Climatology Penalty
    if q_status_upper in {"EXTENDED_PROJECTION", "CLIMATOLOGICAL"} or lead_time_days > 14:
        base_conf -= ext_proj_pen
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.EXTENDED_PROJECTION,
                message=f"Environmental state is based on extended projection ({lead_time_days} days lead time)",
                severity="INFO",
            )
        )

    # 4. SIC Uncertainty Penalty
    if sic_uncertainty is not None:
        unc_frac = sic_uncertainty / 100.0 if sic_uncertainty > 1.0 else sic_uncertainty
        if unc_frac > 0.15:
            base_conf -= min(0.25, unc_frac * 0.4)

    # Clamp confidence
    final_conf = max(min_floor, min(1.0, base_conf))

    # Classification
    if final_conf >= 0.80:
        conf_class = "HIGH"
    elif final_conf >= 0.50:
        conf_class = "MEDIUM"
    elif final_conf >= 0.20:
        conf_class = "LOW"
    else:
        conf_class = "UNKNOWN"

    if conf_class in {"LOW", "UNKNOWN"}:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.LOW_DATA_CONFIDENCE,
                message=f"Low data quality confidence score: {final_conf:.2f} ({conf_class})",
                severity="WARNING",
                variable="confidence_score",
                value=final_conf,
            )
        )

    # Data quality risk is the uncertainty penalty: 1.0 - confidence
    data_quality_risk = max(0.0, min(1.0, 1.0 - final_conf))

    return round(final_conf, 4), conf_class, round(data_quality_risk, 4), warnings
