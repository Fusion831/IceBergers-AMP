"""Geographic coordinates, bounding boxes, and grid specifications."""

from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class GeoPoint(BaseModel):
    """Geographic coordinate in WGS84 decimal degrees."""
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Latitude in decimal degrees North (negative for South)",
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Longitude in decimal degrees East (-180 to 180)",
    )
    name: Optional[str] = Field(default=None, description="Landmark or station name")
    station_code: Optional[str] = Field(default=None, description="Station identifier (e.g. BHARATI)")

    @field_validator("latitude", "longitude")
    @classmethod
    def round_coordinates(cls, v: float) -> float:
        return round(v, 6)

    def to_tuple(self) -> tuple[float, float]:
        return (self.latitude, self.longitude)


class BoundingBox(BaseModel):
    """Spatial bounding box in WGS84."""
    min_latitude: float = Field(..., ge=-90.0, le=90.0)
    min_longitude: float = Field(..., ge=-180.0, le=180.0)
    max_latitude: float = Field(..., ge=-90.0, le=90.0)
    max_longitude: float = Field(..., ge=-180.0, le=180.0)

    @field_validator("max_latitude")
    @classmethod
    def validate_latitude_order(cls, v: float, info) -> float:
        min_lat = info.data.get("min_latitude")
        if min_lat is not None and v <= min_lat:
            raise ValueError("max_latitude must be strictly greater than min_latitude")
        return v

    def contains(self, point: GeoPoint) -> bool:
        """Check if a geographic point is inside this bounding box."""
        return (
            self.min_latitude <= point.latitude <= self.max_latitude
            and self.min_longitude <= point.longitude <= self.max_longitude
        )


class GridSpec(BaseModel):
    """Specification for a 2D spatial raster grid."""
    bounds: Optional[BoundingBox] = None
    resolution_km: float = Field(default=10.0, gt=0.0)
    crs: str = Field(default="EPSG:4326")
    n_lat: int = Field(default=100, gt=1)
    n_lon: int = Field(default=200, gt=1)
    rows: Optional[int] = None
    cols: Optional[int] = None

    @model_validator(mode="after")
    def sync_grid(self) -> "GridSpec":
        if self.bounds is None:
            self.bounds = BoundingBox(
                min_latitude=-75.0,
                max_latitude=-50.0,
                min_longitude=0.0,
                max_longitude=90.0,
            )
        if self.rows is not None:
            self.n_lat = self.rows
        else:
            self.rows = self.n_lat

        if self.cols is not None:
            self.n_lon = self.cols
        else:
            self.cols = self.n_lon
        return self
