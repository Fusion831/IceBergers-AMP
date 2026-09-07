"""
Application-level query interface for the NSIDC Sea Ice Concentration dataset.
Decouples AMIP consumers from raw NetCDF file details.
"""

from datetime import datetime, date
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
import numpy as np
import xarray as xr
from domain.coordinates import GeoPoint, BoundingBox
from core.logging import get_logger
from data_ingestion.nsidc.coordinates import default_transformer

logger = get_logger("data_ingestion.nsidc.interface")


class NSIDCSeaIceInterface:
    """
    AMIP Query interface for processed NSIDC Sea Ice Concentration data.
    Provides fast O(1) point queries and regional bounding box queries.
    """

    def __init__(self, processed_data_dir: Optional[Union[str, Path]] = None):
        self.processed_data_dir = Path(processed_data_dir or "data/processed/nsidc/g02202")
        self.transformer = default_transformer
        self._cached_ds: Optional[xr.Dataset] = None
        self._cached_path: Optional[Path] = None

    def _get_file_for_date(self, target_date: Union[date, datetime]) -> Optional[Path]:
        """Finds the processed NetCDF file corresponding to a target date."""
        d = target_date.date() if isinstance(target_date, datetime) else target_date
        date_str = d.strftime("%Y%m%d")
        candidate = self.processed_data_dir / str(d.year) / f"sic_processed_{date_str}.nc"
        if candidate.exists():
            return candidate

        # Fallback: search any file in processed_data_dir matching date_str
        matches = list(self.processed_data_dir.glob(f"**/sic_processed_{date_str}.nc"))
        if matches:
            return matches[0]

        return None

    def _load_dataset(self, file_path: Path) -> xr.Dataset:
        """Loads dataset with caching for fast consecutive queries."""
        if self._cached_path != file_path or self._cached_ds is None:
            if self._cached_ds is not None:
                self._cached_ds.close()
            self._cached_ds = xr.open_dataset(file_path)
            self._cached_path = file_path
        return self._cached_ds

    def get_sic(
        self,
        lat: float,
        lon: float,
        timestamp: Union[datetime, date],
    ) -> Optional[float]:
        """
        Query sea ice concentration (%) at a specific geographic point and timestamp.
        Returns:
            SIC in percent [0.0, 100.0]%, or None if location is Land/Coast or outside dataset.
        """
        file_path = self._get_file_for_date(timestamp)
        if not file_path:
            logger.warning("No processed NSIDC file found for date", date=str(timestamp))
            return None

        ds = self._load_dataset(file_path)
        x_coords = ds["x"].values
        y_coords = ds["y"].values

        row, col = self.transformer.find_nearest_index(lat, lon, x_coords, y_coords)
        sic_val = float(ds["sea_ice_concentration"].values[0, row, col])
        st_val = int(ds["surface_type"].values[row, col])

        # If NaN or land, return None for navigability
        if np.isnan(sic_val) or st_val in [250, 200, 75]:
            return None

        return round(sic_val, 2)

    def get_sic_point(self, point: GeoPoint, timestamp: datetime) -> Optional[float]:
        """Convenience query taking a GeoPoint."""
        return self.get_sic(point.latitude, point.longitude, timestamp)

    def get_sic_region(
        self,
        bbox: BoundingBox,
        timestamp: Union[datetime, date],
    ) -> Dict[str, Any]:
        """
        Retrieve a 2D spatial region of SIC within a bounding box.
        Returns:
            Dictionary with 'lats', 'lons', 'sic', and 'mask'.
        """
        file_path = self._get_file_for_date(timestamp)
        if not file_path:
            raise FileNotFoundError(f"No processed NSIDC file found for {timestamp}")

        ds = self._load_dataset(file_path)
        lats = ds["latitude"].values
        lons = ds["longitude"].values
        sic = ds["sea_ice_concentration"].values[0]
        st = ds["surface_type"].values

        # Geographic bounding box mask
        in_bbox = (
            (lats >= bbox.min_latitude)
            & (lats <= bbox.max_latitude)
            & (lons >= bbox.min_longitude)
            & (lons <= bbox.max_longitude)
        )

        return {
            "timestamp": str(timestamp),
            "bbox": bbox.model_dump(),
            "lats": lats[in_bbox],
            "lons": lons[in_bbox],
            "sic": sic[in_bbox],
            "is_land": (st[in_bbox] == 250) | (st[in_bbox] == 200),
        }

    def close(self):
        if self._cached_ds is not None:
            self._cached_ds.close()
            self._cached_ds = None
            self._cached_path = None
