"""
Programmatic Downloader and Regional Subsetter for GEBCO_2026 Bathymetry.
Retrieves the official sub-ice topography/bathymetry dataset via OPeNDAP/HTTP
and extracts the configurable Antarctic domain while preserving raw data untouched.
"""

from pathlib import Path
from typing import Optional, Union, Dict, Any
import time
import xarray as xr
from core.logging import get_logger
from domain.coordinates import BoundingBox

logger = get_logger("data_ingestion.gebco.downloader")

# Official CEDA / BODC THREDDS endpoints for GEBCO_2026 Sub-Ice
CEDA_OPENDAP_SUBICE_URL = (
    "https://dap.ceda.ac.uk/thredds/dodsC/bodc/gebco/global/gebco_2026/"
    "sub_ice_topography_bathymetry/netcdf/GEBCO_2026_sub_ice.nc"
)
CEDA_HTTPSERVER_SUBICE_URL = (
    "https://dap.ceda.ac.uk/thredds/fileServer/bodc/gebco/global/gebco_2026/"
    "sub_ice_topography_bathymetry/netcdf/GEBCO_2026_sub_ice.nc"
)

# Default AMIP POC Antarctic domain: 80°S to 45°S, -180° to +180°
DEFAULT_ANTARCTIC_BBOX = BoundingBox(
    min_latitude=-80.0,
    max_latitude=-45.0,
    min_longitude=-180.0,
    max_longitude=180.0,
)


class GEBCODownloader:
    """
    Downloads and extracts regional subsets of GEBCO 2026 bathymetry.
    Preserves raw downloaded files untouched in data/raw/gebco/gebco_2026/.
    """

    def __init__(
        self,
        raw_data_dir: Optional[Union[str, Path]] = None,
        remote_url: str = CEDA_OPENDAP_SUBICE_URL,
        timeout_seconds: float = 60.0,
    ):
        self.raw_data_dir = Path(raw_data_dir or "data/raw/gebco/gebco_2026")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.remote_url = remote_url
        self.timeout_seconds = timeout_seconds

    def get_default_raw_path(self, filename: str = "GEBCO_2026_sub_ice_antarctic_raw.nc") -> Path:
        """Returns the canonical raw storage path."""
        return self.raw_data_dir / filename

    def download_regional_subset(
        self,
        bbox: Optional[BoundingBox] = None,
        stride: int = 4,
        force_redownload: bool = False,
        output_filename: str = "GEBCO_2026_sub_ice_antarctic_raw.nc",
    ) -> Path:
        """
        Extracts a regional subset from GEBCO_2026 sub-ice bathymetry and saves
        it as an untouched raw NetCDF file.

        Args:
            bbox: BoundingBox defining lat_min, lat_max, lon_min, lon_max.
                  Defaults to 80°S to 45°S, -180° to +180°.
            stride: Coordinate sampling stride (default 4 = ~1 arc-minute resolution,
                    1 = full 15 arc-seconds).
            force_redownload: If True, re-downloads even if the raw file exists.
            output_filename: Name of the raw output file.

        Returns:
            Path to the saved raw NetCDF file.
        """
        output_path = self.raw_data_dir / output_filename
        if output_path.exists() and not force_redownload:
            logger.info("Raw regional GEBCO file already exists, preserving untouched", path=str(output_path))
            return output_path

        bbox = bbox or DEFAULT_ANTARCTIC_BBOX
        min_lat = getattr(bbox, "min_latitude", getattr(bbox, "lat_min", -80.0))
        max_lat = getattr(bbox, "max_latitude", getattr(bbox, "lat_max", -45.0))
        min_lon = getattr(bbox, "min_longitude", getattr(bbox, "lon_min", -180.0))
        max_lon = getattr(bbox, "max_longitude", getattr(bbox, "lon_max", 180.0))

        logger.info(
            "Connecting to GEBCO_2026 remote repository",
            url=self.remote_url,
            bbox=dict(min_lat=min_lat, max_lat=max_lat, min_lon=min_lon, max_lon=max_lon),
            stride=stride,
        )

        t0 = time.time()
        # Open remote OPeNDAP dataset using pydap engine
        ds = xr.open_dataset(self.remote_url, engine="pydap")

        # Slice coordinates: GEBCO lat is -90 to +90, lon is -180 to +180
        lat_slice = slice(min_lat, max_lat)
        lon_slice = slice(min_lon, max_lon)

        logger.info("Extracting regional slice...", lat_slice=str(lat_slice), lon_slice=str(lon_slice))
        if stride > 1:
            elev_var = ds["elevation"][::stride, ::stride]
        else:
            elev_var = ds["elevation"]

        subset = elev_var.sel(lat=lat_slice, lon=lon_slice)

        # Create raw dataset preserving original attributes and structure
        raw_ds = xr.Dataset(
            data_vars={"elevation": subset},
            coords={"lat": subset.lat, "lon": subset.lon},
            attrs={
                **ds.attrs,
                "amip_extraction_bbox": f"[{min_lat}, {max_lat}, {min_lon}, {max_lon}]",
                "amip_extraction_stride": stride,
                "amip_source_url": self.remote_url,
                "amip_extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )

        temp_path = output_path.with_suffix(".tmp.nc")
        logger.info("Writing raw regional NetCDF to disk...", temp_path=str(temp_path))
        raw_ds.to_netcdf(temp_path)
        ds.close()

        if output_path.exists():
            output_path.unlink()
        temp_path.rename(output_path)

        duration = time.time() - t0
        logger.info(
            "Raw regional GEBCO subset successfully extracted and saved",
            output_path=str(output_path),
            duration_s=round(duration, 2),
            size_bytes=output_path.stat().st_size,
        )
        return output_path


def download_gebco(
    bbox: Optional[BoundingBox] = None,
    stride: int = 4,
    raw_data_dir: Optional[Union[str, Path]] = None,
    force_redownload: bool = False,
) -> Path:
    """Convenience function to download/extract GEBCO regional bathymetry."""
    downloader = GEBCODownloader(raw_data_dir=raw_data_dir)
    return downloader.download_regional_subset(
        bbox=bbox,
        stride=stride,
        force_redownload=force_redownload,
    )
