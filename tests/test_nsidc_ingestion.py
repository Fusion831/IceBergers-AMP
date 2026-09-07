"""
Automated Test Suite for NSIDC Antarctic Sea-Ice Concentration Ingestion Pipeline.
"""

from datetime import date, datetime
from pathlib import Path
import numpy as np
import pytest
import xarray as xr

from data_ingestion.nsidc.downloader import NSIDCDownloader, get_default_sensor_for_year
from data_ingestion.nsidc.coordinates import NSIDCCoordinateTransformer, GRID_SPACING_M
from data_ingestion.nsidc.reader import NSIDCReader
from data_ingestion.nsidc.processor import NSIDCProcessor
from data_ingestion.nsidc.validator import NSIDCValidator
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface
from domain.coordinates import BoundingBox


class TestNSIDCCoordinates:
    """Tests for NSIDC Polar Stereographic South (EPSG:3412) transformations."""

    def test_south_pole_transformation(self):
        transformer = NSIDCCoordinateTransformer()
        # Origin (0, 0) in meters is South Pole (-90 deg lat)
        lon, lat = transformer.xy_to_lonlat(np.array([0.0]), np.array([0.0]))
        assert np.isclose(lat[0], -90.0, atol=1e-4)

    def test_roundtrip_transformation(self):
        transformer = NSIDCCoordinateTransformer()
        test_lats = np.array([-65.0, -70.0, -75.0, -80.0])
        test_lons = np.array([0.0, 45.0, -90.0, 120.0])

        for lat, lon in zip(test_lats, test_lons):
            x, y = transformer.lonlat_to_xy(lon, lat)
            calc_lon, calc_lat = transformer.xy_to_lonlat(np.array([x]), np.array([y]))
            assert np.isclose(calc_lat[0], lat, atol=1e-4)
            assert np.isclose(calc_lon[0], lon, atol=1e-4)

    def test_find_nearest_index(self):
        transformer = NSIDCCoordinateTransformer()
        x_coords = np.linspace(-3937500.0, 3937500.0, 316)
        y_coords = np.linspace(4337500.0, -3937500.0, 332)

        # South Pole is at ~ index (173, 157)
        row, col = transformer.find_nearest_index(-90.0, 0.0, x_coords, y_coords)
        assert 170 <= row <= 176
        assert 155 <= col <= 160


class TestNSIDCDownloader:
    """Tests for NSIDC HTTPS Downloader."""

    def test_url_construction(self):
        downloader = NSIDCDownloader()
        anc_url = downloader.get_ancillary_url()
        assert "G02202_V6/ancillary/G02202-ancillary-pss25-v06r00.nc" in anc_url

        daily_url = downloader.get_daily_url(date(2024, 1, 1))
        assert "G02202_V6/south/daily/2024/sic_pss25_20240101_F17_v06r00.nc" in daily_url

    def test_sensor_selection_by_epoch(self):
        assert get_default_sensor_for_year(2024) == "F17"
        assert get_default_sensor_for_year(2000) == "F13"
        assert get_default_sensor_for_year(1980) == "N07"

    def test_invalid_url_fails_cleanly(self, tmp_path):
        downloader = NSIDCDownloader(max_retries=1, timeout_seconds=5.0)
        invalid_url = "https://noaadata.apps.nsidc.org/NOAA/G02202_V6/non_existent_file.nc"
        dest = tmp_path / "never_created.nc"

        with pytest.raises(Exception):
            downloader.download_file(invalid_url, dest)
        assert not dest.exists()


class TestNSIDCProcessingAndValidation:
    """Tests for reading, processing, validating, and querying G02202 datasets."""

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Creates or locates real sample files for deterministic testing."""
        # Use existing downloaded raw file if available, or create mock dataset
        raw_dir = Path("data/raw/nsidc/g02202/2024")
        anc_path = Path("data/raw/nsidc/g02202/ancillary/G02202-ancillary-pss25-v06r00.nc")

        raw_files = list(raw_dir.glob("*.nc")) if raw_dir.exists() else []
        if raw_files and anc_path.exists():
            return raw_files[0], anc_path

        # Otherwise synthesize a valid NetCDF fixture with real dimensions
        mock_raw = tmp_path / "sic_pss25_20240101_mock_v06r00.nc"
        mock_anc = tmp_path / "mock_ancillary.nc"

        x = np.linspace(-3937500.0, 3937500.0, 316)
        y = np.linspace(4337500.0, -3937500.0, 332)
        xx, yy = np.meshgrid(x, y)

        transformer = NSIDCCoordinateTransformer()
        lons, lats = transformer.xy_to_lonlat(xx, yy)

        # 50 = ocean, 250 = land (center south pole)
        dist = np.sqrt(xx**2 + yy**2)
        surface_type = np.where(dist < 1500000.0, 250, 50).astype(np.uint8)

        # Raw SIC: 0.0 to 1.0 on ocean, NaN on land
        raw_sic = np.where(surface_type == 50, 0.45, np.nan)
        raw_sic = raw_sic[np.newaxis, :, :]

        ds_raw = xr.Dataset(
            data_vars={
                "cdr_seaice_conc": (("time", "y", "x"), raw_sic),
                "cdr_seaice_conc_qa_flag": (("time", "y", "x"), np.zeros_like(raw_sic, dtype=np.uint8)),
                "crs": ((), 3412),
            },
            coords={
                "time": (("time",), [np.datetime64("2024-01-01T00:00:00")]),
                "y": (("y",), y),
                "x": (("x",), x),
            },
        )
        ds_raw.to_netcdf(mock_raw)

        ds_anc = xr.Dataset(
            data_vars={
                "surface_type": (("y", "x"), surface_type),
                "latitude": (("y", "x"), lats),
                "longitude": (("y", "x"), lons),
            },
            coords={"y": (("y",), y), "x": (("x",), x)},
        )
        ds_anc.to_netcdf(mock_anc)

        return mock_raw, mock_anc

    def test_processor_generates_georeferenced_dataset(self, sample_files, tmp_path):
        raw_file, anc_file = sample_files
        out_processed = tmp_path / "processed_output.nc"

        processor = NSIDCProcessor(
            processed_data_dir=tmp_path,
            ancillary_file_path=anc_file,
        )
        saved_path = processor.process_file(raw_file, output_path=out_processed)

        assert saved_path.exists()
        assert saved_path.stat().st_size > 0

        # Verify raw input was untouched
        assert raw_file.exists()

        # Check processed dataset contents
        with xr.open_dataset(saved_path) as ds:
            assert "sea_ice_concentration" in ds
            assert "surface_type" in ds
            assert "latitude" in ds
            assert "longitude" in ds
            assert "crs" in ds

            # Provenance
            assert ds.attrs["spatial_crs"] == "EPSG:3412"
            assert "processing_timestamp" in ds.attrs

            # Values check
            sic = ds["sea_ice_concentration"].values[0]
            st = ds["surface_type"].values

            # Ocean values are percentage [0, 100]
            ocean_vals = sic[st == 50]
            assert not np.isnan(ocean_vals).any()
            assert np.min(ocean_vals) >= 0.0
            assert np.max(ocean_vals) <= 100.0

            # Land values are NaN
            land_vals = sic[st == 250]
            assert np.isnan(land_vals).all()

    def test_validator_and_plot(self, sample_files, tmp_path):
        raw_file, anc_file = sample_files
        processor = NSIDCProcessor(processed_data_dir=tmp_path, ancillary_file_path=anc_file)
        processed_file = processor.process_file(raw_file, output_path=tmp_path / "test_proc.nc")

        report = NSIDCValidator.validate_dataset(processed_file)
        assert report["checks_passed"] is True

        plot_path = tmp_path / "validation_plot.png"
        generated_plot = NSIDCValidator.generate_validation_plot(processed_file, plot_path)
        assert generated_plot.exists()
        assert generated_plot.stat().st_size > 1000

    def test_query_interface(self, sample_files, tmp_path):
        raw_file, anc_file = sample_files
        proc_dir = tmp_path / "processed"
        processor = NSIDCProcessor(processed_data_dir=proc_dir, ancillary_file_path=anc_file)
        processed_file = proc_dir / "sic_processed_20240101.nc"
        processor.process_file(raw_file, output_path=processed_file)

        interface = NSIDCSeaIceInterface(processed_data_dir=proc_dir)

        # 1. Point query over open Southern Ocean (should return numeric SIC)
        sic_ocean = interface.get_sic(-55.0, 20.0, date(2024, 1, 1))
        assert sic_ocean is not None
        assert 0.0 <= sic_ocean <= 100.0

        # 2. Point query over deep Antarctic continent (should return None / Land)
        sic_land = interface.get_sic(-85.0, 0.0, date(2024, 1, 1))
        assert sic_land is None

        # 3. Region query
        bbox = BoundingBox(
            min_latitude=-70.0,
            max_latitude=-60.0,
            min_longitude=10.0,
            max_longitude=30.0,
        )
        region = interface.get_sic_region(bbox, date(2024, 1, 1))
        assert "sic" in region
        assert len(region["sic"]) > 0

        interface.close()
