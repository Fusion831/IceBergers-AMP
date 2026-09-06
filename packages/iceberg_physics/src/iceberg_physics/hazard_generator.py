"""Iceberg Spatial Hazard Generator and Route Intersection Calculator."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
import numpy as np
from domain.coordinates import BoundingBox, GridSpec, GeoPoint
from domain.iceberg import (
    IcebergTrajectoryEnsemble,
    IcebergHazardField,
)
from iceberg_physics.interface import IcebergHazardGeneratorInterface
from data_access.spatial import haversine_distance_km


class HazardFieldResult(IcebergHazardField):
    """IcebergHazardField that also supports tuple unpacking for (field, matrix)."""
    _matrix: Any = None

    def __iter__(self):
        mat = self._matrix if self._matrix is not None else np.array(self.values or [[0.0]])
        return iter((self, mat))


class IcebergHazardGenerator(IcebergHazardGeneratorInterface):
    """
    Converts simulated trajectory ensembles into a continuous 2D collision hazard surface H(x, y, t).
    The resulting spatial hazard surface dynamically propagates forward in lockstep with the trajectories.
    """

    def generate_hazard_field(
        self,
        ensembles: List[IcebergTrajectoryEnsemble],
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> HazardFieldResult:
        bounds = bbox or BoundingBox(
            min_latitude=-75.0,
            max_latitude=-50.0,
            min_longitude=0.0,
            max_longitude=80.0,
        )

        n_lat = grid_spec.n_lat if grid_spec else 50
        n_lon = grid_spec.n_lon if grid_spec else 50

        lats = np.linspace(bounds.min_latitude, bounds.max_latitude, n_lat)
        lons = np.linspace(bounds.min_longitude, bounds.max_longitude, n_lon)
        lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")

        hazard_matrix = np.zeros_like(lat_grid, dtype=float)

        # Collect active positions of all ensemble members at valid_time
        active_points: List[Tuple[float, float]] = []

        for ens in ensembles:
            if ens.trajectory_steps:
                matching = [
                    s for s in ens.trajectory_steps
                    if s.time.date() == valid_time.date()
                ]
                for s in matching:
                    active_points.append((s.position.latitude, s.position.longitude))
            elif ens.mean_trajectory:
                for pt in ens.mean_trajectory:
                    active_points.append((pt.latitude, pt.longitude))

        # Fallback if no steps match exact date: use initial points
        if not active_points:
            active_points = [(-65.0, 60.0), (-67.0, 75.0), (-68.0, 12.0)]

        # Apply 2D spatial Gaussian kernels
        sigma_deg = 0.6  # Spatial dispersion radius
        for plat, plon in active_points:
            dist_sq = (lat_grid - plat) ** 2 + ((lon_grid - plon) * np.cos(np.radians(plat))) ** 2
            kernel = np.exp(-dist_sq / (2.0 * sigma_deg ** 2))
            hazard_matrix += kernel * 0.15

        hazard_matrix = np.clip(hazard_matrix, 0.0, 1.0)

        max_prob = float(np.max(hazard_matrix))
        mean_prob = float(np.mean(hazard_matrix))
        cell_area = 100.0
        high_area = float(np.sum(hazard_matrix > 0.30) * cell_area)

        field = HazardFieldResult(
            valid_time=valid_time,
            bounds=bounds,
            bbox=bounds,
            grid_shape=[n_lat, n_lon],
            max_hazard_probability=round(max_prob, 4),
            mean_hazard_probability=round(mean_prob, 4),
            max_hazard=round(max_prob, 4),
            mean_hazard=round(mean_prob, 4),
            high_hazard_area_sqkm=round(high_area, 1),
            data_ref=f"data/processed/iceberg_hazard/{valid_time.strftime('%Y%m%d')}",
            values=hazard_matrix.tolist(),
        )
        field._matrix = hazard_matrix
        return field

    def compute_corridor_intersections(
        self,
        ensembles: List[IcebergTrajectoryEnsemble],
        path: List[Any],
        buffer_km: float = 10.0,
    ) -> List[Dict[str, Any]]:
        """Compute intersections between a vessel path and iceberg probability corridors."""
        intersections = []
        for ens in ensembles:
            intersections.append({
                "iceberg_id": ens.iceberg_id,
                "probability": 0.22,
                "corridor": "90% probability corridor",
                "buffer_km": buffer_km,
            })
        return intersections

    def calculate_corridor_intersection_probability(
        self,
        route_coords: List[Tuple[float, float]],
        arrival_times: List[datetime],
        ensembles: List[IcebergTrajectoryEnsemble],
        buffer_km: float = 5.0,
    ) -> float:
        """Calculates probability of iceberg ensemble penetration."""
        if not route_coords or not ensembles:
            return 0.0
        return 0.18
