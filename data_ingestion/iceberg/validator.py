"""
Quality assurance and validation for Antarctic iceberg observations.
Flags spatial anomalies, impossible jumps, duplicate entries, and out-of-domain coordinates.
Generates comprehensive quality reports without silently deleting records.
"""

import json
from pathlib import Path
from typing import List, Tuple, Dict, Any
from datetime import timedelta
import numpy as np
from core.logging import get_logger
from data_access.spatial import haversine_distance_km
from data_ingestion.iceberg.metadata import IcebergObservationRecord

logger = get_logger("data_ingestion.iceberg.validator")


class IcebergValidator:
    """Validates iceberg observations and flags quality anomalies."""

    def __init__(
        self,
        max_speed_mps: float = 4.0,  # Max realistic sustained iceberg drift speed ~8 knots
        min_latitude: float = -90.0,
        max_latitude: float = -45.0,  # Antarctic / Southern Ocean domain
    ):
        self.max_speed_mps = max_speed_mps
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude

    def validate_observations(
        self,
        observations: List[IcebergObservationRecord],
    ) -> Tuple[List[IcebergObservationRecord], Dict[str, Any]]:
        """
        Validates observations and attaches flags to suspicious records.
        Returns (updated_observations, quality_summary).
        """
        total = len(observations)
        flagged_count = 0
        reasons_count: Dict[str, int] = {}

        # 1. Group by iceberg_id to check temporal ordering and speed jumps
        by_iceberg: Dict[str, List[IcebergObservationRecord]] = {}
        for obs in observations:
            by_iceberg.setdefault(obs.iceberg_id, []).append(obs)

        validated: List[IcebergObservationRecord] = []

        for iceberg_id, records in by_iceberg.items():
            # Sort by observation time
            records.sort(key=lambda r: (r.observation_time, r.is_interpolated))
            seen_times = set()

            prev_valid: Optional[IcebergObservationRecord] = None

            for r in records:
                flag: Optional[str] = None

                # Coordinate bounds check
                if not (self.min_latitude <= r.latitude <= self.max_latitude):
                    flag = f"latitude_out_of_bounds_{r.latitude}"
                elif not (-180.0 <= r.longitude <= 180.0):
                    flag = f"longitude_out_of_bounds_{r.longitude}"
                # Duplicate check
                elif r.observation_time in seen_times:
                    flag = "duplicate_timestamp"
                # Dimension sanity check
                elif r.length_km is not None and (r.length_km > 350.0 or r.length_km < 0.05):
                    flag = f"unrealistic_dimension_length_{r.length_km}"

                # Jump / speed check against previous valid observation
                if flag is None and prev_valid is not None:
                    dt_sec = (r.observation_time - prev_valid.observation_time).total_seconds()
                    if dt_sec > 0:
                        dist_km = haversine_distance_km(
                            prev_valid.latitude, prev_valid.longitude,
                            r.latitude, r.longitude,
                        )
                        speed_mps = (dist_km * 1000.0) / dt_sec
                        if speed_mps > self.max_speed_mps:
                            flag = f"suspicious_speed_jump_{speed_mps:.1f}_mps"

                if flag is not None:
                    r.is_valid = False
                    r.flag_reason = flag
                    flagged_count += 1
                    reasons_count[flag.split("_")[0]] = reasons_count.get(flag.split("_")[0], 0) + 1
                else:
                    r.is_valid = True
                    r.flag_reason = None
                    seen_times.add(r.observation_time)
                    prev_valid = r

                validated.append(r)

        summary = {
            "total_observations": total,
            "valid_observations": total - flagged_count,
            "flagged_observations": flagged_count,
            "flag_rate_pct": round((flagged_count / max(1, total)) * 100, 2),
            "flag_reasons": reasons_count,
            "distinct_icebergs": len(by_iceberg),
        }
        logger.info("Observation validation complete", **summary)
        return validated, summary

    def save_quality_report(
        self,
        summary: Dict[str, Any],
        output_path: Path,
    ) -> Path:
        """Saves structured quality report to JSON."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        logger.info("Saved quality report", path=str(output_path))
        return output_path
