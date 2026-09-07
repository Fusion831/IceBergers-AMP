"""
Geometry utilities and coordinate conversions for H3 cells.
Handles H3-to-Polygon projections in WGS84 (EPSG:4326) and Antarctic Polar Stereographic (EPSG:3031).
"""

from typing import List, Tuple, Dict, Any, Optional, Set
import h3
import pyproj
from shapely.geometry import Polygon, box
from core.logging import get_logger

logger = get_logger("data_ingestion.h3.geometry")


class H3GeometryEngine:
    """Provides spatial projections, polygon conversions, and neighborhood queries for H3 cells."""

    def __init__(self):
        self.to_epsg3031 = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)
        self.to_epsg4326 = pyproj.Transformer.from_crs("EPSG:3031", "EPSG:4326", always_xy=True)

    @staticmethod
    def latlng_to_cell(lat: float, lon: float, resolution: int = 5) -> str:
        """Converts lat/lon coordinate into an H3 cell index."""
        # Normalize lon to [-180, 180]
        norm_lon = ((lon + 180.0) % 360.0) - 180.0
        return h3.latlng_to_cell(lat, norm_lon, resolution)

    @staticmethod
    def cell_to_latlng(cell_id: str) -> Tuple[float, float]:
        """Returns the centroid (latitude, longitude) of the H3 cell."""
        return h3.cell_to_latlng(cell_id)

    @staticmethod
    def cell_to_polygon_4326(cell_id: str) -> Polygon:
        """Returns the H3 cell boundary as a Shapely Polygon in EPSG:4326 (lon, lat)."""
        boundary = h3.cell_to_boundary(cell_id)
        # boundary is sequence of (lat, lng) pairs
        coords = [(lng, lat) for lat, lng in boundary]
        return Polygon(coords)

    def cell_to_polygon_3031(self, cell_id: str) -> Polygon:
        """Returns the H3 cell boundary projected into Antarctic Polar Stereographic (EPSG:3031)."""
        boundary = h3.cell_to_boundary(cell_id)
        coords_3031 = [
            self.to_epsg3031.transform(lng, lat)
            for lat, lng in boundary
        ]
        return Polygon(coords_3031)

    @staticmethod
    def neighboring_cells(cell_id: str, k: int = 1) -> Set[str]:
        """Returns the k-ring neighbors around an H3 cell (including or excluding origin)."""
        return set(h3.grid_disk(cell_id, k))

    @staticmethod
    def get_approx_cell_area_km2(resolution: int) -> float:
        """Returns approximate area of an H3 cell in square kilometers."""
        # Standard average H3 cell areas (km^2)
        areas = {
            0: 4250546.85,
            1: 607220.98,
            2: 86745.85,
            3: 12392.26,
            4: 1770.32,
            5: 252.90,
            6: 36.13,
            7: 5.16,
            8: 0.74,
        }
        return areas.get(resolution, 252.90)

    @staticmethod
    def get_approx_cell_edge_km(resolution: int) -> float:
        """Returns approximate edge length of an H3 cell in kilometers."""
        edges = {
            0: 1107.71,
            1: 418.68,
            2: 158.24,
            3: 59.81,
            4: 22.61,
            5: 8.54,
            6: 3.23,
            7: 1.22,
            8: 0.46,
        }
        return edges.get(resolution, 8.54)

    @staticmethod
    def is_valid(cell_id: str) -> bool:
        """Validates H3 cell identifier."""
        try:
            return h3.is_valid_cell(cell_id)
        except Exception:
            return False
