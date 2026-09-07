"""
Canonical AMIP EnvironmentCell Schema.
Represents the unified environmental state at a specific grid cell and time.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class EnvironmentCell(BaseModel):
    """
    Canonical environmental state for a specific AMIP computational grid cell and time.
    Serves as the common data contract consumed by:
    - 4D grid router
    - vessel performance and fuel models
    - risk engine
    - iceberg trajectory simulation
    - frontend / Earth-map visualization
    """

    cell_id: str = Field(..., description="Stable grid cell identifier, e.g. c_120_340")
    valid_time: datetime = Field(..., description="Valid timestamp (UTC)")

    # Spatial properties
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Cell centroid latitude")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Cell centroid longitude")
    lat_min: float = Field(..., ge=-90.0, le=90.0)
    lat_max: float = Field(..., ge=-90.0, le=90.0)
    lon_min: float = Field(..., ge=-180.0, le=180.0)
    lon_max: float = Field(..., ge=-180.0, le=180.0)

    # Cryosphere (Sea Ice)
    sea_ice_concentration: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Sea ice area fraction percentage [0.0, 100.0]%",
    )
    sea_ice_uncertainty: Optional[float] = Field(default=None, ge=0.0, le=100.0)

    # Hydrodynamics (Ocean Currents)
    current_u_ms: Optional[float] = Field(default=None, description="Eastward ocean current (m/s)")
    current_v_ms: Optional[float] = Field(default=None, description="Northward ocean current (m/s)")

    # Meteorology (Wind)
    wind_u_ms: Optional[float] = Field(default=None, description="Eastward 10m wind (m/s)")
    wind_v_ms: Optional[float] = Field(default=None, description="Northward 10m wind (m/s)")
    wind_speed_ms: Optional[float] = Field(default=None, ge=0.0, description="Wind magnitude (m/s)")

    # Ocean Waves
    wave_height_m: Optional[float] = Field(default=None, ge=0.0, description="Significant wave height Hs (m)")
    wave_direction_deg: Optional[float] = Field(default=None, ge=0.0, le=360.0)
    wave_period_s: Optional[float] = Field(default=None, ge=0.0)

    # Hazards & Bathymetry
    iceberg_hazard: Optional[float] = Field(default=0.0, ge=0.0, le=1.0, description="Iceberg encounter hazard index")
    bathymetry_depth_m: Optional[float] = Field(default=None, description="Water depth positive in meters")

    # Geographic Masks & Navigability
    is_land: bool = Field(default=False, description="True if cell intersects continental land")
    is_ice_shelf: bool = Field(default=False, description="True if cell intersects permanent ice shelf")
    is_navigable: bool = Field(default=True, description="False if land, ice-shelf, or unsafe shallow bathymetry")

    # Provenance tracking
    provenance: Dict[str, Any] = Field(default_factory=dict, description="Source dataset attribution and timestamps")
