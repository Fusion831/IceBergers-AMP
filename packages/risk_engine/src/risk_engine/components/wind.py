"""
Wind Risk Evaluator based on 10m Vector Winds and Operational Severity Thresholds.
Evaluates environmental severity at cell level and apparent wind at transition level.
"""

import math
from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_wind_risk(
    wind_u_ms: Optional[float] = None,
    wind_v_ms: Optional[float] = None,
    wind_speed_ms: Optional[float] = None,
    heading_deg: Optional[float] = None,
    policy: Optional[Any] = None,
    vessel: Optional[Any] = None,
) -> Tuple[float, Optional[float], Optional[float], str, List[RiskWarning]]:
    """
    Evaluates wind risk monotonically based on wind speed and optional vessel heading.
    Returns:
        wind_risk: float in [0.0, 1.0]
        speed_ms: Optional[float]
        direction_deg: Optional[float]
        status: str (SAFE, LOW, ELEVATED, HIGH, CRITICAL, UNKNOWN)
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []

    # Derive speed and direction from vector components
    speed = wind_speed_ms
    direction: Optional[float] = None

    if wind_u_ms is not None and wind_v_ms is not None:
        if speed is None:
            speed = math.hypot(wind_u_ms, wind_v_ms)
        direction = (math.degrees(math.atan2(wind_u_ms, wind_v_ms)) + 360.0) % 360.0

    if speed is None:
        return 0.0, None, None, "UNKNOWN", warnings

    speed = max(0.0, float(speed))

    # Thresholds from policy
    safe_w = 10.0
    elev_w = 15.0
    high_w = 20.0
    crit_w = 28.0

    if policy and hasattr(policy, "thresholds"):
        wind_th = policy.thresholds.get("wind", {})
        if wind_th:
            safe_w = wind_th.get("safe_speed_ms", {}).value or safe_w
            elev_w = wind_th.get("elevated_speed_ms", {}).value or elev_w
            high_w = wind_th.get("high_speed_ms", {}).value or high_w
            crit_w = wind_th.get("critical_speed_ms", {}).value or crit_w

    # Vessel limits if available
    vessel_max_wind: Optional[float] = None
    if vessel and hasattr(vessel, "max_wind_speed_ms"):
        vessel_max_wind = float(vessel.max_wind_speed_ms)

    # Base monotonic severity
    if speed <= safe_w:
        base_risk = 0.10 * (speed / max(0.1, safe_w))
        status = "SAFE"
    elif speed <= elev_w:
        base_risk = 0.10 + 0.25 * ((speed - safe_w) / max(0.1, elev_w - safe_w))
        status = "LOW"
    elif speed <= high_w:
        base_risk = 0.35 + 0.35 * ((speed - elev_w) / max(0.1, high_w - elev_w))
        status = "ELEVATED"
    elif speed <= crit_w:
        base_risk = 0.70 + 0.20 * ((speed - high_w) / max(0.1, crit_w - high_w))
        status = "HIGH"
    else:
        base_risk = 0.90 + 0.10 * min(1.0, (speed - crit_w) / 10.0)
        status = "CRITICAL"

    effective_risk = base_risk

    # Directional modulation if heading is known
    if heading_deg is not None and direction is not None:
        rel_angle = abs(heading_deg - direction) % 360.0
        if rel_angle > 180.0:
            rel_angle = 360.0 - rel_angle
        # Headwind (rel_angle < 45) slightly elevates power loss / risk
        if rel_angle < 45.0:
            effective_risk = min(1.0, base_risk * 1.10)

    # Warnings
    if vessel_max_wind is not None and speed > vessel_max_wind:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.CRITICAL_WIND,
                message=f"Wind speed ({speed:.1f} m/s) exceeds vessel operating limit ({vessel_max_wind:.1f} m/s)",
                severity="CRITICAL",
                variable="wind_speed_ms",
                value=speed,
                threshold=vessel_max_wind,
            )
        )
    elif status in {"HIGH", "CRITICAL"}:
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.HIGH_WIND,
                message=f"Severe wind conditions: speed = {speed:.1f} m/s (~{speed*1.94384:.0f} kn, {status})",
                severity="WARNING",
                variable="wind_speed_ms",
                value=speed,
                threshold=high_w,
            )
        )

    return round(effective_risk, 4), round(speed, 2), (round(direction, 1) if direction is not None else None), status, warnings
