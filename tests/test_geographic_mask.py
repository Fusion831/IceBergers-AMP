"""
Unit tests for Antarctic Geographic Mask (SCAR ADD v7.12).
Runs entirely offline with synthetic local geometric fixtures.
Verifies spatial queries, class distinctions, H3 aggregation, CRS handling,
boundary semantics, coverage limits, and provenance generation.
"""

import json
import pytest
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point, MultiPolygon
from shapely import box
import pyproj
import h3

from data_ingestion.geographic_mask.metadata import (
    SurfaceType,
    CoverageStatus,
    ADDDatasetMetadata,
)
from data_ingestion.geographic_mask.downloader import ADDDownloader
from data_ingestion.geographic_mask.validator import ADDGeometryValidator
from data_ingestion.geographic_mask.interface import AntarcticGeographicMask
from data_ingestion.geographic_mask.h3_mask import H3GeographicMaskAggregator


@pytest.fixture
def synthetic_add_geodataframe():
    """
    Creates a synthetic GeoDataFrame in EPSG:3031 representing:
    - Continental land polygon
    - Ice shelf polygon
    - Ice tongue polygon
    - Rumple polygon
    """
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:3031", always_xy=True)

    def make_poly_from_latlon(min_lat, max_lat, min_lon, max_lon):
        lons = [min_lon, max_lon, max_lon, min_lon, min_lon]
        lats = [min_lat, min_lat, max_lat, max_lat, min_lat]
        xs, ys = transformer.transform(lons, lats)
        return Polygon(zip(xs, ys))

    # Features placed between 70°S and 80°S
    land_poly = make_poly_from_latlon(-75.0, -70.0, -10.0, 0.0)
    shelf_poly = make_poly_from_latlon(-75.0, -70.0, 5.0, 15.0)
    tongue_poly = make_poly_from_latlon(-75.0, -70.0, 20.0, 25.0)
    rumple_poly = make_poly_from_latlon(-75.0, -70.0, 30.0, 35.0)

    gdf = gpd.GeoDataFrame(
        {
            "surface": ["land", "ice shelf", "ice tongue", "rumple"],
            "geometry": [land_poly, shelf_poly, tongue_poly, rumple_poly],
        },
        crs="EPSG:3031",
    )
    return gdf


@pytest.fixture
def geographic_mask(synthetic_add_geodataframe):
    return AntarcticGeographicMask(source=synthetic_add_geodataframe, coverage_limit_lat=-60.0)


# ====================================================================
# 1. Point Spatial Queries & Surface Classifications
# ====================================================================

def test_known_land_point(geographic_mask):
    # -72.5°S, -5.0°E is strictly inside the land polygon
    res = geographic_mask.query(-72.5, -5.0)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.LAND
    assert res.is_land is True
    assert res.is_ice_shelf is False
    assert res.is_ice_tongue is False
    assert res.is_rumple is False
    assert res.is_geographically_excluded is True
    assert res.is_geographically_allowed is False


def test_known_ice_shelf_point(geographic_mask):
    # -72.5°S, 10.0°E is inside the ice shelf polygon
    res = geographic_mask.query(-72.5, 10.0)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.ICE_SHELF
    assert res.is_land is False
    assert res.is_ice_shelf is True
    assert res.is_ice_tongue is False
    assert res.is_rumple is False
    assert res.is_geographically_excluded is True
    assert res.is_geographically_allowed is False


def test_known_ice_tongue_point(geographic_mask):
    # -72.5°S, 22.5°E is inside the ice tongue polygon
    res = geographic_mask.query(-72.5, 22.5)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.ICE_TONGUE
    assert res.is_ice_tongue is True
    assert res.is_geographically_excluded is True
    assert res.is_geographically_allowed is False


def test_known_rumple_point(geographic_mask):
    # -72.5°S, 32.5°E is inside the rumple polygon
    res = geographic_mask.query(-72.5, 32.5)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.RUMPLE
    assert res.is_rumple is True
    assert res.is_geographically_excluded is True
    assert res.is_geographically_allowed is False


def test_known_open_ocean_point(geographic_mask):
    # -65.0°S, 0.0°E is south of 60°S (inside ADD domain) but not inside any land or ice shelf
    res = geographic_mask.query(-65.0, 0.0)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.OCEAN
    assert res.is_land is False
    assert res.is_ice_shelf is False
    assert res.is_geographically_excluded is False
    assert res.is_geographically_allowed is True


# ====================================================================
# 2. Domain Boundaries & Outside-Coverage Behavior
# ====================================================================

def test_outside_coverage_north_of_60s(geographic_mask):
    # -55.0°S is north of 60°S (outside SCAR ADD coverage)
    res = geographic_mask.query(-55.0, 0.0)
    assert res.coverage_status == CoverageStatus.OUTSIDE_COVERAGE
    assert res.surface == SurfaceType.UNKNOWN
    assert res.is_geographically_allowed is False
    assert res.is_geographically_excluded is False
    assert geographic_mask.coverage_status(-55.0, 0.0) == CoverageStatus.OUTSIDE_COVERAGE


def test_coverage_boundary_exact_60s(geographic_mask):
    # Exactly -60.0°S is the coverage limit (inside ADD coverage)
    res = geographic_mask.query(-60.0, 0.0)
    assert res.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert res.surface == SurfaceType.OCEAN


def test_point_on_polygon_boundary_semantics(geographic_mask):
    # Take an exact point on the exterior boundary of the land polygon
    land_geom = geographic_mask.geometries[0]
    boundary_pt = land_geom.exterior.interpolate(0.25, normalized=True)
    # Convert boundary point in EPSG:3031 to lat/lon
    lon, lat = geographic_mask.to_epsg4326.transform(boundary_pt.x, boundary_pt.y)
    
    res = geographic_mask.query(lat, lon)
    # AMIP maritime safety standard: boundary intersections are covered/excluded
    assert res.is_geographically_excluded is True


# ====================================================================
# 3. Batch Spatial Queries
# ====================================================================

def test_batch_query(geographic_mask):
    lats = [-72.5, -72.5, -65.0, -50.0]
    lons = [-5.0, 10.0, 0.0, 0.0]
    results = geographic_mask.query_batch(lats, lons)
    assert len(results) == 4
    assert results[0].surface == SurfaceType.LAND
    assert results[1].surface == SurfaceType.ICE_SHELF
    assert results[2].surface == SurfaceType.OCEAN
    assert results[3].coverage_status == CoverageStatus.OUTSIDE_COVERAGE


# ====================================================================
# 4. Geometry Validation & Safe Repair
# ====================================================================

def test_validator_repairs_self_intersecting_polygon():
    validator = ADDGeometryValidator()
    # Create bowtie (self-intersecting) polygon
    bowtie = Polygon([(0, 0), (2, 2), (2, 0), (0, 2), (0, 0)])
    assert not bowtie.is_valid

    gdf = gpd.GeoDataFrame(
        {"surface": ["land"], "geometry": [bowtie]},
        crs="EPSG:3031",
    )
    cleaned_gdf, summary = validator.validate_and_repair_geometries(gdf)
    assert summary["invalid_detected"] == 1
    assert summary["repaired_features"] == 1
    assert cleaned_gdf.geometry.iloc[0].is_valid


def test_validator_rejects_missing_crs():
    validator = ADDGeometryValidator()
    gdf = gpd.GeoDataFrame({"surface": ["land"], "geometry": [box(0, 0, 1, 1)]})
    with pytest.raises(ValueError, match="no CRS defined"):
        validator.validate_crs(gdf)


def test_validator_rejects_wrong_crs():
    validator = ADDGeometryValidator()
    gdf = gpd.GeoDataFrame(
        {"surface": ["land"], "geometry": [box(0, 0, 1, 1)]},
        crs="EPSG:4326",
    )
    with pytest.raises(ValueError, match="SCAR ADD authoritative native CRS must be EPSG:3031"):
        validator.validate_crs(gdf)


# ====================================================================
# 5. H3 Aggregation & Configurable Blocking Thresholds
# ====================================================================

def test_h3_aggregation_and_thresholds(geographic_mask):
    aggregator = H3GeographicMaskAggregator(geographic_mask, default_blocking_threshold=0.5)

    # Pick an H3 cell centered in the synthetic land area (-72.5°S, -5.0°E) at resolution 5
    cell_id = h3.latlng_to_cell(-72.5, -5.0, 5)
    cell_attr = aggregator.compute_cell_attributes(cell_id)

    assert cell_attr.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert cell_attr.land_fraction > 0.95  # Deep inside synthetic land
    assert cell_attr.open_water_fraction < 0.05
    assert cell_attr.geographically_blocked is True

    # Test configurable blocking threshold
    # If threshold is 0.999 and land_fraction is 0.98, it would be allowed
    cell_high_thresh = aggregator.compute_cell_attributes(cell_id, blocking_threshold=0.9999)
    if cell_attr.land_fraction < 0.9999:
        assert cell_high_thresh.geographically_blocked is False

    # Pick an H3 cell in open ocean (-65.0°S, 0.0°E)
    ocean_cell = h3.latlng_to_cell(-65.0, 0.0, 5)
    ocean_attr = aggregator.compute_cell_attributes(ocean_cell)
    assert ocean_attr.coverage_status == CoverageStatus.INSIDE_COVERAGE
    assert ocean_attr.land_fraction == 0.0
    assert ocean_attr.open_water_fraction == 1.0
    assert ocean_attr.geographically_blocked is False

    # Pick an H3 cell north of 60°S (-55.0°S, 0.0°E)
    outside_cell = h3.latlng_to_cell(-55.0, 0.0, 5)
    outside_attr = aggregator.compute_cell_attributes(outside_cell)
    assert outside_attr.coverage_status == CoverageStatus.OUTSIDE_COVERAGE


def test_h3_resolution_configurability(geographic_mask):
    aggregator = H3GeographicMaskAggregator(geographic_mask)
    for res in [3, 4, 5, 6]:
        cell_id = h3.latlng_to_cell(-72.5, -5.0, res)
        attr = aggregator.compute_cell_attributes(cell_id)
        assert attr.resolution == res


# ====================================================================
# 6. Downloader Cache & Manual Mode
# ====================================================================

def test_downloader_manual_mode(tmp_path):
    manual_file = tmp_path / "manual_add.gpkg"
    manual_file.write_text("dummy_content")

    downloader = ADDDownloader(raw_data_dir=tmp_path / "raw")
    retrieved = downloader.download_or_get(mode="manual", manual_path=manual_file)
    assert retrieved == manual_file

    report_path = tmp_path / "raw" / "discovery_report.json"
    assert report_path.exists()
    with open(report_path) as f:
        data = json.load(f)
    assert data["edition"] == "7.12"
    assert data["local_raw_path"] == str(manual_file.resolve())


def test_downloader_local_cache(tmp_path):
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    cached_file = raw_dir / "add_coastline_high_res_polygon_v7_12.gpkg"
    cached_file.write_text("cached_data")

    downloader = ADDDownloader(raw_data_dir=raw_dir)
    retrieved = downloader.download_or_get(mode="auto")
    assert retrieved == cached_file
