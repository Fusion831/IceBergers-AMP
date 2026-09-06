"""Iceberg Service coordinating observations, Lagrangian drift ensembles, and hazard field generation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.iceberg import (
    IcebergObservation,
    IcebergTrajectoryEnsemble,
    IcebergHazardField,
    IcebergSizeClass,
)
from domain.enums import HorizonDay
from iceberg_physics.interface import IcebergDriftEngineInterface, IcebergHazardGeneratorInterface
from iceberg_physics.mock_drift import MockIcebergDriftEngine
from iceberg_physics.hazard_generator import IcebergHazardGenerator
from core.errors import NotFoundError

logger = logging.getLogger(__name__)


# Default synthetic benchmark icebergs in the Indian / Southern Ocean & East Antarctica
DEFAULT_BENCHMARK_ICEBERGS = [
    IcebergObservation(
        iceberg_id="A23a-fragment-01",
        name="A23a Western Flank Fragment",
        observed_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        location=GeoPoint(latitude=-63.5, longitude=-48.2),
        size_class=IcebergSizeClass.VERY_LARGE,
        length_m=42000.0,
        width_m=28000.0,
        estimated_draft_m=260.0,
        source="Sentinel-1 SAR / NIC",
        confidence=0.95,
        drift_speed_knots=0.8,
        drift_heading_deg=35.0,
    ),
    IcebergObservation(
        iceberg_id="IB-PRYDZ-02",
        name="Prydz Bay Calving 2025-C",
        observed_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        location=GeoPoint(latitude=-66.8, longitude=75.4),
        size_class=IcebergSizeClass.LARGE,
        length_m=12000.0,
        width_m=6500.0,
        estimated_draft_m=190.0,
        source="Copernicus Sentinel-2",
        confidence=0.90,
        drift_speed_knots=0.4,
        drift_heading_deg=285.0,
    ),
    IcebergObservation(
        iceberg_id="IB-MAITRI-APPROACH-03",
        name="Astrid Ridge Tabular",
        observed_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        location=GeoPoint(latitude=-68.2, longitude=12.1),
        size_class=IcebergSizeClass.MEDIUM,
        length_m=3500.0,
        width_m=1800.0,
        estimated_draft_m=140.0,
        source="RADARSAT Constellation",
        confidence=0.88,
        drift_speed_knots=0.5,
        drift_heading_deg=260.0,
    ),
    IcebergObservation(
        iceberg_id="IB-SO-DRIFT-04",
        name="Circumpolar Drifter Alpha",
        observed_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        location=GeoPoint(latitude=-58.5, longitude=42.0),
        size_class=IcebergSizeClass.MEDIUM,
        length_m=2800.0,
        width_m=1500.0,
        estimated_draft_m=120.0,
        source="MODIS Aqua",
        confidence=0.85,
        drift_speed_knots=1.1,
        drift_heading_deg=65.0,
    ),
]


class IcebergService:
    """Service for managing iceberg data, running drift simulations, and computing hazards."""

    def __init__(
        self,
        drift_engine: Optional[IcebergDriftEngineInterface] = None,
        hazard_generator: Optional[IcebergHazardGeneratorInterface] = None,
    ) -> None:
        self.drift_engine = drift_engine or MockIcebergDriftEngine()
        self.hazard_generator = hazard_generator or IcebergHazardGenerator()
        self._observations: Dict[str, IcebergObservation] = {
            ib.iceberg_id: ib for ib in DEFAULT_BENCHMARK_ICEBERGS
        }

    def list_observations(
        self,
        bbox: Optional[BoundingBox] = None,
        observed_before: Optional[datetime] = None,
    ) -> List[IcebergObservation]:
        """List active iceberg observations, optionally filtered by bbox and temporal cutoff."""
        results = []
        for ib in self._observations.values():
            if observed_before and ib.observed_at > observed_before:
                continue
            if bbox and not bbox.contains(ib.location):
                continue
            results.append(ib)
        return results

    def get_observation(self, iceberg_id: str) -> IcebergObservation:
        """Fetch an iceberg observation by ID."""
        if iceberg_id not in self._observations:
            raise NotFoundError(f"Iceberg observation '{iceberg_id}' not found.")
        return self._observations[iceberg_id]

    def record_observation(self, observation: IcebergObservation) -> IcebergObservation:
        """Add or update an iceberg observation."""
        self._observations[observation.iceberg_id] = observation
        return observation

    def get_trajectory_ensemble(
        self,
        iceberg_id: str,
        forecast_days: int = 30,
        ensemble_size: int = 50,
        step_hours: int = 6,
        start_time: Optional[datetime] = None,
    ) -> IcebergTrajectoryEnsemble:
        """Compute Lagrangian trajectory ensemble for a specific iceberg."""
        obs = self.get_observation(iceberg_id)
        ensemble = self.drift_engine.simulate_ensemble(
            observation=obs,
            forecast_days=forecast_days,
            ensemble_size=ensemble_size,
            step_hours=step_hours,
            start_time=start_time or obs.observed_at,
        )
        return ensemble

    def get_hazard_field(
        self,
        valid_time: datetime,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        observed_before: Optional[datetime] = None,
    ) -> IcebergHazardField:
        """Compute composite 2D spatial iceberg hazard field H_iceberg(x, y, t)."""
        active_obs = self.list_observations(bbox=bbox, observed_before=observed_before)
        if not active_obs:
            # Fallback to defaults if filtered out
            active_obs = list(self._observations.values())

        # Generate ensembles for all active icebergs
        ensembles: List[IcebergTrajectoryEnsemble] = []
        for obs in active_obs:
            # Calculate days between obs and valid_time
            dt_days = max(1, int((valid_time - obs.observed_at).total_seconds() / 86400.0) + 7)
            ens = self.drift_engine.simulate_ensemble(
                observation=obs,
                forecast_days=dt_days,
                ensemble_size=30,
                step_hours=6,
                start_time=obs.observed_at,
            )
            ensembles.append(ens)

        hazard_field = self.hazard_generator.generate_hazard_field(
            ensembles=ensembles,
            valid_time=valid_time,
            bbox=bbox,
            grid_spec=grid_spec,
        )
        return hazard_field
