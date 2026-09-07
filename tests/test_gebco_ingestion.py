"""
Unit and Integration Tests for GEBCO_2026 Bathymetry Ingestion Subsystem.
Tests:
- Downloader bounding box handling and data preservation.
- Processor vertical convention (negative elevation -> positive depth, land -> NaN).
- Validator strict data contracts (positive depth, physical limits, land masking).
- Interface point queries, regional bounding box queries, and under-keel clearance.
"""

from pathlib import Path
import numpy as np
import pytest
import xarray as xr
from domain.coordinates import GeoPoint, BoundingBox
from data_ingestion.gebco.processor import GEBCOProcessor
from data_ingestion.gebco.validator import GEBCOValidator
from data_ingestion.gebco.interface import GEBCOBathymetryInterface, BathymetryHazard


@pytest.fixture
def sample_raw_nc(tmp_path: Path) -> Path:
    """Creates a synthetic raw GEBCO NetCDF for fast unit testing."""
    lats = np.array([-70.0, -69.0, -68.0], dtype=np.float64)
    lons = np.array([0.0, 1.0, 2.0], dtype=np.float64)

    # Elevation:
    # row 0: ocean deep (-4000), ocean shelf (-200), ocean trench (-5500)
    # row 1: ocean shallow (-15), coast (0), land (+50)
    # row 2: land mountain (+1500), land (+800), land (+250)
    elevation = np.array(
        [
            [-4000, -200, -5500],
            [-15, 0, 50],
            [1500, 800, 250],
        ],
        dtype=np.int16,
    )

    ds = xr.Dataset(
        data_vars={"elevation": (["lat", "lon"], elevation)},
        coords={"lat": lats, "lon": lons},
        attrs={"title": "Synthetic GEBCO Raw Test Grid"},
    )
    raw_path = tmp_path / "test_raw_gebco.nc"
    ds.to_netcdf(raw_path)
    return raw_path


def test_processor_vertical_convention(sample_raw_nc: Path, tmp_path: Path):
    """Verifies that elevation < 0 becomes positive depth and elevation >= 0 becomes NaN."""
    proc_dir = tmp_path / "processed"
    processor = GEBCOProcessor(processed_data_dir=proc_dir)
    proc_file = processor.process_file(sample_raw_nc, output_filename="bathymetry_test.nc")

    assert proc_file.exists()
    with xr.open_dataset(proc_file) as ds:
        depth = ds["depth_m"].values
        is_land = ds["is_land"].values
        is_ocean = ds["is_ocean"].values

        # Deep ocean cell (-4000 elevation -> 4000.0m depth)
        assert depth[0, 0] == 4000.0
        assert is_ocean[0, 0] is np.True_ or is_ocean[0, 0] == 1
        assert is_land[0, 0] is np.False_ or is_land[0, 0] == 0

        # Shelf cell (-200 -> 200.0m depth)
        assert depth[0, 1] == 200.0

        # Shallow ocean cell (-15 -> 15.0m depth)
        assert depth[1, 0] == 15.0

        # Sea level / coastline (0 elevation -> NaN depth, marked as land)
        assert np.isnan(depth[1, 1])
        assert is_land[1, 1] is np.True_ or is_land[1, 1] == 1

        # Mountain cell (+1500 elevation -> NaN depth, marked as land)
        assert np.isnan(depth[2, 0])
        assert is_land[2, 0] is np.True_ or is_land[2, 0] == 1


def test_validator_passes_valid_dataset(sample_raw_nc: Path, tmp_path: Path):
    """Verifies that correctly processed data passes all validator checks."""
    processor = GEBCOProcessor(processed_data_dir=tmp_path / "processed")
    proc_file = processor.process_file(sample_raw_nc, output_filename="bathymetry_valid.nc")

    validator = GEBCOValidator(report_dir=tmp_path / "reports")
    report = validator.validate(proc_file)

    assert report["passed"] is True
    assert len(report["errors"]) == 0
    assert report["metrics"]["depth_stats"]["min_m"] == 15.0
    assert report["metrics"]["depth_stats"]["max_m"] == 5500.0


def test_validator_rejects_negative_depth(tmp_path: Path):
    """Verifies that the validator catches illegal non-positive ocean depths."""
    lats = np.array([-70.0, -69.0])
    lons = np.array([0.0, 1.0])
    # Buggy depth: negative depth value (-100m)
    depth = np.array([[-100.0, 200.0], [500.0, 1000.0]], dtype=np.float32)
    is_ocean = np.ones((2, 2), dtype=bool)
    is_land = np.zeros((2, 2), dtype=bool)

    ds = xr.Dataset(
        data_vars={
            "depth_m": (["lat", "lon"], depth),
            "is_land": (["lat", "lon"], is_land),
            "is_ocean": (["lat", "lon"], is_ocean),
        },
        coords={"lat": lats, "lon": lons},
    )
    bad_file = tmp_path / "bad_depth.nc"
    ds.to_netcdf(bad_file)

    validator = GEBCOValidator(report_dir=tmp_path / "reports")
    report = validator.validate(bad_file)

    assert report["passed"] is False
    assert any("non-positive" in err for err in report["errors"])


def test_validator_rejects_non_nan_land(tmp_path: Path):
    """Verifies that the validator catches land cells that failed to be masked to NaN."""
    lats = np.array([-70.0, -69.0])
    lons = np.array([0.0, 1.0])
    depth = np.array([[100.0, 0.0], [500.0, 1000.0]], dtype=np.float32)
    is_ocean = np.array([[True, False], [True, True]], dtype=bool)
    is_land = np.array([[False, True], [False, False]], dtype=bool)

    ds = xr.Dataset(
        data_vars={
            "depth_m": (["lat", "lon"], depth),
            "is_land": (["lat", "lon"], is_land),
            "is_ocean": (["lat", "lon"], is_ocean),
        },
        coords={"lat": lats, "lon": lons},
    )
    bad_file = tmp_path / "bad_land.nc"
    ds.to_netcdf(bad_file)

    validator = GEBCOValidator(report_dir=tmp_path / "reports")
    report = validator.validate(bad_file)

    assert report["passed"] is False
    assert any("non-NaN depth values on land" in err for err in report["errors"])


def test_interface_queries_and_clearance(sample_raw_nc: Path, tmp_path: Path):
    """Verifies point queries, bounding box regional queries, and under-keel clearance."""
    processor = GEBCOProcessor(processed_data_dir=tmp_path / "processed")
    proc_file = processor.process_file(sample_raw_nc, output_filename="bathymetry_interface.nc")

    interface = GEBCOBathymetryInterface(processed_file_path=proc_file)

    # 1. Point queries
    # Ocean point: (-70.0, 0.0) -> 4000.0m
    depth_ocean = interface.get_depth(lat=-70.0, lon=0.0)
    assert depth_ocean == 4000.0

    # GeoPoint query
    point = GeoPoint(latitude=-70.0, longitude=0.0)
    assert interface.get_depth_point(point) == 4000.0

    # Land point: (-68.0, 0.0) -> +1500m elevation -> None
    depth_land = interface.get_depth(lat=-68.0, lon=0.0)
    assert depth_land is None
    assert interface.is_land(lat=-68.0, lon=0.0) is True

    # Out of bounds point -> None
    assert interface.get_depth(lat=-20.0, lon=0.0) is None

    # 2. Under-keel clearance checks
    # Safe deep water: vessel draft 10.0m, water depth 4000.0m -> clearance 3990.0m, SAFE
    chk_safe = interface.check_under_keel_clearance(lat=-70.0, lon=0.0, vessel_draft_m=10.0)
    assert chk_safe["is_navigable"] is True
    assert chk_safe["hazard"] == BathymetryHazard.SAFE
    assert chk_safe["clearance_m"] == 3990.0

    # Shallow water: depth 15.0m, vessel draft 14.0m, safety margin 2.0m -> clearance 1.0m < 2.0m -> SHALLOW
    chk_shallow = interface.check_under_keel_clearance(
        lat=-69.0, lon=0.0, vessel_draft_m=14.0, safety_margin_m=2.0
    )
    assert chk_shallow["is_navigable"] is False
    assert chk_shallow["hazard"] == BathymetryHazard.SHALLOW
    assert chk_shallow["clearance_m"] == 1.0

    # Grounding risk: depth 15.0m, vessel draft 18.0m -> clearance -3.0m <= 0 -> GROUNDING_RISK
    chk_ground = interface.check_under_keel_clearance(lat=-69.0, lon=0.0, vessel_draft_m=18.0)
    assert chk_ground["is_navigable"] is False
    assert chk_ground["hazard"] == BathymetryHazard.GROUNDING_RISK

    # Land clearance check -> LAND
    chk_land = interface.check_under_keel_clearance(lat=-68.0, lon=0.0, vessel_draft_m=10.0)
    assert chk_land["is_navigable"] is False
    assert chk_land["hazard"] == BathymetryHazard.LAND

    # 3. Regional bbox query
    bbox = BoundingBox(min_latitude=-70.5, max_latitude=-68.5, min_longitude=-0.5, max_longitude=1.5)
    region = interface.get_depth_region(bbox)
    assert region["shape"] == (2, 2)
    assert len(region["lats"]) == 2
    assert len(region["lons"]) == 2

    interface.close()


def test_real_processed_antarctic_dataset():
    """Integration test checking queries against the real processed regional Antarctic dataset."""
    proc_file = Path("data/processed/gebco/gebco_2026/bathymetry_processed_antarctic.nc")
    if not proc_file.exists():
        pytest.skip("Processed regional Antarctic dataset not found on disk")

    interface = GEBCOBathymetryInterface(processed_file_path=proc_file)

    # 1. Test Drake Passage deep Southern Ocean point (~58°S, 65°W)
    drake_depth = interface.get_depth(lat=-58.0, lon=-65.0)
    assert drake_depth is not None
    assert drake_depth > 1000.0  # Deep ocean trench/basin

    # 2. Test continental interior Antarctic highland point (~75.4°S, 8.44°E) -> continental mountain above sea level
    interior_depth = interface.get_depth(lat=-75.40, lon=8.44)
    # Highland bedrock elevation is above sea level (> 0), so depth is None and is_land is True
    assert interior_depth is None
    assert interface.is_land(lat=-75.40, lon=8.44) is True

    # 3. Test under-keel clearance in deep water
    clearance = interface.check_under_keel_clearance(lat=-58.0, lon=-65.0, vessel_draft_m=11.5)
    assert clearance["is_navigable"] is True
    assert clearance["hazard"] == BathymetryHazard.SAFE

    # 4. Regional bounding box query in Weddell Sea (-72 to -70°S, -45 to -40°W)
    weddell_bbox = BoundingBox(
        min_latitude=-72.0, max_latitude=-70.0, min_longitude=-45.0, max_longitude=-40.0
    )
    region = interface.get_depth_region(weddell_bbox)
    assert region["shape"][0] > 0
    assert region["shape"][1] > 0
    assert "depth_m" in region

    interface.close()

