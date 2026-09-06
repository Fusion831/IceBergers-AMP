"""Sea Ice Service coordinating sea-ice forecast models and baselines."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from domain.coordinates import BoundingBox, GridSpec
from domain.sea_ice import SeaIcePredictionResult, BaselineComparison
from domain.enums import HorizonDay
from domain.provenance import ModelRunRecord
from models.base import SeaIceModelInterface
from models.registry import ModelRegistry
from models.sea_ice.mock_model import MockSeaIceModel
from models.sea_ice.baselines import PersistenceBaseline, ClimatologyBaseline, compute_baseline_comparison

logger = logging.getLogger(__name__)


class SeaIceService:
    """Coordinates sea-ice model inference and baseline benchmarking."""

    def __init__(
        self,
        model_registry: Optional[ModelRegistry] = None,
        default_model_id: str = "mock-sea-ice-unet",
    ) -> None:
        self.registry = model_registry or ModelRegistry()
        self.default_model_id = default_model_id
        self.persistence = PersistenceBaseline()
        self.climatology = ClimatologyBaseline()

    def get_forecast(
        self,
        reference_time: datetime,
        horizon_days: int = 14,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        model_id: Optional[str] = None,
    ) -> SeaIcePredictionResult:
        """Run sea-ice forecast for a given reference time and horizon."""
        model = self.registry.get_model(model_id or self.default_model_id)
        prediction = model.predict(
            reference_time=reference_time,
            horizon_days=horizon_days,
            bbox=bbox,
            grid_spec=grid_spec,
        )
        return prediction

    def get_baseline_comparison(
        self,
        reference_time: datetime,
        horizon_days: int = 14,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Dict[str, Any]:
        """Compute forecast along with persistence and climatology baselines."""
        model = self.registry.get_model(self.default_model_id)
        forecast = model.predict(reference_time, horizon_days, bbox, grid_spec)
        persistence = self.persistence.predict(reference_time, horizon_days, bbox, grid_spec)
        climatology = self.climatology.predict(reference_time, horizon_days, bbox, grid_spec)

        comparison = compute_baseline_comparison(forecast, persistence, climatology)

        return {
            "reference_time": reference_time.isoformat(),
            "horizon_days": horizon_days,
            "forecast": forecast.model_dump(),
            "persistence": persistence.model_dump(),
            "climatology": climatology.model_dump(),
            "metrics": comparison.model_dump(),
        }

    def get_multi_horizon_forecast(
        self,
        reference_time: datetime,
        horizons: Optional[List[int]] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
    ) -> Dict[int, SeaIcePredictionResult]:
        """Fetch forecasts across standard AMIP horizons: 0, 7, 14, 30, 60, 90."""
        target_horizons = horizons or [0, 7, 14, 30, 60, 90]
        results: Dict[int, SeaIcePredictionResult] = {}
        for h in target_horizons:
            results[h] = self.get_forecast(reference_time, h, bbox, grid_spec)
        return results
