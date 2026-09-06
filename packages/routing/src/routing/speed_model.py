"""Dynamic vessel speed determination engine based on vessel capabilities and local environment."""

import math
from dataclasses import dataclass
from typing import Optional
from domain.vessel import VesselProfile


@dataclass
class SegmentSpeedResult:
    """Speed evaluation along a navigational leg or segment."""
    effective_speed_knots: float
    base_speed_knots: float
    current_boost_knots: float
    wave_penalty_factor: float
    ice_penalty_factor: float
    is_passable: bool
    segment_duration_hours: float
    limiting_factor: str = "nominal"


class VesselSpeedModel:
    """
    Computes realistic effective vessel speed over ground:
    v_effective = f(VesselProfile, Environment(x, y, t), Heading)
    """

    def __init__(self, default_max_navigable_sic: float = 0.40):
        self.default_max_navigable_sic = default_max_navigable_sic

    def calculate_segment_speed(
        self,
        vessel: VesselProfile,
        distance_nm: float,
        heading_deg: float,
        sic: float = 0.0,
        wave_height_m: float = 1.5,
        wind_speed_ms: float = 5.0,
        current_u_ms: float = 0.0,
        current_v_ms: float = 0.0,
        max_navigable_sic: Optional[float] = None,
        desired_speed_knots: Optional[float] = None,
    ) -> SegmentSpeedResult:
        """
        Evaluate effective vessel transit speed along a segment.
        """
        if max_navigable_sic is not None:
            max_sic = max_navigable_sic
        elif hasattr(vessel, "max_navigable_sic") and vessel.max_navigable_sic is not None:
            max_sic = min(self.default_max_navigable_sic, vessel.max_navigable_sic)
        else:
            max_sic = self.default_max_navigable_sic

        cruise_speed = desired_speed_knots or vessel.service_speed_knots

        # 1. Hard ice constraint check
        if sic > max_sic:
            return SegmentSpeedResult(
                effective_speed_knots=0.0,
                base_speed_knots=cruise_speed,
                current_boost_knots=0.0,
                wave_penalty_factor=1.0,
                ice_penalty_factor=0.0,
                is_passable=False,
                segment_duration_hours=float("inf"),
                limiting_factor=f"Impassable: SIC {sic:.2f} exceeds vessel limit {max_sic:.2f}",
            )

        # 2. Ocean current projection along heading (0° = North, 90° = East)
        rad = math.radians(heading_deg)
        east_comp = math.sin(rad)
        north_comp = math.cos(rad)
        # Vector dot product with ocean current
        current_along_track_ms = (current_u_ms * east_comp) + (current_v_ms * north_comp)
        current_boost_knots = current_along_track_ms * 1.94384  # m/s to knots

        # 3. Wave penalty (slowdown in heavy swell)
        if wave_height_m > 2.5:
            # Drop speed up to 30% in extreme 6m+ seas
            wave_penalty = max(0.70, 1.0 - 0.06 * (wave_height_m - 2.5))
        else:
            wave_penalty = 1.0

        # 4. Non-linear sea ice slowdown curve
        if sic > 0.05:
            # Normalized ice resistance ratio
            ratio = min(1.0, sic / max_sic)
            ice_penalty = max(0.20, 1.0 - (ratio ** 1.6))
        else:
            ice_penalty = 1.0

        # 5. Effective speed calculation
        base_speed = cruise_speed * wave_penalty * ice_penalty
        effective_speed = base_speed + current_boost_knots

        # Vessel physical boundaries
        min_steerage_speed = 1.5
        max_vessel_speed = getattr(vessel, "max_speed_knots", cruise_speed * 1.25)

        effective_speed = max(min_steerage_speed, min(max_vessel_speed, effective_speed))

        # 6. Duration
        duration_hours = distance_nm / effective_speed if distance_nm > 0 else 0.0

        # Determine primary limiting factor
        limiting_factor = "nominal"
        if ice_penalty < 0.85:
            limiting_factor = f"sea_ice_resistance (SIC {sic:.2f})"
        elif wave_penalty < 0.90:
            limiting_factor = f"adverse_sea_state (H_s {wave_height_m:.1f}m)"
        elif current_boost_knots < -0.5:
            limiting_factor = f"opposing_current ({current_boost_knots:.1f} kn)"
        elif current_boost_knots > 0.5:
            limiting_factor = f"favorable_current (+{current_boost_knots:.1f} kn)"

        return SegmentSpeedResult(
            effective_speed_knots=round(effective_speed, 2),
            base_speed_knots=round(cruise_speed, 2),
            current_boost_knots=round(current_boost_knots, 2),
            wave_penalty_factor=round(wave_penalty, 3),
            ice_penalty_factor=round(ice_penalty, 3),
            is_passable=True,
            segment_duration_hours=round(duration_hours, 3),
            limiting_factor=limiting_factor,
        )
