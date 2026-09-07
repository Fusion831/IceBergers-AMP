"""
Stochastic ensemble trajectory generation and spread metrics for Antarctic icebergs.
Applies physical perturbations to initial states, dimensions, drag coefficients,
and environmental forcing using reproducible deterministic seeds.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import numpy as np
from core.logging import get_logger
from data_access.spatial import haversine_distance_km
from data_ingestion.iceberg.metadata import (
    TrajectoryPoint,
    EnsembleSpreadPoint,
    TrajectoryStatus,
)
from data_ingestion.iceberg.physics import IcebergPhysicalProfile
from data_ingestion.iceberg.integrator import IcebergTrajectoryIntegrator
from data_ingestion.iceberg.environment_adapter import AntarcticEnvironmentAdapter

logger = get_logger("data_ingestion.iceberg.ensemble")


class IcebergEnsembleGenerator:
    """Generates stochastic trajectory ensembles and calculates spread statistics."""

    def __init__(
        self,
        integrator: IcebergTrajectoryIntegrator,
        default_ensemble_size: int = 25,
        random_seed: int = 42,
    ):
        self.integrator = integrator
        self.default_ensemble_size = default_ensemble_size
        self.random_seed = random_seed

    def generate_ensemble(
        self,
        iceberg_id: str,
        start_time: datetime,
        start_lat: float,
        start_lon: float,
        initial_u: float = 0.0,
        initial_v: float = 0.0,
        horizon_hours: float = 2160.0,  # 90 days default
        ensemble_size: Optional[int] = None,
        base_profile: Optional[IcebergPhysicalProfile] = None,
    ) -> Tuple[List[TrajectoryPoint], List[EnsembleSpreadPoint]]:
        """
        Executes stochastic trajectory realizations and computes ensemble spread metrics.
        """
        n_members = ensemble_size or self.default_ensemble_size
        rng = np.random.RandomState(self.random_seed)
        profile = base_profile or IcebergPhysicalProfile()

        all_points: List[TrajectoryPoint] = []
        member_trajectories: List[List[TrajectoryPoint]] = []

        # Member 0: Deterministic baseline (unperturbed)
        det_traj = self.integrator.integrate_trajectory(
            iceberg_id=iceberg_id,
            start_time=start_time,
            start_lat=start_lat,
            start_lon=start_lon,
            initial_u=initial_u,
            initial_v=initial_v,
            horizon_hours=horizon_hours,
            profile=profile,
            ensemble_id=0,
        )
        all_points.extend(det_traj)
        member_trajectories.append(det_traj)

        # Members 1 to n_members - 1: Stochastic perturbed realizations
        for m_id in range(1, n_members):
            # 1. Perturb initial position (~ 1-2 km std dev)
            dlat = rng.normal(0.0, 0.015)  # ~1.6 km
            dlon = rng.normal(0.0, 0.035)  # ~1.8 km at 65°S
            p_lat = start_lat + dlat
            p_lon = start_lon + dlon

            # 2. Perturb initial velocity (+/- 15%)
            p_u = initial_u + rng.normal(0.0, max(0.02, abs(initial_u) * 0.15))
            p_v = initial_v + rng.normal(0.0, max(0.02, abs(initial_v) * 0.15))

            # 3. Perturb physical profile (dimensions +/- 15%, drag coefficients +/- 10%)
            scale_dim = rng.uniform(0.85, 1.15)
            c_w = profile.water_drag_coeff * rng.uniform(0.9, 1.1)
            c_a = profile.air_drag_coeff * rng.uniform(0.9, 1.1)
            p_profile = IcebergPhysicalProfile(
                length_m=profile.length_m * scale_dim,
                width_m=profile.width_m * scale_dim,
                thickness_m=profile.thickness_m * scale_dim,
                water_drag_coeff=c_w,
                air_drag_coeff=c_a,
            )

            traj = self.integrator.integrate_trajectory(
                iceberg_id=iceberg_id,
                start_time=start_time,
                start_lat=p_lat,
                start_lon=p_lon,
                initial_u=p_u,
                initial_v=p_v,
                horizon_hours=horizon_hours,
                profile=p_profile,
                ensemble_id=m_id,
            )
            all_points.extend(traj)
            member_trajectories.append(traj)

        # 4. Calculate timestep-level spread metrics
        spread_points = self.compute_spread_metrics(member_trajectories)
        logger.info(
            "Generated trajectory ensemble",
            iceberg_id=iceberg_id,
            members=n_members,
            horizon_hours=horizon_hours,
            total_points=len(all_points),
        )
        return all_points, spread_points

    def compute_spread_metrics(
        self,
        trajectories: List[List[TrajectoryPoint]],
    ) -> List[EnsembleSpreadPoint]:
        """
        Calculates ensemble statistics at each aligned simulation timestamp.
        """
        if not trajectories:
            return []

        # Find maximum length
        max_steps = max(len(t) for t in trajectories)
        spread_list: List[EnsembleSpreadPoint] = []

        for step_idx in range(max_steps):
            active_lats: List[float] = []
            active_lons: List[float] = []
            t_stamp: Optional[datetime] = None
            active_count = 0
            grounded_count = 0

            for traj in trajectories:
                if step_idx < len(traj):
                    pt = traj[step_idx]
                    t_stamp = pt.time
                    active_lats.append(pt.latitude)
                    active_lons.append(pt.longitude)
                    if pt.status == TrajectoryStatus.GROUNDED:
                        grounded_count += 1
                    else:
                        active_count += 1
                else:
                    # If trajectory ended early (e.g. grounded), repeat last point
                    pt = traj[-1]
                    active_lats.append(pt.latitude)
                    active_lons.append(pt.longitude)
                    grounded_count += 1

            if not active_lats or t_stamp is None:
                continue

            mean_lat = float(np.mean(active_lats))
            mean_lon = float(np.mean(active_lons))
            med_lat = float(np.median(active_lats))
            med_lon = float(np.median(active_lons))
            std_lat = float(np.std(active_lats))
            std_lon = float(np.std(active_lons))

            # Distances from centroid to all members
            dists = [
                haversine_distance_km(mean_lat, mean_lon, lat, lon)
                for lat, lon in zip(active_lats, active_lons)
            ]
            bounding_rad = float(np.max(dists)) if dists else 0.0
            p50_rad = float(np.percentile(dists, 50)) if dists else 0.0
            p90_rad = float(np.percentile(dists, 90)) if dists else 0.0

            spread_list.append(
                EnsembleSpreadPoint(
                    time=t_stamp,
                    mean_latitude=round(mean_lat, 5),
                    mean_longitude=round(mean_lon, 5),
                    median_latitude=round(med_lat, 5),
                    median_longitude=round(med_lon, 5),
                    std_latitude=round(std_lat, 5),
                    std_longitude=round(std_lon, 5),
                    bounding_radius_km=round(bounding_rad, 2),
                    p50_radius_km=round(p50_rad, 2),
                    p90_radius_km=round(p90_rad, 2),
                    active_member_count=active_count,
                    grounded_member_count=grounded_count,
                )
            )

        return spread_list
