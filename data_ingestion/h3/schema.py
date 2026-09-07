"""
Canonical Schemas for Static and Dynamic H3 Environmental State.
Provides strongly-typed contracts for application grid cells, ML interfaces, and unified state.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class TemporalQualityStatus(str, Enum):
    """Quality and forecast origin states for temporal environmental data."""
    OBSERVED = "OBSERVED"
    FORECAST = "FORECAST"
    MODEL_PREDICTED = "MODEL_PREDICTED"
    INTERPOLATED = "INTERPOLATED"
    PERSISTED = "PERSISTED"
    CLIMATOLOGICAL = "CLIMATOLOGICAL"
    EXTENDED_PROJECTION = "EXTENDED_PROJECTION"
    MISSING = "MISSING"


class H3GeographicStatus(str, Enum):
    """Geographic classification for an H3 cell."""
    OPEN_OCEAN = "OPEN_OCEAN"
    MIXED = "MIXED"
    LAND = "LAND"
    ICE_SHELF = "ICE_SHELF"
    ICE_TONGUE = "ICE_TONGUE"
    RUMPLE = "RUMPLE"
    UNKNOWN = "UNKNOWN"
    OUTSIDE_DOMAIN = "OUTSIDE_DOMAIN"


class StaticH3Cell(BaseModel):
    """Static spatial, geographic, and bathymetric attributes of an H3 cell."""
    cell_id: str = Field(..., description="Canonical H3 cell index")
    h3_resolution: int = Field(..., description="H3 index resolution level")
    centroid_lat: float = Field(..., ge=-90.0, le=90.0)
    centroid_lon: float = Field(..., ge=-180.0, le=180.0)
    geometry_wkt: str = Field(..., description="WKT polygon in EPSG:4326")

    # SCAR ADD fractional coverage [0.0, 1.0]
    ocean_fraction: float = Field(default=1.0, ge=0.0, le=1.0)
    land_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    ice_shelf_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    ice_tongue_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    rumple_fraction: float = Field(default=0.0, ge=0.0, le=1.0)
    geographic_status: H3GeographicStatus = Field(default=H3GeographicStatus.OPEN_OCEAN)
    is_blocked: bool = Field(default=False)

    # GEBCO 2026 sub-ice bathymetry attributes (positive water depth convention: depth_m > 0)
    bathymetry_valid_fraction: float = Field(default=1.0, ge=0.0, le=1.0)
    bathymetry_mean_m: Optional[float] = Field(default=None, description="Water depth positive in meters")
    bathymetry_min_m: Optional[float] = Field(default=None)
    bathymetry_p10_m: Optional[float] = Field(default=None)
    bathymetry_p50_m: Optional[float] = Field(default=None)
    bathymetry_p90_m: Optional[float] = Field(default=None)


class DynamicH3State(BaseModel):
    """Dynamic environmental state for a specific H3 cell at a specific timestamp."""
    cell_id: str
    valid_time: datetime

    # Cryosphere: NSIDC Sea Ice Concentration
    sea_ice_concentration: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="SIC % [0, 100]")
    sea_ice_uncertainty: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    sic_valid_fraction: float = Field(default=1.0, ge=0.0, le=1.0)

    # Hydrodynamics: CMEMS Ocean Currents
    current_u_ms: Optional[float] = Field(default=None, description="Eastward current m/s")
    current_v_ms: Optional[float] = Field(default=None, description="Northward current m/s")
    current_speed_ms: Optional[float] = Field(default=None, ge=0.0)
    current_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    current_valid_fraction: float = Field(default=1.0, ge=0.0, le=1.0)

    # Meteorology: ECMWF 10m Wind
    wind_u_ms: Optional[float] = Field(default=None, description="Eastward 10m wind m/s")
    wind_v_ms: Optional[float] = Field(default=None, description="Northward 10m wind m/s")
    wind_speed_ms: Optional[float] = Field(default=None, ge=0.0)
    wind_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    wind_valid_fraction: float = Field(default=1.0, ge=0.0, le=1.0)

    # Ocean Waves: CMEMS Waves
    wave_height_m: Optional[float] = Field(default=None, ge=0.0, description="Significant wave height Hs in m")
    wave_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0, description="Circularly aggregated wave direction")
    wave_period_s: Optional[float] = Field(default=None, ge=0.0, description="Wave peak period Tp in s")
    wave_valid_fraction: float = Field(default=1.0, ge=0.0, le=1.0)

    # Hazards: Iceberg Hazard Field
    iceberg_hazard: float = Field(default=0.0, ge=0.0, le=1.0, description="Iceberg encounter/occupancy hazard proxy")
    distinct_iceberg_count: int = Field(default=0, ge=0)
    contributing_iceberg_ids: List[str] = Field(default_factory=list)

    # Quality and provenance
    quality_status: TemporalQualityStatus = Field(default=TemporalQualityStatus.OBSERVED)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class UnifiedEnvironmentCell(BaseModel):
    """
    Complete consolidated cell state combining static geography/bathymetry with dynamic environmental variables.
    Single point of consumption for routing, risk engine, and frontend.
    """
    cell_id: str
    valid_time: datetime
    h3_resolution: int
    centroid_lat: float
    centroid_lon: float

    # Static Geography
    ocean_fraction: float
    land_fraction: float
    ice_shelf_fraction: float
    ice_tongue_fraction: float
    rumple_fraction: float
    geographic_status: str
    is_blocked: bool

    # Static Bathymetry
    bathymetry_depth_m: Optional[float] = None
    bathymetry_min_m: Optional[float] = None
    bathymetry_p10_m: Optional[float] = None
    bathymetry_p90_m: Optional[float] = None

    # Dynamic Variables
    sea_ice_concentration: Optional[float] = None
    sea_ice_uncertainty: Optional[float] = None
    current_u_ms: Optional[float] = None
    current_v_ms: Optional[float] = None
    current_speed_ms: Optional[float] = None
    current_direction_deg: Optional[float] = None
    wind_u_ms: Optional[float] = None
    wind_v_ms: Optional[float] = None
    wind_speed_ms: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    wave_height_m: Optional[float] = None
    wave_direction_deg: Optional[float] = None
    wave_period_s: Optional[float] = None
    iceberg_hazard: float = 0.0
    contributing_iceberg_ids: List[str] = Field(default_factory=list)

    # Navigability indicator
    is_navigable: bool = True
    quality_status: str = "OBSERVED"
    provenance: Dict[str, Any] = Field(default_factory=dict)
