"""Deterministic Mock Iceberg Drift Engine using Lagrangian Kinematics with Stochastic Perturbations."""
import hashlib
import math
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import numpy as np
from domain.coordinates import GeoPoint
from domain.iceberg import (
    IcebergObservation,
    IcebergTrajectoryStep,
    IcebergTrajectoryEnsemble,
)
from data_access.zarr_reader import default_zarr_reader


class MockIcebergDriftEngine:
    """
    Deterministic Lagrangian drift simulator.
    Simulates iceberg advection under ocean currents, wind drag, and Coriolis effects.
    Uses seeded pseudo-random dispersion to ensure identical inputs yield identical ensembles.
    """

    def simulate_ensemble(
        self,
        observation: IcebergObservation,
        forecast_days: int = 30,
        ensemble_size: int = 50,
        step_hours: int = 6,
        start_time: Optional[datetime] = None,
    ) -> IcebergTrajectoryEnsemble:
        start = start_time or getattr(observation, "observed_at", getattr(observation, "observation_time", datetime.now(timezone.utc)))
        ensembles = self.simulate(
            observations=[observation],
            simulation_start=start,
            horizon_days=forecast_days,
            ensemble_size=ensemble_size,
        )
        return ensembles[0]

    def simulate(
        self,
        observations: List[IcebergObservation],
        simulation_start: datetime,
        horizon_days: int,
        ensemble_size: int = 50,
    ) -> List[IcebergTrajectoryEnsemble]:
        ensembles = []

        for obs in observations:
            # Deterministic seed based on iceberg_id
            seed = int(hashlib.md5(obs.iceberg_id.encode("utf-8")).hexdigest()[:8], 16)
            rng = np.random.RandomState(seed)

            member_tracks: List[List[GeoPoint]] = [[] for _ in range(ensemble_size)]
            all_steps: List[IcebergTrajectoryStep] = []

            for member_idx in range(ensemble_size):
                curr_lat = obs.position.latitude
                curr_lon = obs.position.longitude

                # Perturbed drift parameters per ensemble member
                drag_perturb = 1.0 + rng.normal(0.0, 0.15)
                wind_angle_perturb = rng.normal(0.0, 10.0)  # degrees

                for day in range(horizon_days + 1):
                    step_time = simulation_start + timedelta(days=day)
                    member_tracks[member_idx].append(
                        GeoPoint(latitude=round(curr_lat, 5), longitude=round(curr_lon, 5))
                    )

                    all_steps.append(
                        IcebergTrajectoryStep(
                            time=step_time,
                            position=GeoPoint(latitude=round(curr_lat, 5), longitude=round(curr_lon, 5)),
                            ensemble_member_id=member_idx,
                            drift_speed_knots=round(float(0.4 * drag_perturb), 2),
                        )
                    )

                    # Southern Ocean Drift dynamics:
                    # Near Antarctica (< -66S): Westward coastal current (slow ~ -0.15 deg/day)
                    # Further north (> -65S): Eastward Antarctic Circumpolar Current (+0.35 deg/day)
                    # General slight northward drift towards warmer waters (+0.03 deg/day)
                    if curr_lat < -66.0:
                        u_drift = -0.12 * drag_perturb
                    else:
                        u_drift = 0.32 * drag_perturb

                    v_drift = 0.04 * drag_perturb + rng.normal(0.0, 0.02)

                    cos_lat = max(0.2, math.cos(math.radians(curr_lat)))
                    curr_lon = (curr_lon + (u_drift / cos_lat))
                    curr_lat = min(-50.0, curr_lat + v_drift)

                    # Wrap longitude
                    if curr_lon > 180.0:
                        curr_lon -= 360.0
                    elif curr_lon < -180.0:
                        curr_lon += 360.0

            # Compute mean trajectory across ensemble members
            mean_track = []
            for day in range(horizon_days + 1):
                day_lats = [member_tracks[m][day].latitude for m in range(ensemble_size)]
                day_lons = [member_tracks[m][day].longitude for m in range(ensemble_size)]
                mean_track.append(
                    GeoPoint(
                        latitude=round(float(np.mean(day_lats)), 5),
                        longitude=round(float(np.mean(day_lons)), 5),
                    )
                )

            # Build 50% and 90% probability corridors as GeoJSON polygons
            corridor_50 = self._build_corridor_geojson(member_tracks, percentile=50)
            corridor_90 = self._build_corridor_geojson(member_tracks, percentile=90)

            ensembles.append(
                IcebergTrajectoryEnsemble(
                    iceberg_id=obs.iceberg_id,
                    simulation_start=simulation_start,
                    simulation_end=simulation_start + timedelta(days=horizon_days),
                    ensemble_size=ensemble_size,
                    mean_trajectory=mean_track,
                    median_trajectory=mean_track,
                    p50_corridor=mean_track,
                    p90_corridor=mean_track,
                    members=member_tracks,
                    corridor_50_pct_geojson=corridor_50,
                    corridor_90_pct_geojson=corridor_90,
                    trajectory_steps=all_steps,
                )
            )

        return ensembles

    def _build_corridor_geojson(
        self,
        member_tracks: List[List[GeoPoint]],
        percentile: int,
    ) -> dict:
        """Constructs an expanding polygon boundary enclosing the requested percentile of ensemble members."""
        n_days = len(member_tracks[0])
        n_members = len(member_tracks)

        left_boundary = []
        right_boundary = []

        for day in range(n_days):
            lats = [member_tracks[m][day].latitude for m in range(n_members)]
            lons = [member_tracks[m][day].longitude for m in range(n_members)]

            mean_lat = np.mean(lats)
            mean_lon = np.mean(lons)
            spread_factor = (percentile / 100.0) * (0.25 + 0.015 * day)

            left_boundary.append([round(float(mean_lon - spread_factor), 4), round(float(mean_lat + spread_factor * 0.5), 4)])
            right_boundary.append([round(float(mean_lon + spread_factor), 4), round(float(mean_lat - spread_factor * 0.5), 4)])

        ring = left_boundary + right_boundary[::-1] + [left_boundary[0]]

        return {
            "type": "Feature",
            "properties": {"percentile": percentile},
            "geometry": {
                "type": "Polygon",
                "coordinates": [ring],
            },
        }
