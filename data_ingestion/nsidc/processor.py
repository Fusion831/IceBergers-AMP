"""
NSIDC Sea-Ice Concentration Preprocessor and Georeferenced Dataset Generator.
Cleans raw SIC, handles missing/land masks with scientific integrity,
derives geographic coordinates, and attaches comprehensive provenance metadata.
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union, Dict, Any
import re
import numpy as np
import xarray as xr
from core.logging import get_logger
from data_ingestion.nsidc.coordinates import default_transformer, EPSG_CODE, PROJ4_STRING
from data_ingestion.nsidc.reader import NSIDCReader

logger = get_logger("data_ingestion.nsidc.processor")


class NSIDCProcessor:
    """
    Processes raw G02202 v6 files into clean, validated, georeferenced NetCDF datasets.
    """

    def __init__(
        self,
        processed_data_dir: Optional[Union[str, Path]] = None,
        ancillary_file_path: Optional[Union[str, Path]] = None,
    ):
        self.processed_data_dir = Path(processed_data_dir or "data/processed/nsidc/g02202")
        self.ancillary_file_path = Path(
            ancillary_file_path or "data/raw/nsidc/g02202/ancillary/G02202-ancillary-pss25-v06r00.nc"
        )
        self.transformer = default_transformer

    def process_file(
        self,
        raw_file_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """
        Processes a single raw G02202 NetCDF file into a georeferenced output NetCDF.
        """
        raw_path = Path(raw_file_path)
        if not raw_path.exists():
            raise FileNotFoundError(f"Raw file not found: {raw_path}")

        logger.info("Processing raw NSIDC file", file=str(raw_path))

        with NSIDCReader.open_dataset(raw_path) as ds_raw:
            # 1. Extract raw variables
            raw_sic = ds_raw["cdr_seaice_conc"].values
            if raw_sic.ndim == 3:
                raw_sic = raw_sic[0]  # shape (332, 316)

            x_coords = ds_raw["x"].values
            y_coords = ds_raw["y"].values
            time_coord = ds_raw["time"].values if "time" in ds_raw else [np.datetime64(datetime.now())]
            qa_flags = (
                ds_raw["cdr_seaice_conc_qa_flag"].values[0]
                if "cdr_seaice_conc_qa_flag" in ds_raw
                else np.zeros_like(raw_sic, dtype=np.uint8)
            )

            # 2. Derive geographic coordinates
            if self.ancillary_file_path.exists():
                logger.info("Using official ancillary file for coordinates and surface masks")
                surface_type, lats, lons = NSIDCReader.extract_ancillary_masks(self.ancillary_file_path)
            else:
                logger.info("Generating coordinates from mathematical projection")
                lats, lons = self.transformer.generate_latlon_grid(x_coords, y_coords)
                # If ancillary is missing, classify land as where raw_sic is NaN and lat < -60
                surface_type = np.where(np.isnan(raw_sic), 250, 50).astype(np.uint8)

            # 3. Scientific Normalization of Sea Ice Concentration:
            # Raw G02202 cdr_seaice_conc is fraction in [0.0, 1.0].
            # AMIP application representation is percentage [0.0, 100.0]%.
            # Scientific rules:
            # - Open water is 0.0% (not NaN, not masked)
            # - Valid sea ice is 15.0% to 100.0%
            # - Land (flag 250), Coast (flag 200), and Lake (flag 75) are preserved as NaN in SIC
            # - Any unobserved/missing ocean cells remain NaN
            clean_sic = np.copy(raw_sic)
            clean_sic = clean_sic * 100.0  # Convert 0..1 to 0..100%

            # Explicitly ensure non-ocean features are NaN
            non_ocean_mask = (surface_type == 250) | (surface_type == 200) | (surface_type == 75)
            clean_sic[non_ocean_mask] = np.nan

            # Valid physical range clamp on ocean
            ocean_mask = surface_type == 50
            clean_sic[ocean_mask] = np.clip(clean_sic[ocean_mask], 0.0, 100.0)

            # 4. Determine output path
            if output_path is None:
                # Deterministic naming: sic_processed_YYYYMMDD.nc
                date_match = re.search(r"(\d{8})", raw_path.name)
                date_str = date_match.group(1) if date_match else "unknown"
                year_str = date_str[:4] if date_str != "unknown" else "output"
                out_dir = self.processed_data_dir / year_str
                out_dir.mkdir(parents=True, exist_ok=True)
                output_path = out_dir / f"sic_processed_{date_str}.nc"
            else:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)

            # 5. Build clean, georeferenced xarray Dataset
            ds_out = xr.Dataset(
                data_vars={
                    "sea_ice_concentration": (
                        ("time", "y", "x"),
                        clean_sic[np.newaxis, :, :],
                        {
                            "standard_name": "sea_ice_area_fraction",
                            "long_name": "Antarctic Sea Ice Concentration",
                            "units": "%",
                            "valid_min": 0.0,
                            "valid_max": 100.0,
                            "coverage_content_type": "physicalMeasurement",
                            "grid_mapping": "crs",
                            "flag_meaning_nan": "land, coast, lake, or missing observation",
                        },
                    ),
                    "surface_type": (
                        ("y", "x"),
                        surface_type,
                        {
                            "standard_name": "surface_type_flag",
                            "long_name": "Surface Classification Mask",
                            "flag_values": [50, 75, 200, 250],
                            "flag_meanings": "ocean lake coast land",
                            "grid_mapping": "crs",
                        },
                    ),
                    "qa_flags": (
                        ("time", "y", "x"),
                        qa_flags[np.newaxis, :, :],
                        {
                            "standard_name": "status_flag",
                            "long_name": "CDR Quality Assurance Flags",
                            "grid_mapping": "crs",
                        },
                    ),
                    "latitude": (
                        ("y", "x"),
                        lats,
                        {
                            "standard_name": "latitude",
                            "long_name": "Geographic Latitude",
                            "units": "degrees_north",
                            "valid_min": -90.0,
                            "valid_max": -39.0,
                        },
                    ),
                    "longitude": (
                        ("y", "x"),
                        lons,
                        {
                            "standard_name": "longitude",
                            "long_name": "Geographic Longitude",
                            "units": "degrees_east",
                            "valid_min": -180.0,
                            "valid_max": 180.0,
                        },
                    ),
                    "crs": (
                        (),
                        np.int32(EPSG_CODE),
                        {
                            "grid_mapping_name": "polar_stereographic",
                            "epsg_code": EPSG_CODE,
                            "proj4text": PROJ4_STRING,
                            "standard_parallel": -70.0,
                            "latitude_of_projection_origin": -90.0,
                            "straight_vertical_longitude_from_pole": 0.0,
                            "semi_major_axis": 6378273.0,
                            "inverse_flattening": 298.279411123064,
                        },
                    ),
                },
                coords={
                    "time": (("time",), time_coord),
                    "y": (("y",), y_coords, {"units": "meters", "axis": "Y"}),
                    "x": (("x",), x_coords, {"units": "meters", "axis": "X"}),
                },
                attrs={
                    "Conventions": "CF-1.11, ACDD-1.3",
                    "title": "AMIP Processed Antarctic Sea Ice Concentration",
                    "institution": "AMIP - Antarctic Mission Intelligence Platform",
                    "source_dataset": "NOAA/NSIDC G02202 v6 CDR",
                    "source_file": raw_path.name,
                    "source_doi": "https://doi.org/10.7265/b18j-z797",
                    "spatial_resolution": "25km",
                    "spatial_crs": "EPSG:3412",
                    "processing_software": "AMIP Data Ingestion Pipeline (nsidc.processor)",
                    "processing_timestamp": datetime.now(timezone.utc).isoformat(),
                    "geospatial_lat_min": float(np.min(lats)),
                    "geospatial_lat_max": float(np.max(lats)),
                    "geospatial_lon_min": float(np.min(lons)),
                    "geospatial_lon_max": float(np.max(lons)),
                },
            )

            # 6. Save to NetCDF
            ds_out.to_netcdf(output_path, format="NETCDF4")
            logger.info("Processed dataset saved successfully", path=str(output_path))
            return output_path


def process_nsidc_file(
    raw_file_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    ancillary_file_path: Optional[Union[str, Path]] = None,
) -> Path:
    """Convenience function for processing an NSIDC file."""
    processor = NSIDCProcessor(ancillary_file_path=ancillary_file_path)
    return processor.process_file(raw_file_path, output_path=output_path)
