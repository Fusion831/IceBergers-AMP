"""
Historical track reconstruction and trajectory diagnostics.
Calculates derived velocities, observation intervals, total displacement,
and associates observations with configurable H3 spatial cells.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import math
import numpy as np
import h3
from core.logging import get_logger
from data_access.spatial import haversine_distance_km
from data_ingestion.iceberg.metadata import (
    IcebergObservationRecord,
    IcebergTrackDiagnostic,
)

logger = get_logger("data_ingestion.iceberg.tracks")


class TrackSegmentPoint:
    """Enhanced track point with derived velocity and H3 cell."""
    def __init__(
        self,
        observation: IcebergObservationRecord,
        velocity_u_mps: float = 0.0,
        velocity_v_mps: float = 0.0,
        speed_mps: float = 0.0,
        bearing_deg: float = 0.0,
        h3_cell: Optional[str] = None,
    ):
        self.observation = observation
        self.velocity_u_mps = velocity_u_mps
        self.velocity_v_mps = velocity_v_mps
        self.speed_mps = speed_mps
        self.bearing_deg = bearing_deg
        self.h3_cell = h3_cell


def calculate_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates initial compass bearing (azimuth) from point 1 to point 2 in degrees [0, 360)."""
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)
    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


class IcebergTrackReconstructor:
    """Reconstructs continuous tracks from discrete observations."""

    def __init__(self, h3_resolution: int = 5):
        self.h3_resolution = h3_resolution

    def reconstruct_track(
        self,
        observations: List[IcebergObservationRecord],
    ) -> Tuple[List[TrackSegmentPoint], IcebergTrackDiagnostic]:
        """
        Reconstructs an ordered track from a list of observations for a single iceberg.
        """
        if not observations:
            raise ValueError("No observations provided for track reconstruction.")

        # Sort chronologically, preferring raw observations over interpolated ones
        sorted_obs = sorted(observations, key=lambda r: (r.observation_time, r.is_interpolated))
        iceberg_id = sorted_obs[0].iceberg_id
        source = sorted_obs[0].source

        points: List[TrackSegmentPoint] = []
        intervals_hours: List[float] = []
        speeds_mps: List[float] = []
        total_displacement_km = 0.0

        for i, obs in enumerate(sorted_obs):
            # Compute H3 cell
            cell = h3.latlng_to_cell(obs.latitude, obs.longitude, self.h3_resolution)

            if i == 0:
                points.append(TrackSegmentPoint(obs, 0.0, 0.0, 0.0, 0.0, cell))
                continue

            prev = sorted_obs[i - 1]
            dt_sec = (obs.observation_time - prev.observation_time).total_seconds()
            dist_km = haversine_distance_km(prev.latitude, prev.longitude, obs.latitude, obs.longitude)
            total_displacement_km += dist_km

            if dt_sec > 0:
                intervals_hours.append(dt_sec / 3600.0)
                speed = (dist_km * 1000.0) / dt_sec
                speeds_mps.append(speed)
                bearing = calculate_bearing_deg(prev.latitude, prev.longitude, obs.latitude, obs.longitude)

                # Decompose into East (u) and North (v) velocities
                rad = math.radians(bearing)
                u = speed * math.sin(rad)
                v = speed * math.cos(rad)
                points.append(TrackSegmentPoint(obs, round(u, 3), round(v, 3), round(speed, 3), round(bearing, 1), cell))
            else:
                points.append(TrackSegmentPoint(obs, 0.0, 0.0, 0.0, 0.0, cell))

        start_time = sorted_obs[0].observation_time
        end_time = sorted_obs[-1].observation_time
        duration_days = max(0.0, (end_time - start_time).total_seconds() / 86400.0)

        median_interval = float(np.median(intervals_hours)) if intervals_hours else 0.0
        max_gap_days = (float(np.max(intervals_hours)) / 24.0) if intervals_hours else 0.0
        mean_speed = float(np.mean(speeds_mps)) if speeds_mps else 0.0
        median_speed = float(np.median(speeds_mps)) if speeds_mps else 0.0
        max_speed = float(np.max(speeds_mps)) if speeds_mps else 0.0
        flagged_count = sum(1 for o in sorted_obs if not o.is_valid)

        diag = IcebergTrackDiagnostic(
            iceberg_id=iceberg_id,
            source=source,
            observation_count=len(sorted_obs),
            track_start=start_time,
            track_end=end_time,
            duration_days=round(duration_days, 1),
            median_observation_interval_hours=round(median_interval, 1),
            max_observation_gap_days=round(max_gap_days, 1),
            total_displacement_km=round(total_displacement_km, 1),
            mean_speed_mps=round(mean_speed, 3),
            median_speed_mps=round(median_speed, 3),
            max_speed_mps=round(max_speed, 3),
            flagged_jump_count=flagged_count,
        )

        return points, diag

    def reconstruct_all_tracks(
        self,
        observations: List[IcebergObservationRecord],
    ) -> Dict[str, Tuple[List[TrackSegmentPoint], IcebergTrackDiagnostic]]:
        """
        Reconstructs tracks for all distinct icebergs in the observation set.
        """
        by_iceberg: Dict[str, List[IcebergObservationRecord]] = {}
        for obs in observations:
            by_iceberg.setdefault(obs.iceberg_id, []).append(obs)

        results = {}
        for iceberg_id, obs_list in by_iceberg.items():
            if len(obs_list) >= 2:
                points, diag = self.reconstruct_track(obs_list)
                results[iceberg_id] = (points, diag)

        logger.info("Reconstructed tracks", count=len(results))
        return results
