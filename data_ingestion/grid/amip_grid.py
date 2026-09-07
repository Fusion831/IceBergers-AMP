"""
Canonical AMIP Computational Grid Interface.
Provides stable cell indexing, boundaries, centroids, and fast O(1) spatial lookup.
Acts as an architectural interface pending multi-dataset inspection.
"""

from typing import Optional, Tuple, Dict, List
import numpy as np
from pydantic import BaseModel, Field
from domain.coordinates import BoundingBox, GeoPoint


class GridCell(BaseModel):
    """Spatial definition of a single AMIP computational grid cell."""
    cell_id: str
    row: int
    col: int
    centroid_lat: float
    centroid_lon: float
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float


class AMIPGrid:
    """
    Canonical 2D Computational Grid for AMIP.
    Maps geographic coordinates into stable cell identifiers and geometries.
    """

    def __init__(
        self,
        bbox: Optional[BoundingBox] = None,
        resolution_deg: float = 0.25,
    ):
        # Default Southern Ocean / Antarctic domain
        self.bbox = bbox or BoundingBox(
            min_latitude=-80.0,
            max_latitude=-40.0,
            min_longitude=-180.0,
            max_longitude=180.0,
        )
        self.resolution_deg = resolution_deg

        self.lat_span = self.bbox.max_latitude - self.bbox.min_latitude
        self.lon_span = self.bbox.max_longitude - self.bbox.min_longitude

        self.n_rows = int(np.ceil(self.lat_span / self.resolution_deg))
        self.n_cols = int(np.ceil(self.lon_span / self.resolution_deg))

    def get_cell_id(self, row: int, col: int) -> str:
        """Stable cell identifier."""
        return f"c_{row:04d}_{col:04d}"

    def find_cell(self, lat: float, lon: float) -> Optional[GridCell]:
        """
        O(1) lookup of the grid cell containing (lat, lon).
        Returns None if point is outside the grid bounding box.
        """
        if not (self.bbox.min_latitude <= lat <= self.bbox.max_latitude):
            return None
        if not (self.bbox.min_longitude <= lon <= self.bbox.max_longitude):
            return None

        # Row 0 starts at max_latitude (descending latitude)
        row = int((self.bbox.max_latitude - lat) / self.resolution_deg)
        col = int((lon - self.bbox.min_longitude) / self.resolution_deg)

        row = min(self.n_rows - 1, max(0, row))
        col = min(self.n_cols - 1, max(0, col))

        lat_max = self.bbox.max_latitude - row * self.resolution_deg
        lat_min = lat_max - self.resolution_deg
        lon_min = self.bbox.min_longitude + col * self.resolution_deg
        lon_max = lon_min + self.resolution_deg

        return GridCell(
            cell_id=self.get_cell_id(row, col),
            row=row,
            col=col,
            centroid_lat=round((lat_min + lat_max) / 2.0, 4),
            centroid_lon=round((lon_min + lon_max) / 2.0, 4),
            lat_min=round(lat_min, 4),
            lat_max=round(lat_max, 4),
            lon_min=round(lon_min, 4),
            lon_max=round(lon_max, 4),
        )
