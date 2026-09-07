"""
Data models and schemas for Antarctic Iceberg Trajectory Pipeline.
Provides strong typing for observations, track reconstructions, physical states,
ensembles, H3 hazard fields, and pipeline execution manifests.
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class IcebergSource(str, Enum):
    BYU_HISTORICAL = "BYU_HISTORICAL"
    USNIC_OPERATIONAL = "USNIC_OPERATIONAL"
    BYU_CURRENT = "BYU_CURRENT"


class InitialVelocityMethod(str, Enum):
    RECENT_VELOCITY = "RECENT_VELOCITY"
    REGIONAL_MEAN_VELOCITY = "REGIONAL_MEAN_VELOCITY"
    ZERO_VELOCITY = "ZERO_VELOCITY"


class ForcingMode(str, Enum):
    DIRECT_FORECAST = "DIRECT_FORECAST"
    EXTENDED_FORCING = "EXTENDED_FORCING"
    CLIMATOLOGY = "CLIMATOLOGY"
    PERSISTENCE = "PERSISTENCE"


class TrajectoryStatus(str, Enum):
    ACTIVE_DRIFT = "ACTIVE_DRIFT"
    GROUNDED = "GROUNDED"
    BLOCKED = "BLOCKED"
    OUT_OF_DOMAIN = "OUT_OF_DOMAIN"


class IcebergObservationRecord(BaseModel):
    """Normalized individual iceberg observation."""
    iceberg_id: str
    source: IcebergSource
    observation_time: datetime
    latitude: float
    longitude: float
    length_km: Optional[float] = None
    width_km: Optional[float] = None
    area_sqkm: Optional[float] = None
    sensor: Optional[str] = None
    is_interpolated: bool = False
    is_valid: bool = True
    flag_reason: Optional[str] = None
    source_file: Optional[str] = None
    source_record_id: Optional[str] = None


class IcebergTrackDiagnostic(BaseModel):
    """Derived track diagnostics for an individual iceberg."""
    iceberg_id: str
    source: IcebergSource
    observation_count: int
    track_start: datetime
    track_end: datetime
    duration_days: float
    median_observation_interval_hours: float
    max_observation_gap_days: float
    total_displacement_km: float
    mean_speed_mps: float
    median_speed_mps: float
    max_speed_mps: float
    flagged_jump_count: int


class TrajectoryPoint(BaseModel):
    """Single discrete step in an iceberg trajectory simulation."""
    iceberg_id: str
    ensemble_id: int = 0
    time: datetime
    latitude: float
    longitude: float
    velocity_u: float
    velocity_v: float
    speed_mps: float
    h3_cell: Optional[str] = None
    status: TrajectoryStatus = TrajectoryStatus.ACTIVE_DRIFT
    forcing_mode: ForcingMode = ForcingMode.DIRECT_FORECAST
    forcing_source: str = "AMIP_ENVIRONMENT"
    model_version: str = "1.0.0"
    current_u: Optional[float] = None
    current_v: Optional[float] = None
    wind_u: Optional[float] = None
    wind_v: Optional[float] = None
    sic: Optional[float] = None
    bathymetry_depth_m: Optional[float] = None


class EnsembleSpreadPoint(BaseModel):
    """Summary statistics for an ensemble of trajectory realizations at a single timestamp."""
    time: datetime
    mean_latitude: float
    mean_longitude: float
    median_latitude: float
    median_longitude: float
    std_latitude: float
    std_longitude: float
    bounding_radius_km: float
    p50_radius_km: float
    p90_radius_km: float
    active_member_count: int
    grounded_member_count: int


class H3HazardCell(BaseModel):
    """Time-dependent H3 spatial occupancy hazard proxy."""
    h3_cell: str
    valid_time: datetime
    hazard: float = Field(ge=0.0, le=1.0)
    supporting_iceberg_count: int = 1
    ensemble_count: int
    active_icebergs: List[str] = Field(default_factory=list)
    model_version: str = "1.0.0"
    forcing_mode: ForcingMode = ForcingMode.DIRECT_FORECAST
    geographic_mask_mode: str = "REAL"


class ModelValidationHorizonMetric(BaseModel):
    """Validation performance at a specific forecast lead-time horizon."""
    horizon: str
    horizon_hours: float
    sample_count: int
    persistence_mean_error_km: Optional[float] = None
    persistence_median_error_km: Optional[float] = None
    persistence_rmse_km: Optional[float] = None
    const_vel_mean_error_km: Optional[float] = None
    const_vel_median_error_km: Optional[float] = None
    const_vel_rmse_km: Optional[float] = None
    physics_mean_error_km: Optional[float] = None
    physics_median_error_km: Optional[float] = None
    physics_rmse_km: Optional[float] = None
    physics_p90_error_km: Optional[float] = None
