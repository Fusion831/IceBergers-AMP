"""
GEBCO_2026 Bathymetry Data Processor.
Converts raw GEBCO elevation data into canonical AMIP bathymetry representation:
- Applies positive-down vertical convention: depth_m = -elevation for ocean cells.
- Strictly masks land/ice elevation (>= 0) as NaN, preventing false zero-depth shallow water.
- Produces CF-compliant NetCDF and provenance records.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Optional, Union, Dict, Any
import numpy as np
import xarray as xr
from core.logging import get_logger
from domain.provenance import DatasetProvenance

logger = get_logger("data_ingestion.gebco.processor")


class GEBCOProcessor:
    """
    Processes raw GEBCO elevation grids into the canonical AMIP bathymetry format.
    """

    def __init__(
        self,
        raw_data_dir: Optional[Union[str, Path]] = None,
        processed_data_dir: Optional[Union[str, Path]] = None,
    ):
        self.raw_data_dir = Path(raw_data_dir or "data/raw/gebco/gebco_2026")
        self.processed_data_dir = Path(processed_data_dir or "data/processed/gebco/gebco_2026")
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def process_file(
        self,
        raw_nc_path: Union[str, Path],
        output_filename: str = "bathymetry_processed_antarctic.nc",
    ) -> Path:
        """
        Processes a raw GEBCO NetCDF file into the AMIP standard bathymetry format.

        Args:
            raw_nc_path: Path to the raw regional GEBCO NetCDF file.
            output_filename: Name of the resulting processed file.

        Returns:
            Path to the processed NetCDF file.
        """
        raw_path = Path(raw_nc_path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw GEBCO file not found at: {raw_path}")

        logger.info("Opening raw GEBCO NetCDF for processing", path=str(raw_path))
        with xr.open_dataset(raw_path) as ds:
            if "elevation" not in ds.data_vars:
                raise ValueError(f"Required variable 'elevation' not found in {raw_path}. Variables: {list(ds.data_vars)}")

            elevation = ds["elevation"].values  # int16 or float
            lats = ds["lat"].values
            lons = ds["lon"].values

            # AMIP vertical convention transformation:
            # GEBCO native: elevation > 0 is land, elevation < 0 is ocean seafloor.
            # AMIP canonical: depth_m = -elevation for ocean (strictly > 0), NaN for land/ice.
            is_ocean = elevation < 0
            is_land = elevation >= 0

            depth_m = np.where(is_ocean, (-elevation).astype(np.float32), np.nan).astype(np.float32)

            ocean_count = int(np.sum(is_ocean))
            land_count = int(np.sum(is_land))
            total_count = int(elevation.size)

            valid_depths = depth_m[is_ocean]
            min_depth = float(np.min(valid_depths)) if ocean_count > 0 else 0.0
            max_depth = float(np.max(valid_depths)) if ocean_count > 0 else 0.0
            median_depth = float(np.median(valid_depths)) if ocean_count > 0 else 0.0
            mean_depth = float(np.mean(valid_depths)) if ocean_count > 0 else 0.0

            logger.info(
                "Bathymetry processing stats",
                total_cells=total_count,
                ocean_cells=ocean_count,
                land_cells=land_count,
                min_depth_m=round(min_depth, 2),
                max_depth_m=round(max_depth, 2),
                median_depth_m=round(median_depth, 2),
            )

            # Build CF-compliant xarray dataset
            processed_ds = xr.Dataset(
                data_vars={
                    "depth_m": (
                        ["lat", "lon"],
                        depth_m,
                        {
                            "standard_name": "sea_floor_depth_below_sea_surface",
                            "long_name": "Seafloor depth below sea surface (sub-ice)",
                            "units": "m",
                            "positive": "down",
                            "_FillValue": np.nan,
                            "valid_min": np.float32(0.0),
                            "valid_max": np.float32(11000.0),
                        },
                    ),
                    "is_land": (
                        ["lat", "lon"],
                        is_land.astype(bool),
                        {
                            "standard_name": "land_binary_mask",
                            "long_name": "Binary mask for land / ice above sea level",
                            "flag_values": [0, 1],
                            "flag_meanings": "ocean land",
                        },
                    ),
                    "is_ocean": (
                        ["lat", "lon"],
                        is_ocean.astype(bool),
                        {
                            "standard_name": "ocean_binary_mask",
                            "long_name": "Binary mask for ocean / navigable water",
                            "flag_values": [0, 1],
                            "flag_meanings": "land ocean",
                        },
                    ),
                },
                coords={
                    "lat": (
                        ["lat"],
                        lats,
                        {
                            "standard_name": "latitude",
                            "long_name": "latitude",
                            "units": "degrees_north",
                            "axis": "Y",
                        },
                    ),
                    "lon": (
                        ["lon"],
                        lons,
                        {
                            "standard_name": "longitude",
                            "long_name": "longitude",
                            "units": "degrees_east",
                            "axis": "X",
                        },
                    ),
                },
                attrs={
                    "title": "AMIP Canonical Antarctic Bathymetry Layer (GEBCO_2026 Sub-Ice)",
                    "source": "GEBCO_2026 Sub-Ice Topography and Bathymetry Grid",
                    "convention": "AMIP Standard (Depth Positive Down, Land as NaN)",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "total_cells": total_count,
                    "ocean_cells": ocean_count,
                    "land_cells": land_count,
                    "min_depth_m": min_depth,
                    "max_depth_m": max_depth,
                    "mean_depth_m": mean_depth,
                    "median_depth_m": median_depth,
                },
            )

            output_path = self.processed_data_dir / output_filename
            temp_output = output_path.with_suffix(".tmp.nc")
            logger.info("Writing processed bathymetry NetCDF", path=str(output_path))
            processed_ds.to_netcdf(temp_output)
            if output_path.exists():
                output_path.unlink()
            temp_output.rename(output_path)

            # Generate DatasetProvenance record
            prov = DatasetProvenance(
                dataset_id="gebco-2026-sub-ice-antarctic",
                variable_name="depth_m",
                source="GEBCO_2026 / Nippon Foundation - GEBCO Seabed 2030",
                version="2026.1",
                coverage_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
                coverage_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
                uri=str(output_path.as_posix()),
            )

            prov_file = output_path.with_suffix(".provenance.json")
            with open(prov_file, "w", encoding="utf-8") as pf:
                json.dump(
                    {
                        "provenance": prov.model_dump(mode="json"),
                        "raw_source_file": str(raw_path),
                        "statistics": {
                            "ocean_cells": ocean_count,
                            "land_cells": land_count,
                            "min_depth_m": min_depth,
                            "max_depth_m": max_depth,
                            "mean_depth_m": mean_depth,
                            "median_depth_m": median_depth,
                        },
                    },
                    pf,
                    indent=2,
                )
            logger.info("Saved provenance and statistics to JSON", prov_path=str(prov_file))
            return output_path


def process_gebco_file(
    raw_nc_path: Union[str, Path],
    output_filename: str = "bathymetry_processed_antarctic.nc",
    processed_data_dir: Optional[Union[str, Path]] = None,
) -> Path:
    """Convenience function to process a raw GEBCO NetCDF file."""
    processor = GEBCOProcessor(processed_data_dir=processed_data_dir)
    return processor.process_file(raw_nc_path=raw_nc_path, output_filename=output_filename)
