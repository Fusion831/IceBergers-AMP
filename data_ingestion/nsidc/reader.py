"""
Reader and metadata extractor for NOAA@NSIDC G02202 v6 Sea-Ice Concentration files.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union
import xarray as xr
import numpy as np
from core.logging import get_logger

logger = get_logger("data_ingestion.nsidc.reader")


class NSIDCReader:
    """
    Reads and inspects raw NetCDF-4 G02202 v6 files.
    """

    @staticmethod
    def open_dataset(file_path: Union[str, Path]) -> xr.Dataset:
        """Opens a NetCDF dataset using xarray."""
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"G02202 file not found: {p}")
        if p.stat().st_size == 0:
            raise ValueError(f"G02202 file is empty (0 bytes): {p}")

        return xr.open_dataset(p, engine="netcdf4")

    @classmethod
    def inspect_metadata(cls, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Inspects all metadata, dimensions, coordinate variables, CRS, and attributes.
        Returns a structured dictionary report.
        """
        with cls.open_dataset(file_path) as ds:
            metadata = {
                "file_path": str(file_path),
                "file_size_bytes": Path(file_path).stat().st_size,
                "dimensions": {dim: size for dim, size in ds.sizes.items()},
                "data_variables": {},
                "coordinate_variables": {},
                "global_attributes": dict(ds.attrs),
                "crs_info": {},
            }

            # Inspect data variables
            for vname, var in ds.data_vars.items():
                metadata["data_variables"][vname] = {
                    "shape": list(var.shape),
                    "dtype": str(var.dtype),
                    "attributes": dict(var.attrs),
                }

            # Inspect coordinates
            for cname, coord in ds.coords.items():
                metadata["coordinate_variables"][cname] = {
                    "shape": list(coord.shape),
                    "dtype": str(coord.dtype),
                    "attributes": dict(coord.attrs),
                }

            # Inspect CRS
            if "crs" in ds:
                metadata["crs_info"] = dict(ds["crs"].attrs)

            return metadata

    @classmethod
    def extract_raw_sic(
        cls, file_path: Union[str, Path]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts raw SIC array, x coordinates, y coordinates, and time timestamp.
        Returns:
            Tuple of (sic_2d, x_1d, y_1d, timestamp)
        """
        with cls.open_dataset(file_path) as ds:
            if "cdr_seaice_conc" not in ds:
                raise KeyError(f"Expected variable 'cdr_seaice_conc' not found in {file_path}")

            sic = ds["cdr_seaice_conc"].values
            # Squeeze time dimension if present: shape (1, 332, 316) -> (332, 316)
            if sic.ndim == 3:
                sic = sic[0]

            x = ds["x"].values
            y = ds["y"].values
            time_val = ds["time"].values[0] if "time" in ds else None

            return sic, x, y, time_val

    @classmethod
    def extract_ancillary_masks(
        cls, ancillary_path: Union[str, Path]
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Extracts official surface_type, latitude, and longitude from ancillary file.
        Returns:
            Tuple of (surface_type, latitude, longitude) 2D arrays.
        """
        with cls.open_dataset(ancillary_path) as ds:
            surface_type = ds["surface_type"].values
            lat = ds["latitude"].values
            lon = ds["longitude"].values
            return surface_type, lat, lon
