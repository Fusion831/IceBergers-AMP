"""Iceberg observation, trajectory ensemble, and spatial hazard domain schemas."""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import BoundingBox, GeoPoint


class IcebergSizeClass(str, Enum):
    VERY_LARGE = "VERY_LARGE"
    LARGE = "LARGE"
    MEDIUM = "MEDIUM"
    SMALL = "SMALL"
    BERGY_BIT = "BERGY_BIT"
    GROWLER = "GROWLER"


class IcebergObservation(BaseModel):
    """Reported iceberg detection from satellite radar (NIC / CMEMS / SAR)."""
    iceberg_id: str
    name: Optional[str] = None
    source: str = Field(default="NIC_ANTARCTIC_DATABASE")
    observation_time: Optional[datetime] = None
    observed_at: Optional[datetime] = None
    position: Optional[GeoPoint] = None
    location: Optional[GeoPoint] = None
    size_class: Optional[IcebergSizeClass] = IcebergSizeClass.MEDIUM
    length_meters: Optional[float] = Field(default=None, ge=10.0, le=200000.0)
    length_m: Optional[float] = None
    width_meters: Optional[float] = Field(default=None, ge=10.0, le=200000.0)
    width_m: Optional[float] = None
    estimated_draft_m: Optional[float] = None
    confidence: float = Field(default=0.90, ge=0.0, le=1.0)
    estimated_drift_speed_knots: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    drift_speed_knots: Optional[float] = None
    estimated_drift_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    drift_heading_deg: Optional[float] = None
    is_grounded: bool = Field(default=False)

    @model_validator(mode="after")
    def sync_observation_fields(self) -> "IcebergObservation":
        if self.observed_at is None:
            self.observed_at = self.observation_time or datetime.now(timezone.utc)
        if self.observation_time is None:
            self.observation_time = self.observed_at

        if self.location is None:
            self.location = self.position or GeoPoint(latitude=-65.0, longitude=50.0)
        if self.position is None:
            self.position = self.location

        if self.length_m is not None and self.length_meters is None:
            self.length_meters = self.length_m
        if self.length_meters is not None and self.length_m is None:
            self.length_m = self.length_meters

        if self.width_m is not None and self.width_meters is None:
            self.width_meters = self.width_m
        if self.width_meters is not None and self.width_m is None:
            self.width_m = self.width_meters

        if self.drift_speed_knots is not None and self.estimated_drift_speed_knots is None:
            self.estimated_drift_speed_knots = self.drift_speed_knots
        if self.estimated_drift_speed_knots is not None and self.drift_speed_knots is None:
            self.drift_speed_knots = self.estimated_drift_speed_knots

        if self.drift_heading_deg is not None and self.estimated_drift_direction_deg is None:
            self.estimated_drift_direction_deg = self.drift_heading_deg
        if self.estimated_drift_direction_deg is not None and self.drift_heading_deg is None:
            self.drift_heading_deg = self.estimated_drift_direction_deg
        return self


class IcebergTrajectoryStep(BaseModel):
    """Discrete point in an individual iceberg trajectory path."""
    time: datetime
    position: GeoPoint
    ensemble_member_id: int = 0
    drift_speed_knots: float = 0.5


class IcebergTrajectoryEnsemble(BaseModel):
    """Stochastic ensemble of simulated iceberg trajectory realization tracks."""
    iceberg_id: str
    simulation_start: datetime
    simulation_end: datetime
    ensemble_size: int = Field(default=50, ge=5, le=200)
    mean_trajectory: Optional[List[GeoPoint]] = None
    median_trajectory: Optional[List[GeoPoint]] = None
    p50_corridor: Optional[List[GeoPoint]] = None
    p90_corridor: Optional[List[GeoPoint]] = None
    members: Optional[List[List[Any]]] = None
    corridor_50_pct_geojson: Dict[str, Any] = Field(default_factory=lambda: {"type": "FeatureCollection", "features": []})
    corridor_90_pct_geojson: Dict[str, Any] = Field(default_factory=lambda: {"type": "FeatureCollection", "features": []})
    trajectory_steps: Optional[List[IcebergTrajectoryStep]] = None

    @model_validator(mode="after")
    def sync_trajectory_fields(self) -> "IcebergTrajectoryEnsemble":
        if self.median_trajectory is None and self.mean_trajectory is not None:
            self.median_trajectory = self.mean_trajectory
        if self.mean_trajectory is None and self.median_trajectory is not None:
            self.mean_trajectory = self.median_trajectory
        if self.p50_corridor is None and self.median_trajectory is not None:
            self.p50_corridor = self.median_trajectory
        if self.p90_corridor is None and self.median_trajectory is not None:
            self.p90_corridor = self.median_trajectory
        return self


class IcebergHazardField(BaseModel):
    """2D spatial collision hazard representation derived from trajectory ensembles."""
    valid_time: datetime
    bounds: Optional[BoundingBox] = None
    bbox: Optional[BoundingBox] = None
    grid_shape: Optional[List[int]] = None
    max_hazard_probability: Optional[float] = None
    mean_hazard_probability: Optional[float] = None
    max_hazard: Optional[float] = None
    mean_hazard: Optional[float] = None
    high_hazard_area_sqkm: float = Field(default=0.0, ge=0.0)
    data_ref: Optional[str] = "internal://iceberg-hazard"
    values: Optional[List[List[float]]] = None

    @model_validator(mode="after")
    def sync_hazard_fields(self) -> "IcebergHazardField":
        if self.bbox is not None and self.bounds is None:
            self.bounds = self.bbox
        if self.bounds is not None and self.bbox is None:
            self.bbox = self.bounds

        if self.max_hazard is not None and self.max_hazard_probability is None:
            self.max_hazard_probability = self.max_hazard
        if self.max_hazard_probability is not None and self.max_hazard is None:
            self.max_hazard = self.max_hazard_probability

        if self.mean_hazard is not None and self.mean_hazard_probability is None:
            self.mean_hazard_probability = self.mean_hazard
        if self.mean_hazard_probability is not None and self.mean_hazard is None:
            self.mean_hazard = self.mean_hazard_probability

        if self.grid_shape is None and self.values is not None:
            self.grid_shape = [len(self.values), len(self.values[0]) if self.values else 0]
        return self
