"""
Ocean Current Risk Evaluator based on 2D Velocity Vectors and Vessel Heading.
Distinguishes favorable assistance from adverse opposing current penalty.
"""

import math
from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode

KNOTS_PER_MS = 1.9438444924406


def evaluate_current_risk(
    current_u_ms: Optional[float] = None,
    current_v_ms: Optional[float] = None,
    current_speed_ms: Optional[float] = None,
    current_direction_deg: Optional[float] = None,
    heading_deg: Optional[float] = None,
    policy: Optional[Any] = None,
) -> Tuple[float, Optional[float], Optional[float], Optional[float], str, List[RiskWarning]]:
    """
    Evaluates ocean current impact.
    Returns:
        current_risk: float in [0.0, 1.0]
        speed_ms: Optional[float]
        direction_deg: Optional[float]
        assistance_knots: Optional[float] (positive = favorable, negative = opposing)
        status: str (FAVORABLE, NEUTRAL, ADVERSE, UNKNOWN)
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []

    speed = current_speed_ms
    direction = current_direction_deg

    if current_u_ms is not None and current_v_ms is not None:
        if speed is None:
            speed = math.hypot(current_u_ms, current_v_ms)
        if direction is None:
            direction = (math.degrees(math.atan2(current_u_ms, current_v_ms)) + 360.0) % 360.0

    if speed is None:
        return 0.0, None, None, None, "UNKNOWN", warnings

    speed = max(0.0, float(speed))
    assistance_kn: Optional[float] = None

    # Case 1: Vessel Heading is Known (Transition or Route Context)
    if heading_deg is not None and current_u_ms is not None and current_v_ms is not None:
        hdg_rad = math.radians(heading_deg)
        u_hdg = math.sin(hdg_rad)
        v_hdg = math.cos(hdg_rad)

        # Along-track current component in m/s (+ forward, - opposing)
        along_track_ms = current_u_ms * u_hdg + current_v_ms * v_hdg
        assistance_kn = along_track_ms * KNOTS_PER_MS

        if assistance_kn >= 0.2:
            current_risk = 0.0
            status = "FAVORABLE"
        elif assistance_kn >= -0.3:
            current_risk = 0.05
            status = "NEUTRAL"
        else:
            # Adverse opposing current penalty
            opposing_ms = abs(along_track_ms)
            current_risk = min(1.0, 0.10 + 0.40 * (opposing_ms / 1.5))
            status = "ADVERSE"
            if opposing_ms > 1.0:
                warnings.append(
                    RiskWarning(
                        code=RiskWarningCode.ADVERSE_CURRENT,
                        message=f"Strong opposing ocean current: {assistance_kn:.1f} knots",
                        severity="WARNING",
                        variable="current_assistance_kn",
                        value=assistance_kn,
                    )
                )
    # Case 2: Vessel Heading is Unknown (Cell-Only Context)
    else:
        # Ambient environmental current characteristics
        # Current is not intrinsically a hazard without a known motion heading
        if speed < 0.3:
            current_risk = 0.0
            status = "NEUTRAL"
        elif speed < 0.8:
            current_risk = 0.10
            status = "NEUTRAL"
        else:
            current_risk = min(0.35, 0.15 + 0.20 * ((speed - 0.8) / 1.2))
            status = "ELEVATED_AMBIENT"

    return (
        round(current_risk, 4),
        round(speed, 2),
        (round(direction, 1) if direction is not None else None),
        (round(assistance_kn, 2) if assistance_kn is not None else None),
        status,
        warnings,
    )
