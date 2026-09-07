"""
Constraint Evaluation Engine for AMIP Vessel Transitions.
Strictly separates HARD constraints (infeasible) from SOFT constraints (warnings / operational penalties).
"""

from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel, Field
from vessel.models import VesselProfile


class ConstraintResult(BaseModel):
    """Structured evaluation of physical and operational constraints on an edge transition."""
    is_feasible: bool = True
    hard_violations: List[str] = Field(default_factory=list)
    soft_warnings: List[str] = Field(default_factory=list)
    under_keel_clearance_m: Optional[float] = None
    clearance_status: str = Field(
        default="SAFE",
        description="Categorical under-keel status: SAFE, WARNING, CRITICAL, or HARD_BLOCK",
    )
    is_grounded: bool = False
    is_scar_blocked: bool = False
    is_ice_blocked: bool = False


class VesselConstraintChecker:
    """
    Evaluates regulatory, naval architectural, and environmental safety limits.
    """

    def __init__(self, vessel: Optional[VesselProfile] = None):
        self.vessel = vessel

    def evaluate(
        self,
        vessel: VesselProfile,
        geographic_status: str,
        is_blocked_scar: bool,
        water_depth_m: Optional[float],
        sea_ice_concentration: Optional[float],
        wave_height_m: Optional[float],
        wind_speed_ms: Optional[float],
        iceberg_hazard: Optional[float] = 0.0,
        ground_speed_knots: Optional[float] = None,
    ) -> ConstraintResult:
        """
        Executes strict constraint checks on a transition.
        """
        v = vessel or self.vessel
        hard_violations: List[str] = []
        soft_warnings: List[str] = []

        is_scar_blocked = False
        is_grounded = False
        is_ice_blocked = False
        clearance_status = "SAFE"

        # 1. Authoritative SCAR ADD Geographic Mask Check (HARD BLOCK)
        # SCAR ADD status must be respected. Never let routing trade land for fuel.
        blocked_statuses = v.geographic_constraints.blocked_statuses
        if is_blocked_scar or geographic_status.upper() in blocked_statuses:
            is_scar_blocked = True
            hard_violations.append(
                f"Traverses SCAR ADD blocked region ({geographic_status}); land or ice shelf"
            )

        # 2. Bathymetry / Draft / Under-Keel Clearance
        # Policy distinguishes: SAFE, WARNING, CRITICAL, HARD_BLOCK
        draft = v.draft_m  # 5.6m published for Sagar Kanya
        req_clearance = v.under_keel_margin_m  # 3.0m configured default
        clearance: Optional[float] = None

        if water_depth_m is not None:
            clearance = round(water_depth_m - draft, 2)
            if water_depth_m <= draft:
                is_grounded = True
                clearance_status = "CRITICAL"
                hard_violations.append(
                    f"Vessel grounding: water depth {water_depth_m:.1f}m <= draft {draft:.1f}m"
                )
            elif clearance < req_clearance:
                ukc_rule = str(v.environmental_operational_limits.under_keel_rule.value).upper()
                if ukc_rule == "HARD_BLOCK":
                    clearance_status = "HARD_BLOCK"
                    hard_violations.append(
                        f"Insufficient under-keel clearance: {clearance:.1f}m < required {req_clearance:.1f}m (rule=HARD_BLOCK)"
                    )
                elif clearance < (req_clearance * 0.5):
                    clearance_status = "CRITICAL"
                    soft_warnings.append(
                        f"Critical under-keel clearance: {clearance:.1f}m < 50% of required {req_clearance:.1f}m (rule={ukc_rule})"
                    )
                else:
                    clearance_status = "WARNING"
                    soft_warnings.append(
                        f"Low under-keel clearance: {clearance:.1f}m < required {req_clearance:.1f}m (rule={ukc_rule})"
                    )
            else:
                clearance_status = "SAFE"

        # 3. Sea Ice Concentration Limits (Conservative non-ice-class Sagar Kanya)
        max_sic = v.max_navigable_sic  # Default 0.15 (15%)
        pref_sic = float(v.ice_capability.preferred_max_sic.value)  # Default 0.05 (5%)

        if sea_ice_concentration is not None:
            sic_fraction = sea_ice_concentration / 100.0 if sea_ice_concentration > 1.0 else sea_ice_concentration
            if sic_fraction > max_sic:
                is_ice_blocked = True
                hard_violations.append(
                    f"Sea ice concentration {sic_fraction*100:.1f}% exceeds operational limit {max_sic*100:.1f}% (Ice Class: {v.ice_capability.status})"
                )
            elif sic_fraction > pref_sic:
                soft_warnings.append(
                    f"Navigating in ice pack: SIC {sic_fraction*100:.1f}% > preferred {pref_sic*100:.1f}%"
                )

        # 4. Wave Thresholds (Soft Warnings / Operational Speed Reduction)
        max_safe_hs = v.max_wave_height_m  # 6.0m
        pref_hs = float(v.environmental_operational_limits.preferred_max_wave_height_m.value)  # 4.0m

        if wave_height_m is not None:
            if wave_height_m >= max_safe_hs:
                soft_warnings.append(
                    f"Severe sea state: Hs {wave_height_m:.1f}m >= safe limit {max_safe_hs:.1f}m"
                )
            elif wave_height_m >= pref_hs:
                soft_warnings.append(
                    f"Rough seas: Hs {wave_height_m:.1f}m >= operational threshold {pref_hs:.1f}m"
                )

        # 5. Wind Limits
        max_wind = v.max_wind_speed_ms  # 20.0 m/s (~39 knots)
        if wind_speed_ms is not None and wind_speed_ms >= max_wind:
            soft_warnings.append(
                f"Gale force winds: {wind_speed_ms:.1f} m/s ({wind_speed_ms*1.94384:.1f} kn) >= threshold {max_wind:.1f} m/s"
            )

        # 6. Iceberg Hazard Exposure
        if iceberg_hazard is not None and iceberg_hazard > 0.005:
            soft_warnings.append(
                f"Elevated iceberg collision hazard: score={iceberg_hazard:.4f}"
            )

        # 7. Counter-Current Steerage / Headway Warning
        if ground_speed_knots is not None:
            if ground_speed_knots <= 0.0:
                soft_warnings.append(
                    f"Zero or negative progression: opposing current stalls vessel (along-track ground speed {ground_speed_knots:.1f} kn)"
                )
            elif ground_speed_knots < 1.5:
                soft_warnings.append(
                    f"Adverse current / slow ground speed: {ground_speed_knots:.1f} kn (minimum steerage control risk)"
                )

        is_feasible = len(hard_violations) == 0

        return ConstraintResult(
            is_feasible=is_feasible,
            hard_violations=hard_violations,
            soft_warnings=soft_warnings,
            under_keel_clearance_m=clearance,
            clearance_status=clearance_status,
            is_grounded=is_grounded,
            is_scar_blocked=is_scar_blocked,
            is_ice_blocked=is_ice_blocked,
        )

