"""Environmental risk engine configuration, composite surfaces, and factor attribution."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import BoundingBox, GeoPoint
from domain.vessel import VesselProfile


class RiskWeightsConfig(BaseModel):
    """Configurable weights for fusing multi-hazard environmental inputs into R(x, y, t)."""
    weight_sea_ice: float = Field(default=0.40, ge=0.0, le=2.0)
    weight_iceberg_hazard: float = Field(default=0.25, ge=0.0, le=2.0)
    weight_wind: float = Field(default=0.15, ge=0.0, le=2.0)
    weight_waves: float = Field(default=0.10, ge=0.0, le=2.0)
    weight_current_cost: float = Field(default=0.05, ge=0.0, le=2.0)
    weight_uncertainty: float = Field(default=0.05, ge=0.0, le=2.0)


class RiskFactorAttribution(BaseModel):
    """Explainable factor decomposition showing why a cell or waypoint is risky."""
    sea_ice_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    iceberg_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    weather_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    wave_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    current_penalty: float = Field(default=0.0, ge=-0.5, le=1.0)
    is_hard_constrained: bool = Field(default=False)
    hard_constraint_violated: bool = Field(default=False)
    sea_ice_concentration: float = Field(default=0.0, ge=0.0, le=1.0)
    composite_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    dominant_hazard: str = Field(default="NONE", json_schema_extra={"example": "HIGH_SEA_ICE_CONCENTRATION"})
    explanation: str = "Conditions within normal operating envelope."

    @model_validator(mode="after")
    def sync_attribution(self) -> "RiskFactorAttribution":
        if self.hard_constraint_violated and not self.is_hard_constrained:
            self.is_hard_constrained = True
        if self.is_hard_constrained and not self.hard_constraint_violated:
            self.hard_constraint_violated = True
        return self


class RiskField(BaseModel):
    """Composite 2D environmental navigation risk representation R(x, y, t)."""
    valid_time: datetime
    lead_time_days: int = 14
    bounds: Optional[BoundingBox] = None
    bbox: Optional[BoundingBox] = None
    grid_shape: List[int] = Field(default_factory=lambda: [50, 50])
    mean_risk: float = Field(default=0.2, ge=0.0, le=1.0)
    max_risk: float = Field(default=0.8, ge=0.0, le=1.0)
    p90_risk: float = Field(default=0.5, ge=0.0, le=1.0)
    p95_risk: Optional[float] = None
    impassable_cells_count: int = Field(default=0, ge=0)
    impassable_area_sqkm: float = Field(default=0.0, ge=0.0)
    data_ref: Optional[str] = "internal://risk-field"
    hard_constraint_mask_ref: Optional[str] = None
    contour_geojson: Optional[Dict[str, Any]] = None
    values: Optional[List[List[float]]] = None
    hard_constraint_mask: Optional[List[List[bool]]] = None

    @model_validator(mode="after")
    def sync_risk_field(self) -> "RiskField":
        if self.bounds is not None and self.bbox is None:
            self.bbox = self.bounds
        elif self.bbox is not None and self.bounds is None:
            self.bounds = self.bbox
        elif self.bounds is None and self.bbox is None:
            self.bounds = BoundingBox(min_latitude=-75.0, min_longitude=0.0, max_latitude=-50.0, max_longitude=80.0)
            self.bbox = self.bounds

        if self.p95_risk is None:
            self.p95_risk = round(min(1.0, self.p90_risk * 1.1), 3)

        if self.values is not None and not self.grid_shape:
            self.grid_shape = [len(self.values), len(self.values[0]) if self.values else 0]
        return self


class PointRiskQuery(BaseModel):
    """Query to inspect local risk and factor attribution at an arbitrary point and time."""
    position: Optional[GeoPoint] = None
    point: Optional[GeoPoint] = None
    timestamp: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    vessel_profile: Optional[VesselProfile] = None
    risk_weights: Optional[RiskWeightsConfig] = None

    @model_validator(mode="after")
    def sync_query(self) -> "PointRiskQuery":
        if self.position is not None and self.point is None:
            self.point = self.position
        elif self.point is not None and self.position is None:
            self.position = self.point

        if self.timestamp is not None and self.valid_time is None:
            self.valid_time = self.timestamp
        elif self.valid_time is not None and self.timestamp is None:
            self.timestamp = self.valid_time

        if self.valid_time is None:
            self.valid_time = datetime.now(timezone.utc)
            self.timestamp = self.valid_time
        return self
