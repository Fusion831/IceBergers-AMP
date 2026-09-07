"""
Wave Risk Evaluator based on Significant Wave Height (Hs), Wave Period, and Encounter Angle.
Provides reduced-order operational severity without claiming naval architecture seakeeping simulation.
"""

import math
from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_wave_risk(
    wave_height_m: Optional[float],
    wave_direction_deg: Optional[float] = None,
    wave_period_s: Optional[float] = None,
    heading_deg: Optional[float] = None,
    policy: Optional[Any] = None,
    vessel: Optional[Any] = None,
) -> Tuple[float, str, List[RiskWarning]]:
    """
    Evaluates wave risk monotonically based on significant wave height and optional encounter angle.
    Returns:
        wave_risk: float in [0.0, 1.0]
        status: str (SAFE, LOW, ELEVATED, HIGH, CRITICAL, UNKNOWN)
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []

    if wave_height_m is None:
        return 0.0, "UNKNOWN", warnings

    hs = max(0.0, float(wave_height_m))

    # Thresholds from policy
    safe_hs = 2.5
    elev_hs = 4.0
    high_hs = 6.0
    crit_hs = 8.0

    if policy and hasattr(policy, "thresholds"):
        wave_th = policy.thresholds.get("waves", {})
        if wave_th:
            safe_hs = wave_th.get("safe_hs_m", {}).value or safe_hs
            elev_hs = wave_th.get("elevated_hs_m", {}).value or elev_hs
            high_hs = wave_th.get("high_hs_m", {}).value or high_hs
            crit_hs = wave_th.get("critical_hs_m", {}).value or crit_hs

    # Vessel operational limit
    vessel_max_wave: Optional[float] = None
    if vessel and hasattr(vessel, "max_wave_height_m"):
        vessel_max_wave = float(vessel.max_wave_height_m)

    # Base monotonic risk from significant wave height
    if hs <= safe_hs:
        base_risk = 0.10 * (hs / max(0.1, safe_hs))
        status = "SAFE"
    elif hs <= elev_hs:
        base_risk = 0.10 + 0.25 * ((hs - safe_hs) / max(0.1, elev_hs - safe_hs))
        status = "LOW"
    elif hs <= high_hs:
        base_risk = 0.35 + 0.35 * ((hs - elev_hs) / max(0.1, high_hs - elev_hs))
        status = "ELEVATED"
    elif hs <= crit_hs:
        base_risk = 0.70 + 0.20 * ((hs - high_hs) / max(0.1, crit_hs - high_hs))
        status = "HIGH"
    else:
        base_risk = 0.90 + 0.10 * min(1.0, (hs - crit_hs) / 4.0)
        status = "CRITICAL"

    # Directional modulation if heading is known
    encounter_factor = 1.0
    if heading_deg is not None and wave_direction_deg is not None:
        enc_angle = abs(heading_deg - wave_direction_deg) % 360.0
        if enc_angle > 180.0:
            enc_angle = 360.0 - enc_angle
        # Head seas (enc ~ 0 deg) and beam seas (~ 90 deg) carry higher operational discomfort/risk
        if enc_angle < 45.0:
            encounter_factor = 1.15  # Head seas
        elif 70.0 <= enc_angle <= 110.0:
            encounter_factor = 1.10  # Beam seas roll tendency
        elif enc_angle > 135.0:
            encounter_factor = 0.90  # Following seas

    effective_risk = min(1.0, base_risk * encounter_factor)

    # Warnings
    if vessel_max_wave is not None and hs > vessel_max_wave:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.CRITICAL_WAVE,
                message=f"Wave height ({hs:.1f}m) exceeds configured vessel operating limit ({vessel_max_wave:.1f}m)",
                severity="CRITICAL",
                variable="wave_height_m",
                value=hs,
                threshold=vessel_max_wave,
            )
        )
    elif status in {"HIGH", "CRITICAL"}:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.HIGH_WAVE,
                message=f"Severe wave conditions: Hs = {hs:.1f}m ({status})",
                severity="WARNING",
                variable="wave_height_m",
                value=hs,
                threshold=high_hs,
            )
        )

    return round(effective_risk, 4), status, warnings
