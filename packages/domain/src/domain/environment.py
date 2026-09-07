"""Environmental state and spatiotemporal grid schemas."""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, model_validator
from domain.coordinates import BoundingBox, GeoPoint


class LayerMetadata(BaseModel):
    """Metadata describing an environmental variable layer."""
    variable: str = Field(..., json_schema_extra={"example": "sea_ice_concentration"})
    units: str = Field(..., json_schema_extra={"example": "fraction (0.0 to 1.0)"})
    source_agency: str = Field(..., json_schema_extra={"example": "NSIDC / AMIP-UNet-v1"})
    initialization_time: datetime
    valid_time: datetime
    lead_time_days: int = Field(default=0, ge=0)
    spatial_resolution_km: float = 10.0


class GridSlice(BaseModel):
    """2D raster slice of environmental variables at a specific timestamp for time-slider display."""
    variable: str = "multi-variable"
    units: str = "physical"
    valid_time: datetime
    lead_time_days: int = 0
    bounds: Optional[BoundingBox] = None
    bbox: Optional[BoundingBox] = None
    grid_shape: List[int] = Field(default_factory=lambda: [50, 50])
    min_value: float = 0.0
    max_value: float = 1.0
    mean_value: float = 0.5
    values: Optional[List[List[float]]] = None
    layers: Optional[Dict[str, Any]] = None
    contour_geojson: Optional[Dict[str, Any]] = None
    data_ref: Optional[str] = None
    tile_url: Optional[str] = None

    @model_validator(mode="after")
    def sync_slice_fields(self) -> "GridSlice":
        if self.bounds is not None and self.bbox is None:
            self.bbox = self.bounds
        elif self.bbox is not None and self.bounds is None:
            self.bounds = self.bbox
        elif self.bounds is None and self.bbox is None:
            self.bounds = BoundingBox(min_latitude=-75.0, min_longitude=0.0, max_latitude=-50.0, max_longitude=80.0)
            self.bbox = self.bounds
        return self


class PointEnvironment(BaseModel):
    """Environmental and meteorological conditions at a specific geographic point and time."""
    position: Optional[GeoPoint] = None
    point: Optional[GeoPoint] = None
    timestamp: Optional[datetime] = None
    valid_time: Optional[datetime] = None
    sea_ice_concentration: float = Field(default=0.0, ge=0.0, le=1.0)
    ice_thickness_m: float = Field(default=0.0, ge=0.0)
    sea_surface_temp_c: float = 0.0
    sst_c: Optional[float] = None
    wind_speed_knots: float = Field(default=15.0, ge=0.0)
    wind_speed: Optional[float] = None
    wind_direction_deg: float = Field(default=270.0, ge=0.0, le=360.0)
    ocean_current_speed_knots: float = Field(default=0.5, ge=0.0)
    ocean_current_direction_deg: float = Field(default=90.0, ge=0.0, le=360.0)
    significant_wave_height_m: float = Field(default=2.5, ge=0.0)
    wave_height_m: Optional[float] = None
    wave_peak_period_s: float = Field(default=8.0, ge=0.0)
    water_depth_m: float = Field(default=3000.0, description="Bathymetric depth in meters")
    depth_m: Optional[float] = None
    is_land: bool = False

    @model_validator(mode="after")
    def sync_point_fields(self) -> "PointEnvironment":
        if self.position is not None and self.point is None:
            self.point = self.position
        elif self.point is not None and self.position is None:
            self.position = self.point

        if self.timestamp is not None and self.valid_time is None:
            self.valid_time = self.timestamp
        elif self.valid_time is not None and self.timestamp is None:
            self.timestamp = self.valid_time

        if self.wave_height_m is not None:
            self.significant_wave_height_m = self.wave_height_m
        else:
            self.wave_height_m = self.significant_wave_height_m

        if self.wind_speed is not None:
            self.wind_speed_knots = self.wind_speed
        else:
            self.wind_speed = self.wind_speed_knots

        if self.depth_m is not None:
            self.water_depth_m = self.depth_m
        else:
            self.depth_m = self.water_depth_m

        if self.sst_c is not None:
            self.sea_surface_temp_c = self.sst_c
        else:
            self.sst_c = self.sea_surface_temp_c

        return self


class EnvironmentalState(BaseModel):
    """Combined environmental state descriptor for risk calculation at valid_time."""
    valid_time: datetime
    lead_time_days: int
    sic_grid_ref: str
    uncertainty_grid_ref: Optional[str] = None
    wind_u_ref: Optional[str] = None
    wind_v_ref: Optional[str] = None
    current_u_ref: Optional[str] = None
    current_v_ref: Optional[str] = None
    wave_height_ref: Optional[str] = None
    bathymetry_ref: Optional[str] = None


class EnvironmentCell(BaseModel):
    """Discrete computational environmental grid cell with complete multi-modal physical attribution."""
    cell_id: str = Field(..., description="Structured cell identifier: grid_{res}_{row}_{col}")
    alias: Optional[str] = Field(default=None, description="Human-readable alias if a designated target, e.g. S17, BHARATI")
    point: GeoPoint = Field(..., description="Cell centroid coordinate")
    row: int = Field(default=0, ge=0)
    col: int = Field(default=0, ge=0)
    resolution_deg: float = Field(default=1.0, gt=0.0)
    timestamp: datetime = Field(..., description="Valid timestamp for this physical state")
    sea_ice_concentration: float = Field(default=0.0, ge=0.0, le=1.0)
    sea_ice_uncertainty: float = Field(default=0.05, ge=0.0, le=1.0)
    current_u_ms: float = Field(default=0.0, description="Eastward ocean velocity in m/s")
    current_v_ms: float = Field(default=0.0, description="Northward ocean velocity in m/s")
    wind_u_ms: float = Field(default=0.0, description="10m eastward wind in m/s")
    wind_v_ms: float = Field(default=0.0, description="10m northward wind in m/s")
    wind_speed_ms: float = Field(default=0.0, ge=0.0)
    wave_height_m: float = Field(default=2.5, ge=0.0)
    wave_period_s: float = Field(default=8.0, ge=0.0)
    bathymetry_depth_m: float = Field(default=3500.0)
    iceberg_hazard: float = Field(default=0.05, ge=0.0, le=1.0)
    composite_risk: float = Field(default=0.10, ge=0.0, le=1.0)
    is_land: bool = Field(default=False)
    is_ice_shelf: bool = Field(default=False)
    is_navigable: bool = Field(default=True)
    provenance: str = Field(default="MOCK / SYNTHETIC")


class EnvironmentCellCollection(BaseModel):
    """Sub-grid collection of computational cells for a visible map region and timestamp."""
    valid_time: datetime
    resolution_deg: float
    bounds: BoundingBox
    total_cells: int
    cells: List[EnvironmentCell]

