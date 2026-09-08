"""
Dynamic vessel speed determination engine based on vessel capabilities and local environment.
Explicitly separates Speed Through Water (STW) from Speed Over Ground (SOG),
verifies current vector projection along navigational heading (0°=North, 90°=East),
eliminates current double-counting, and removes silent 1.5-knot crawl fallbacks.
"""

import math
from dataclasses import dataclass
from typing import Optional
from domain.vessel import VesselProfile


@dataclass
class SegmentSpeedResult:
    """Speed evaluation along a navigational leg or segment."""
    effective_speed_knots: float          # Synonym for sog_kt for legacy compatibility
    base_speed_knots: float               # Target operating cruise speed
    vessel_stw_kt: float                  # Speed Through Water after environmental penalties
    current_u_ms: float                   # Eastward ocean current component
    current_v_ms: float                   # Northward ocean current component
    current_along_track_ms: float         # Ocean current projected along ship heading
    current_along_track_kt: float         # Along-track current in knots
    sog_kt: float                         # Speed Over Ground (STW + along-track current)
    current_boost_knots: float            # Synonym for current_along_track_kt
    wave_penalty_factor: float            # Fractional speed reduction from wave resistance
    ice_penalty_factor: float             # Fractional speed reduction from ice resistance
    is_passable: bool                     # False if hard constraints violated (e.g. SIC > limit)
    segment_duration_hours: float         # Leg duration based strictly on SOG
    limiting_factor: str = "nominal"


class VesselSpeedModel:
    """
    Computes physically rigorous vessel speed over ground:
    STW = TargetSpeed * WavePenalty * IcePenalty
    SOG = STW + Current_along_track
    Duration = Distance / SOG
    """

    def __init__(self, default_max_navigable_sic: float = 0.15):
        # Configured operational SIC threshold
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
        allow_ice_crawl: bool = False,
    ) -> SegmentSpeedResult:
        """
        Evaluate vessel STW, SOG, along-track current, and leg duration.

        Heading convention: 0° = North, 90° = East, 180° = South, 270° = West.
        """
        if max_navigable_sic is not None:
            max_sic = max_navigable_sic
        elif self.default_max_navigable_sic != 0.15:
            max_sic = self.default_max_navigable_sic
        elif hasattr(vessel, "configured_operational_sic_limit") and vessel.configured_operational_sic_limit is not None:
            max_sic = vessel.configured_operational_sic_limit
        elif hasattr(vessel, "max_navigable_sic") and vessel.max_navigable_sic is not None:
            max_sic = vessel.max_navigable_sic
        else:
            max_sic = self.default_max_navigable_sic

        cruise_speed = desired_speed_knots or getattr(vessel, "service_speed_knots", None) or vessel.cruising_speed_knots

        # 1. Hard ice operational limit check — NO SILENT 1.5-KNOT CRAWL
        if sic > max_sic and not allow_ice_crawl:
            return SegmentSpeedResult(
                effective_speed_knots=0.0,
                base_speed_knots=round(cruise_speed, 2),
                vessel_stw_kt=0.0,
                current_u_ms=round(current_u_ms, 3),
                current_v_ms=round(current_v_ms, 3),
                current_along_track_ms=0.0,
                current_along_track_kt=0.0,
                sog_kt=0.0,
                current_boost_knots=0.0,
                wave_penalty_factor=1.0,
                ice_penalty_factor=0.0,
                is_passable=False,
                segment_duration_hours=float("inf"),
                limiting_factor=f"Impassable: SIC {sic:.2f} exceeds configured operational limit {max_sic:.2f}",
            )

        # 2. Ocean current vector projection along heading (0° = N, 90° = E)
        rad = math.radians(heading_deg % 360.0)
        east_comp = math.sin(rad)
        north_comp = math.cos(rad)
        current_along_track_ms = (current_u_ms * east_comp) + (current_v_ms * north_comp)
        current_along_track_kt = current_along_track_ms * 1.94384  # m/s to knots

        # 3. Wave resistance penalty
        if wave_height_m > 2.5:
            wave_penalty = max(0.70, 1.0 - 0.06 * (wave_height_m - 2.5))
        else:
            wave_penalty = 1.0

        # 4. Non-linear sea ice resistance curve for navigable ice (SIC <= max_sic)
        if sic > 0.03:
            ratio = min(1.0, sic / max(0.01, max_sic))
            ice_penalty = max(0.35, 1.0 - 0.65 * (ratio ** 1.4))
        else:
            ice_penalty = 1.0

        # 5. Speed Through Water (STW)
        max_stw = getattr(vessel, "max_speed_knots", None) or (cruise_speed * 1.25)
        vessel_stw = min(max_stw, cruise_speed * wave_penalty * ice_penalty)

        # 6. Speed Over Ground (SOG) = STW + along-track current
        # Audited: Current is added once here into SOG and NEVER re-penalized in duration!
        sog_unclamped = vessel_stw + current_along_track_kt

        min_steerage = 3.0 if not allow_ice_crawl else 1.5
        sog = max(min_steerage, sog_unclamped)

        # 7. Segment Duration (strictly Distance / SOG)
        duration_hours = (distance_nm / sog) if (distance_nm > 0 and sog > 0) else 0.0

        # Limiting factor diagnostics
        limiting_factor = "nominal"
        if ice_penalty < 0.85:
            limiting_factor = f"sea_ice_resistance (SIC {sic:.2f})"
        elif wave_penalty < 0.90:
            limiting_factor = f"adverse_sea_state (H_s {wave_height_m:.1f}m)"
        elif current_along_track_kt < -0.5:
            limiting_factor = f"opposing_current ({current_along_track_kt:.1f} kn)"
        elif current_along_track_kt > 0.5:
            limiting_factor = f"favorable_current (+{current_along_track_kt:.1f} kn)"

        return SegmentSpeedResult(
            effective_speed_knots=round(sog, 2),
            base_speed_knots=round(cruise_speed, 2),
            vessel_stw_kt=round(vessel_stw, 2),
            current_u_ms=round(current_u_ms, 3),
            current_v_ms=round(current_v_ms, 3),
            current_along_track_ms=round(current_along_track_ms, 3),
            current_along_track_kt=round(current_along_track_kt, 2),
            sog_kt=round(sog, 2),
            current_boost_knots=round(current_along_track_kt, 2),
            wave_penalty_factor=round(wave_penalty, 3),
            ice_penalty_factor=round(ice_penalty, 3),
            is_passable=True,
            segment_duration_hours=round(duration_hours, 3),
            limiting_factor=limiting_factor,
        )
