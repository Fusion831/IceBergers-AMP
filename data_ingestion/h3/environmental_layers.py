"""
Dynamic Environmental Layers Mapping to H3:
- NSIDC Sea Ice Concentration (Scientific valid pixels only, QA respect)
- CMEMS Surface Ocean Currents (Direct vector component aggregation: mean(u), mean(v))
- CMEMS Waves (Scalar height/period, Circular vector-aware wave direction)
- ECMWF 10m Wind (Direct vector component aggregation: mean(10u), mean(10v))
"""

import math
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from core.logging import get_logger
from data_ingestion.h3.schema import DynamicH3State, TemporalQualityStatus

logger = get_logger("data_ingestion.h3.environmental_layers")


def circular_mean_degrees(angles_deg: List[float]) -> Optional[float]:
    """
    Computes vector-aware circular mean for compass directions in degrees [0, 360).
    Correctly aggregates angles without wrap-around artifacts (e.g., 359° and 1° average to 0°/360°, not 180°).
    """
    if not angles_deg:
        return None
    valid_angles = [a for a in angles_deg if a is not None and not np.isnan(a)]
    if not valid_angles:
        return None

    rads = np.radians(valid_angles)
    sin_sum = float(np.sum(np.sin(rads)))
    cos_sum = float(np.sum(np.cos(rads)))

    if sin_sum == 0.0 and cos_sum == 0.0:
        return None

    mean_rad = math.atan2(sin_sum, cos_sum)
    mean_deg = math.degrees(mean_rad) % 360.0
    return round(mean_deg, 2)


def vector_mean_components(u_list: List[float], v_list: List[float]) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
    """
    Aggregates vector velocity components directly:
    Returns (mean_u, mean_v, derived_speed, derived_direction_deg).
    """
    valid_u = [u for u in u_list if u is not None and not np.isnan(u)]
    valid_v = [v for v in v_list if v is not None and not np.isnan(v)]

    if not valid_u or not valid_v:
        return None, None, None, None

    mean_u = float(np.mean(valid_u))
    mean_v = float(np.mean(valid_v))
    speed = float(math.hypot(mean_u, mean_v))
    # Compass direction (degrees clockwise from North toward which vector points)
    direction = float(math.degrees(math.atan2(mean_u, mean_v)) % 360.0)

    return round(mean_u, 4), round(mean_v, 4), round(speed, 3), round(direction, 2)


class H3EnvironmentalAggregator:
    """
    Aggregates native scientific datasets (NSIDC, CMEMS, ECMWF) into canonical H3 cells.
    Preserves exact vector aggregation rules and circular directional integrity.
    """

    @staticmethod
    def aggregate_nsidc_sic(
        raw_sic_values: List[float],
        valid_pixel_mask: List[bool],
    ) -> Dict[str, Any]:
        """
        Aggregates valid scientific NSIDC sea-ice pixels within an H3 cell.
        Excludes land, coast, and lake flags from ocean SIC averages.
        """
        if not raw_sic_values:
            return {
                "sic_mean": None,
                "sic_min": None,
                "sic_max": None,
                "sic_uncertainty": None,
                "sic_valid_fraction": 0.0,
            }

        valid_vals = [
            v for v, is_v in zip(raw_sic_values, valid_pixel_mask)
            if is_v and v is not None and not np.isnan(v) and 0.0 <= v <= 100.0
        ]

        valid_f = len(valid_vals) / float(len(raw_sic_values))
        if not valid_vals:
            return {
                "sic_mean": None,
                "sic_min": None,
                "sic_max": None,
                "sic_uncertainty": None,
                "sic_valid_fraction": round(valid_f, 3),
            }

        arr = np.array(valid_vals, dtype=float)
        return {
            "sic_mean": round(float(np.mean(arr)), 2),
            "sic_min": round(float(np.min(arr)), 2),
            "sic_max": round(float(np.max(arr)), 2),
            "sic_uncertainty": round(float(np.std(arr)), 2) if len(arr) > 1 else 0.0,
            "sic_valid_fraction": round(valid_f, 3),
        }

    @staticmethod
    def aggregate_cmems_currents(
        u_samples: List[float],
        v_samples: List[float],
    ) -> Dict[str, Any]:
        """
        Direct vector component aggregation for ocean currents (mean(u), mean(v)).
        """
        total = max(len(u_samples), len(v_samples))
        if total == 0:
            return {
                "current_u_ms": None,
                "current_v_ms": None,
                "current_speed_ms": None,
                "current_direction_deg": None,
                "current_valid_fraction": 0.0,
            }

        u_mean, v_mean, spd, dir_deg = vector_mean_components(u_samples, v_samples)
        valid_count = len([u for u in u_samples if u is not None and not np.isnan(u)])
        valid_f = valid_count / float(total)

        return {
            "current_u_ms": u_mean,
            "current_v_ms": v_mean,
            "current_speed_ms": spd,
            "current_direction_deg": dir_deg,
            "current_valid_fraction": round(valid_f, 3),
        }

    @staticmethod
    def aggregate_cmems_waves(
        hs_samples: List[float],
        tp_samples: List[float],
        dir_samples_deg: List[float],
    ) -> Dict[str, Any]:
        """
        Aggregates waves: scalar height/period and circular vector-aware wave direction.
        """
        total = max(len(hs_samples), len(tp_samples), len(dir_samples_deg))
        if total == 0:
            return {
                "wave_height_m": None,
                "wave_direction_deg": None,
                "wave_period_s": None,
                "wave_valid_fraction": 0.0,
            }

        valid_hs = [h for h in hs_samples if h is not None and not np.isnan(h) and h >= 0.0]
        valid_tp = [t for t in tp_samples if t is not None and not np.isnan(t) and t >= 0.0]
        circ_dir = circular_mean_degrees(dir_samples_deg)

        valid_f = len(valid_hs) / float(total) if total > 0 else 0.0
        return {
            "wave_height_m": round(float(np.mean(valid_hs)), 2) if valid_hs else None,
            "wave_direction_deg": circ_dir,
            "wave_period_s": round(float(np.mean(valid_tp)), 2) if valid_tp else None,
            "wave_valid_fraction": round(valid_f, 3),
        }

    @staticmethod
    def aggregate_ecmwf_wind(
        u10_samples: List[float],
        v10_samples: List[float],
    ) -> Dict[str, Any]:
        """
        Direct vector component aggregation for 10m wind (mean(u10), mean(v10)).
        """
        total = max(len(u10_samples), len(v10_samples))
        if total == 0:
            return {
                "wind_u_ms": None,
                "wind_v_ms": None,
                "wind_speed_ms": None,
                "wind_direction_deg": None,
                "wind_valid_fraction": 0.0,
            }

        u_mean, v_mean, spd, dir_deg = vector_mean_components(u10_samples, v10_samples)
        valid_count = len([u for u in u10_samples if u is not None and not np.isnan(u)])
        valid_f = valid_count / float(total)

        return {
            "wind_u_ms": u_mean,
            "wind_v_ms": v_mean,
            "wind_speed_ms": spd,
            "wind_direction_deg": dir_deg,
            "wind_valid_fraction": round(valid_f, 3),
        }
