"""
NSIDC Sea Ice Polar Stereographic South (EPSG:3412) Coordinate Transformations.
Handles projection transformations, 2D meshgrid generation, and coordinate resolution.
"""

from typing import Tuple
import numpy as np
import pyproj

# Official NSIDC Polar Stereographic South projection definition (EPSG:3412)
# Hughes 1980 ellipsoid, standard parallel 70°S, central meridian 0°E
EPSG_CODE = 3412
PROJ4_STRING = (
    "+proj=stere +lat_0=-90 +lat_ts=-70 +lon_0=0 +k=1 "
    "+x_0=0 +y_0=0 +a=6378273 +b=6356889.449 +units=m +no_defs"
)

# Standard G02202 25km grid specifications
GRID_SPACING_M = 25000.0
DEFAULT_N_X = 316
DEFAULT_N_Y = 332
DEFAULT_X_MIN = -3937500.0
DEFAULT_X_MAX = 3937500.0
DEFAULT_Y_MIN = -3937500.0
DEFAULT_Y_MAX = 4337500.0


class NSIDCCoordinateTransformer:
    """
    Bidirectional coordinate transformer between NSIDC Polar Stereographic South (EPSG:3412)
    and Geographic WGS84 (EPSG:4326).
    """

    def __init__(self):
        self.crs_projected = pyproj.CRS.from_string(PROJ4_STRING)
        self.crs_geographic = pyproj.CRS.from_epsg(4326)
        # always_xy=True ensures (x, y) or (lon, lat) ordering
        self.to_geographic_transformer = pyproj.Transformer.from_crs(
            self.crs_projected, self.crs_geographic, always_xy=True
        )
        self.to_projected_transformer = pyproj.Transformer.from_crs(
            self.crs_geographic, self.crs_projected, always_xy=True
        )

    def xy_to_lonlat(self, x: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert projected coordinates (meters) to geographic coordinates (lon, lat in degrees).
        Args:
            x: 1D array or 2D meshgrid of x coordinates in meters.
            y: 1D array or 2D meshgrid of y coordinates in meters.
        Returns:
            Tuple of (longitude, latitude) arrays in decimal degrees.
        """
        lon, lat = self.to_geographic_transformer.transform(x, y)
        return lon, lat

    def lonlat_to_xy(self, lon: float, lat: float) -> Tuple[float, float]:
        """
        Convert geographic coordinates (lon, lat in degrees) to projected coordinates (meters).
        Args:
            lon: Longitude in degrees East [-180, 180].
            lat: Latitude in degrees North [-90, 0].
        Returns:
            Tuple of (x, y) in meters.
        """
        x, y = self.to_projected_transformer.transform(lon, lat)
        return float(x), float(y)

    def generate_latlon_grid(
        self, x_coords: np.ndarray, y_coords: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate 2D (latitude, longitude) coordinate arrays for 1D grid coordinate vectors.
        Args:
            x_coords: 1D array of x coordinates (length 316).
            y_coords: 1D array of y coordinates (length 332, descending).
        Returns:
            Tuple of 2D arrays: (lats, lons) with shape (len(y), len(x)).
        """
        xx, yy = np.meshgrid(x_coords, y_coords)
        lons, lats = self.xy_to_lonlat(xx, yy)
        return lats, lons

    def find_nearest_index(
        self,
        lat: float,
        lon: float,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
    ) -> Tuple[int, int]:
        """
        Find nearest (row_y, col_x) grid cell index for a given (lat, lon) in O(1) time.
        Args:
            lat: Latitude in degrees.
            lon: Longitude in degrees.
            x_coords: 1D array of x coordinates (ascending).
            y_coords: 1D array of y coordinates (descending).
        Returns:
            Tuple of (row_idx, col_idx).
        """
        px, py = self.lonlat_to_xy(lon, lat)
        # x is ascending: x_0 = x_coords[0], spacing = 25000
        col = int(np.round((px - x_coords[0]) / GRID_SPACING_M))
        # y is descending: y_0 = y_coords[0], spacing = -25000
        row = int(np.round((y_coords[0] - py) / GRID_SPACING_M))

        col = max(0, min(len(x_coords) - 1, col))
        row = max(0, min(len(y_coords) - 1, row))
        return row, col


default_transformer = NSIDCCoordinateTransformer()
