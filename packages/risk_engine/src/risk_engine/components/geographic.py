"""
Authoritative Geographic Risk Evaluator based on SCAR ADD v7.12.
Preserves land, ice shelf, ice tongue, and rumple fractions while enforcing hard barriers.
"""

from typing import Dict, Any, Tuple, List, Optional
from risk_engine.warnings import RiskWarning, RiskWarningCode


def evaluate_geographic_risk(
    geographic_status: str = "OPEN_OCEAN",
    ocean_fraction: float = 1.0,
    land_fraction: float = 0.0,
    ice_shelf_fraction: float = 0.0,
    ice_tongue_fraction: float = 0.0,
    rumple_fraction: float = 0.0,
    is_blocked: bool = False,
    policy: Optional[Any] = None,
) -> Tuple[float, bool, Optional[str], Optional[str], List[RiskWarning]]:
    """
    Evaluates geographic risk and authoritative hard constraints.
    Returns:
        geographic_risk: float in [0.0, 1.0]
        hard_blocked: bool
        block_reason: Optional[str]
        blocking_rule: Optional[str]
        warnings: List[RiskWarning]
    """
    warnings: List[RiskWarning] = []
    status_upper = str(geographic_status).upper()

    # Authoritative hard blocking statuses from SCAR ADD
    blocked_statuses = {"LAND", "ICE_SHELF", "ICE_TONGUE", "RUMPLE"}
    if policy and hasattr(policy, "hard_constraints"):
        scar_spec = policy.hard_constraints.get("respect_scar_add_mask")
        if scar_spec and scar_spec.blocked_statuses:
            blocked_statuses = set(s.upper() for s in scar_spec.blocked_statuses)

    # 1. Hard Block Evaluation
    is_hard_blocked = is_blocked or (status_upper in blocked_statuses)
    if is_hard_blocked:
        reason = f"Prohibited SCAR ADD geographic feature: {status_upper}"
        rule = "SCAR_ADD_GEOGRAPHIC_MASK"
        warnings.append(
            RiskWarning(
                code=RiskWarningCode.GEOGRAPHIC_BLOCK,
                message=reason,
                severity="CRITICAL",
                variable="geographic_status",
            )
        )
        return 1.0, True, reason, rule, warnings

    # 2. Mixed / Coastal Cell Evaluation
    non_ocean_fraction = max(0.0, 1.0 - ocean_fraction)
    if non_ocean_fraction > 0.0 or status_upper == "MIXED":
        # Continuous monotonic risk proportional to non-ocean fraction
        geo_risk = min(0.95, non_ocean_fraction)
        if geo_risk > 0.30:
            warnings.append(
                RiskWarning(
                    code=RiskWarningCode.GEOGRAPHIC_BLOCK,
                    message=f"Mixed coastal cell with {non_ocean_fraction*100:.1f}% land/ice shelf fraction",
                    severity="WARNING",
                    variable="ocean_fraction",
                    value=ocean_fraction,
                )
            )
        return geo_risk, False, None, None, warnings

    # 3. Open Ocean
    return 0.0, False, None, None, warnings
