"""
Application-Level Query and Bathymetry Interface for GEBCO 2026.
Provides fast spatial lookups, regional bounding box queries, and vessel
under-keel draft clearance evaluation for AMIP navigation routing and risk engine.
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import numpy as np
import xarray as xr
from core.logging import get_logger
from domain.coordinates import GeoPoint, BoundingBox

logger = get_logger("data_ingestion.gebco.interface")


class BathymetryHazard(str, Enum):
    SAFE = "SAFE"
    SHALLOW = "SHALLOW"
    GROUNDING_RISK = "GROUNDING_RISK"
    LAND = "LAND"
    OUT_OF_BOUNDS = "OUT_OF_BOUNDS"


class GEBCOBathymetryInterface:
    """
    AMIP Query interface for processed GEBCO under-ice bathymetry data.
    Provides fast O(log N) point queries, regional bounding box slicing, and draft safety checks.
    """

    def __init__(self, processed_file_path: Optional[Union[str, Path]] = None):
        self.file_path = Path(processed_file_path or "data/processed/gebco/gebco_2026/bathymetry_processed_antarctic.nc")
        self._ds: Optional[xr.Dataset] = None
        self._lats: Optional[np.ndarray] = None
        self._lons: Optional[np.ndarray] = None
        self._depth_m: Optional[np.ndarray] = None
        self._is_land: Optional[np.ndarray] = None

    def _ensure_loaded(self):
        """Loads and caches dataset arrays in memory for rapid queries."""
        if self._ds is None:
            if not self.file_path.exists():
                raise FileNotFoundError(f"Processed GEBCO bathymetry file not found at: {self.file_path}")
            logger.info("Loading processed GEBCO bathymetry into interface cache", path=str(self.file_path))
            self._ds = xr.open_dataset(self.file_path)
            self._lats = self._ds["lat"].values
            self._lons = self._ds["lon"].values
            self._depth_m = self._ds["depth_m"].values
            self._is_land = self._ds["is_land"].values.astype(bool)

    def close(self):
        """Closes the underlying dataset."""
        if self._ds is not None:
            self._ds.close()
            self._ds = None
            self._lats = None
            self._lons = None
            self._depth_m = None
            self._is_land = None

    def __enter__(self):
        self._ensure_loaded()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _find_nearest_indices(self, lat: float, lon: float) -> Optional[tuple[int, int]]:
        """Finds nearest row and column indices using binary search."""
        self._ensure_loaded()
        if lat < self._lats[0] or lat > self._lats[-1]:
            return None
        if lon < self._lons[0] or lon > self._lons[-1]:
            return None

        # Binary search
        lat_idx = int(np.clip(np.searchsorted(self._lats, lat), 0, len(self._lats) - 1))
        if lat_idx > 0 and abs(self._lats[lat_idx - 1] - lat) < abs(self._lats[lat_idx] - lat):
            lat_idx -= 1

        lon_idx = int(np.clip(np.searchsorted(self._lons, lon), 0, len(self._lons) - 1))
        if lon_idx > 0 and abs(self._lons[lon_idx - 1] - lon) < abs(self._lons[lon_idx] - lon):
            lon_idx -= 1

        return lat_idx, lon_idx

    def get_depth(self, lat: float, lon: float) -> Optional[float]:
        """
        Query seafloor bathymetry depth at a geographic coordinate.

        Returns:
            Positive depth in meters (e.g. 3450.5 m), or None if location
            is Land/Ice or outside dataset coverage.
        """
        indices = self._find_nearest_indices(lat, lon)
        if indices is None:
            return None

        row, col = indices
        if self._is_land[row, col]:
            return None

        val = float(self._depth_m[row, col])
        if np.isnan(val) or val <= 0.0:
            return None

        return round(val, 2)

    def get_depth_point(self, point: GeoPoint) -> Optional[float]:
        """Convenience query taking a domain GeoPoint."""
        return self.get_depth(point.latitude, point.longitude)

    def is_land(self, lat: float, lon: float) -> bool:
        """Checks whether a coordinate is dry land or continental ice."""
        indices = self._find_nearest_indices(lat, lon)
        if indices is None:
            return False
        row, col = indices
        return bool(self._is_land[row, col])

    def get_depth_region(self, bbox: BoundingBox) -> Dict[str, Any]:
        """
        Extracts a 2D bathymetry subregion within the specified bounding box.

        Returns:
            Dict with 'lats', 'lons', 'depth_m', 'is_ocean', 'is_land'.
        """
        self._ensure_loaded()
        min_lat = getattr(bbox, "min_latitude", getattr(bbox, "lat_min", -80.0))
        max_lat = getattr(bbox, "max_latitude", getattr(bbox, "lat_max", -45.0))
        min_lon = getattr(bbox, "min_longitude", getattr(bbox, "lon_min", -180.0))
        max_lon = getattr(bbox, "max_longitude", getattr(bbox, "lon_max", 180.0))

        lat_mask = (self._lats >= min_lat) & (self._lats <= max_lat)
        lon_mask = (self._lons >= min_lon) & (self._lons <= max_lon)

        sub_lats = self._lats[lat_mask]
        sub_lons = self._lons[lon_mask]
        sub_depth = self._depth_m[np.ix_(lat_mask, lon_mask)]
        sub_land = self._is_land[np.ix_(lat_mask, lon_mask)]

        return {
            "lats": sub_lats,
            "lons": sub_lons,
            "depth_m": sub_depth,
            "is_land": sub_land,
            "is_ocean": ~sub_land,
            "shape": sub_depth.shape,
        }

    def check_under_keel_clearance(
        self,
        lat: float,
        lon: float,
        vessel_draft_m: float,
        safety_margin_m: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Evaluates under-keel clearance and navigation grounding hazard
        for a given vessel draft.

        Args:
            lat: Target latitude
            lon: Target longitude
            vessel_draft_m: Vessel maximum draft in meters (positive)
            safety_margin_m: Minimum required safe clearance margin in meters (default 2.0m)

        Returns:
            Dict containing navigability verdict and clearance metrics.
        """
        indices = self._find_nearest_indices(lat, lon)
        if indices is None:
            return {
                "is_navigable": False,
                "water_depth_m": None,
                "clearance_m": None,
                "hazard": BathymetryHazard.OUT_OF_BOUNDS,
                "reason": "Coordinate outside dataset bounds",
            }

        row, col = indices
        if self._is_land[row, col]:
            return {
                "is_navigable": False,
                "water_depth_m": None,
                "clearance_m": None,
                "hazard": BathymetryHazard.LAND,
                "reason": "Location is continental land or ice shelf",
            }

        depth = float(self._depth_m[row, col])
        if np.isnan(depth) or depth <= 0.0:
            return {
                "is_navigable": False,
                "water_depth_m": None,
                "clearance_m": None,
                "hazard": BathymetryHazard.GROUNDING_RISK,
                "reason": "No valid positive water depth",
            }

        clearance = depth - vessel_draft_m
        if clearance <= 0.0:
            hazard = BathymetryHazard.GROUNDING_RISK
            navigable = False
        elif clearance < safety_margin_m:
            hazard = BathymetryHazard.SHALLOW
            navigable = False
        else:
            hazard = BathymetryHazard.SAFE
            navigable = True

        return {
            "is_navigable": navigable,
            "water_depth_m": round(depth, 2),
            "vessel_draft_m": round(vessel_draft_m, 2),
            "clearance_m": round(clearance, 2),
            "safety_margin_m": round(safety_margin_m, 2),
            "hazard": hazard,
        }
