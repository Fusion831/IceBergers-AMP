"""Sea ice forecasting, uncertainty, and baseline comparison domain schemas."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import BoundingBox


class SeaIceForecast(BaseModel):
    """Predicted sea ice concentration field metadata and summary statistics."""
    forecast_id: str
    model_name: str = "AMIP-Mock-UNet-v1"
    model_version: str = "1.0.0"
    initialization_time: datetime
    valid_time: datetime
    lead_time_days: int = Field(default=0, ge=0)
    bounds: Optional[BoundingBox] = None
    mean_sic: float = Field(default=0.0, ge=0.0, le=1.0)
    total_ice_area_sqkm: float = Field(default=0.0, ge=0.0)
    ice_edge_perimeter_km: float = Field(default=0.0, ge=0.0)
    data_ref: Optional[str] = None
    values: Optional[List[List[float]]] = None
    is_mock: bool = Field(default=True)


class SeaIceUncertainty(BaseModel):
    """Ensemble-derived uncertainty and quantile fields."""
    forecast_id: str
    valid_time: datetime
    mean_variance: float = Field(default=0.05, ge=0.0, le=1.0)
    p10_data_ref: Optional[str] = None
    p50_data_ref: Optional[str] = None
    p90_data_ref: Optional[str] = None
    high_uncertainty_area_sqkm: float = Field(default=0.0, ge=0.0)
    values: Optional[List[List[float]]] = None


class SeaIcePredictionResult(BaseModel):
    """Consolidated result returned by SeaIceModelInterface."""
    forecast: SeaIceForecast
    uncertainty: SeaIceUncertainty
    contour_15pct_geojson: Optional[Dict[str, Any]] = None
    ice_edge_geojson: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def sync_geojson(self) -> "SeaIcePredictionResult":
        if self.contour_15pct_geojson is not None and self.ice_edge_geojson is None:
            self.ice_edge_geojson = self.contour_15pct_geojson
        elif self.ice_edge_geojson is not None and self.contour_15pct_geojson is None:
            self.contour_15pct_geojson = self.ice_edge_geojson
        return self


class SeaIceSkillMetrics(BaseModel):
    """Verification metrics comparing forecast to ground truth observations."""
    mean_absolute_error: float = Field(default=0.045, ge=0.0)
    root_mean_squared_error: float = Field(default=0.068, ge=0.0)
    anomaly_correlation_coeff: float = Field(default=0.88, ge=-1.0, le=1.0)
    integrated_ice_edge_error_sqkm: float = Field(default=1200.0, ge=0.0)


class BaselineComparison(BaseModel):
    """Benchmark comparing AI model skill to persistence and climatology."""
    ai_model_name: str = "AMIP-Mock-UNet-v1"
    baseline_name: str = "Persistence & Climatology"
    evaluation_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lead_time_days: int = 14
    ai_metrics: Optional[SeaIceSkillMetrics] = Field(default_factory=SeaIceSkillMetrics)
    baseline_metrics: Optional[SeaIceSkillMetrics] = Field(default_factory=SeaIceSkillMetrics)
    rmse_improvement_pct: float = 24.5
    iiee_improvement_pct: float = 31.0
    mean_absolute_error: float = 0.048
    root_mean_squared_error: float = 0.072
    brier_score: float = 0.035
