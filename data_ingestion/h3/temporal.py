"""
Temporal Alignment and Quality Tracking for H3 x Time Environmental Grid.
Aligns multi-source environmental datasets (3h waves, 6h currents, forecast steps, daily SIC)
into the canonical 6-hour discrete time index with explicit quality provenance.
"""

from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from core.logging import get_logger
from data_ingestion.h3.schema import TemporalQualityStatus

logger = get_logger("data_ingestion.h3.temporal")


class H3TemporalAligner:
    """
    Coordinates temporal transformation and discrete time alignment across environmental layers:
    - CMEMS Currents: native 6-hourly (direct alignment)
    - CMEMS Waves: native 3-hourly (configurable 6-hourly temporal stride/interpolation)
    - ECMWF Wind: native forecast steps (direct mapping to valid timestamp)
    - NSIDC SIC: daily (daily observation carried forward with PERSISTED flag)
    - GEBCO / SCAR ADD: static (time-invariant)
    - Iceberg Trajectories: hourly model integration (sampled at canonical 6h intervals)
    """

    def __init__(self, step_hours: int = 6):
        self.step_hours = step_hours

    def generate_canonical_time_index(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> List[datetime]:
        """
        Generates monotonic list of canonical timestamps spaced at step_hours.
        """
        # Ensure UTC timezone
        if start_time.tzinfo is None:
            start_time = start_time.replace(tzinfo=timezone.utc)
        if end_time.tzinfo is None:
            end_time = end_time.replace(tzinfo=timezone.utc)

        # Snap start_time to nearest preceding canonical step
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        start_sec = int((start_time - epoch).total_seconds())
        step_sec = self.step_hours * 3600
        snapped_start = epoch + timedelta(seconds=(start_sec // step_sec) * step_sec)

        timestamps = []
        cur = snapped_start
        while cur <= end_time:
            timestamps.append(cur)
            cur += timedelta(seconds=step_sec)

        return timestamps

    def classify_temporal_quality(
        self,
        valid_time: datetime,
        observation_or_ref_time: datetime,
        source_is_forecast: bool = False,
    ) -> TemporalQualityStatus:
        """
        Evaluates temporal provenance and assigns explicit quality flags.
        Never silently replaces missing values with zero or marks forecast as observed.
        """
        diff_hours = (valid_time - observation_or_ref_time).total_seconds() / 3600.0

        if source_is_forecast:
            if diff_hours <= 240.0:  # Within 10-day NWP horizon
                return TemporalQualityStatus.FORECAST
            else:
                return TemporalQualityStatus.EXTENDED_PROJECTION

        if abs(diff_hours) <= float(self.step_hours):
            return TemporalQualityStatus.OBSERVED
        elif 0.0 < diff_hours <= 72.0:
            return TemporalQualityStatus.PERSISTED
        elif diff_hours > 72.0:
            return TemporalQualityStatus.CLIMATOLOGICAL
        else:
            return TemporalQualityStatus.INTERPOLATED

    def build_time_index_manifest(
        self,
        timestamps: List[datetime],
        base_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Generates time index metadata mapping T+0, T+6h, T+1d, T+3d, etc. for frontend time-slider.
        """
        ref_time = base_time or (timestamps[0] if timestamps else datetime.now(timezone.utc))
        time_entries = []

        for idx, t in enumerate(timestamps):
            lead_h = (t - ref_time).total_seconds() / 3600.0
            time_entries.append({
                "step_index": idx,
                "timestamp": t.isoformat(),
                "lead_hours": round(lead_h, 1),
                "lead_days": round(lead_h / 24.0, 2),
                "label": f"T+{int(lead_h)}h" if lead_h >= 0 else f"T{int(lead_h)}h",
            })

        return {
            "canonical_step_hours": self.step_hours,
            "reference_time": ref_time.isoformat(),
            "total_timesteps": len(timestamps),
            "time_steps": time_entries,
            "temporal_quality_rules": {
                "cmems_currents": "Native 6-hourly direct alignment",
                "cmems_waves": "Native 3-hourly sampled at 6h stride",
                "ecmwf_wind": "0-48h NWP forecast aligned to valid timestamps",
                "nsidc_sic": "Daily polar stereographic observation persisted over 24h cycle",
                "gebco_bathymetry": "Static (time-invariant)",
                "scar_add_mask": "Static (time-invariant)",
                "iceberg_hazard": "Hourly ensemble occupancy evaluated at canonical timestamps",
            }
        }
