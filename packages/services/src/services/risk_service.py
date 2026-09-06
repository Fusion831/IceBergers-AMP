"""Risk Service coordinating environmental fields, iceberg hazards, and composite risk evaluation."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.vessel import VesselProfile
from domain.risk import RiskWeightsConfig, RiskField, RiskFactorAttribution
from domain.environment import GridSlice
from domain.iceberg import IcebergHazardField
from domain.sea_ice import SeaIcePredictionResult
from risk_engine.interface import RiskEngineInterface
from risk_engine.engine import RiskEngine
from services.environment_service import EnvironmentService
from services.sea_ice_service import SeaIceService
from services.iceberg_service import IcebergService

logger = logging.getLogger(__name__)


class RiskService:
    """Evaluates composite spatiotemporal risk R(x,y,t) using physical layers and iceberg hazards."""

    def __init__(
        self,
        risk_engine: Optional[RiskEngineInterface] = None,
        env_service: Optional[EnvironmentService] = None,
        sea_ice_service: Optional[SeaIceService] = None,
        iceberg_service: Optional[IcebergService] = None,
    ) -> None:
        self.risk_engine = risk_engine or RiskEngine()
        self.env_service = env_service or EnvironmentService()
        self.sea_ice_service = sea_ice_service or SeaIceService()
        self.iceberg_service = iceberg_service or IcebergService()

    def get_risk_field(
        self,
        valid_time: datetime,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
        bbox: Optional[BoundingBox] = None,
        grid_spec: Optional[GridSpec] = None,
        horizon_days: int = 14,
    ) -> RiskField:
        """Compute composite risk field R(x, y, t) for a given timestamp."""
        # 1. Fetch physical ocean & atmospheric grid slice
        env_slice = self.env_service.get_slice(valid_time=valid_time, bbox=bbox, grid_spec=grid_spec)

        # 2. Fetch sea-ice forecast
        sic_result = self.sea_ice_service.get_forecast(
            reference_time=valid_time,
            horizon_days=horizon_days,
            bbox=bbox,
            grid_spec=grid_spec,
        )

        # 3. Fetch iceberg hazard field
        iceberg_hazard = self.iceberg_service.get_hazard_field(
            valid_time=valid_time,
            bbox=bbox,
            grid_spec=grid_spec,
        )

        # 4. Synthesize with RiskEngine
        risk_field = self.risk_engine.evaluate_grid(
            valid_time=valid_time,
            env_slice=env_slice,
            sea_ice_forecast=sic_result,
            iceberg_hazard=iceberg_hazard,
            vessel=vessel,
            weights=weights,
        )

        return risk_field

    def evaluate_point_risk(
        self,
        point: GeoPoint,
        valid_time: datetime,
        vessel: Optional[VesselProfile] = None,
        weights: Optional[RiskWeightsConfig] = None,
    ) -> Dict[str, Any]:
        """Evaluate point risk and factor attribution."""
        point_env = self.env_service.get_point(point, valid_time)
        sic_forecast = self.sea_ice_service.get_forecast(valid_time, horizon_days=0)
        iceberg_hazard = self.iceberg_service.get_hazard_field(valid_time)

        attribution = self.risk_engine.evaluate_point(
            point=point,
            valid_time=valid_time,
            point_env=point_env,
            sea_ice_forecast=sic_forecast,
            iceberg_hazard=iceberg_hazard,
            vessel=vessel,
            weights=weights,
        )

        return attribution.model_dump()
