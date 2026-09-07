"""
Comprehensive Test Suite for Canonical H3 Spatial Backbone and Temporal Integration.
Validates all 25 architectural criteria, vector aggregation mathematics, circular wave direction,
all 73 iceberg representation, GEBCO statistics, SCAR ADD fractions, and lookup API.
"""

from datetime import datetime, timezone, timedelta
import pytest
import h3
import numpy as np
import pandas as pd
from shapely.geometry import Polygon

from data_ingestion.h3.config import H3Config, default_h3_config
from data_ingestion.h3.geometry import H3GeometryEngine
from data_ingestion.h3.grid import AntarcticH3GridGenerator
from data_ingestion.h3.static_layers import H3StaticLayerMapper
from data_ingestion.h3.environmental_layers import (
    circular_mean_degrees,
    vector_mean_components,
    H3EnvironmentalAggregator,
)
from data_ingestion.h3.iceberg import H3IcebergIndexer
from data_ingestion.h3.hazard import H3HazardMapper
from data_ingestion.h3.ml_interface import SeaIceForecastCell, MockSeaIceMLProvider
from data_ingestion.h3.temporal import H3TemporalAligner
from data_ingestion.h3.lookup import H3CellLookupService
from data_ingestion.h3.validator import H3Validator
from data_ingestion.h3.schema import TemporalQualityStatus, H3GeographicStatus


# 1. Config & Resolution Configurability
def test_h3_config_and_resolution():
    cfg = H3Config(resolution=5)
    assert cfg.resolution == 5
    cfg4 = H3Config(resolution=4)
    assert cfg4.resolution == 4


# 2. Geometry Engine & Projections
def test_h3_geometry_conversions():
    engine = H3GeometryEngine()
    test_lat, test_lon = -65.0, 10.0
    cell_id = engine.latlng_to_cell(test_lat, test_lon, resolution=5)
    assert h3.is_valid_cell(cell_id)
    assert h3.get_resolution(cell_id) == 5

    c_lat, c_lon = engine.cell_to_latlng(cell_id)
    assert abs(c_lat - test_lat) < 0.2
    assert abs(c_lon - test_lon) < 0.5

    poly4326 = engine.cell_to_polygon_4326(cell_id)
    assert isinstance(poly4326, Polygon)
    assert poly4326.is_valid

    poly3031 = engine.cell_to_polygon_3031(cell_id)
    assert isinstance(poly3031, Polygon)
    assert poly3031.is_valid
    assert poly3031.area > 0


# 3. Domain Grid Generation
def test_domain_grid_generation():
    gen = AntarcticH3GridGenerator()
    cells = gen.generate_domain_cells(resolution=4)
    assert len(cells) > 10000
    diag = gen.get_grid_diagnostics(len(cells), resolution=4)
    assert diag["h3_resolution"] == 4
    assert diag["total_cells"] == len(cells)


# 4. Vector Aggregation Mathematics (Currents and Winds)
def test_vector_component_aggregation():
    # Opposing u vectors (1 and -1) must cancel out to 0
    # Aligned v vectors (2 and 2) must average to 2
    # Resulting speed must be 2.0, direction 0° (North)
    u_mean, v_mean, spd, dir_deg = vector_mean_components([1.0, -1.0], [2.0, 2.0])
    assert u_mean == 0.0
    assert v_mean == 2.0
    assert spd == 2.0
    assert dir_deg == 0.0

    # Test with None and NaN values
    u_m, v_m, spd_m, _ = vector_mean_components([5.0, None, np.nan], [0.0, None, np.nan])
    assert u_m == 5.0
    assert v_m == 0.0
    assert spd_m == 5.0


# 5. Circular Wave Direction Aggregation (No Wrap-Around Artifacts)
def test_circular_wave_direction_aggregation():
    # 359° and 1° must average to 0°/360°, NEVER to 180°!
    avg_deg = circular_mean_degrees([359.0, 1.0])
    assert avg_deg in (0.0, 360.0)

    # 89° and 91° must average to 90°
    avg_east = circular_mean_degrees([89.0, 91.0])
    assert avg_east == 90.0

    # Empty / None
    assert circular_mean_degrees([]) is None


# 6. NSIDC Valid Pixel Masking
def test_nsidc_valid_pixel_masking():
    # Pixels with invalid flag 254 (land) and 255 (missing) must be excluded
    res = H3EnvironmentalAggregator.aggregate_nsidc_sic(
        raw_sic_values=[70.0, 80.0, 254.0, 255.0],
        valid_pixel_mask=[True, True, False, False],
    )
    assert res["sic_mean"] == 75.0
    assert res["sic_min"] == 70.0
    assert res["sic_max"] == 80.0
    assert res["sic_valid_fraction"] == 0.5


# 7. SCAR ADD & GEBCO Static Mapping
def test_static_layer_mapper():
    mapper = H3StaticLayerMapper()
    # High-latitude land cell in Queen Maud Land
    c_land = mapper.geom.latlng_to_cell(-75.0, 0.0, 5)
    st_land = mapper.map_cell(c_land)
    assert st_land.h3_resolution == 5
    assert st_land.land_fraction > 0.0 or st_land.ice_shelf_fraction > 0.0

    # Open ocean cell
    c_ocean = mapper.geom.latlng_to_cell(-50.0, 0.0, 5)
    st_ocean = mapper.map_cell(c_ocean)
    assert st_ocean.ocean_fraction == 1.0
    assert st_ocean.geographic_status == H3GeographicStatus.OPEN_OCEAN
    assert st_ocean.is_blocked is False


# 8. All 73 Icebergs Represented in H3
def test_all_73_icebergs_indexed():
    indexer = H3IcebergIndexer()
    obs_df, meta_obs = indexer.index_observations()
    assert meta_obs["distinct_iceberg_ids_count"] == 73
    assert meta_obs["all_73_icebergs_present"] is True
    assert "h3_cell" in obs_df.columns
    assert (obs_df["h3_cell"] != "").all()

    traj_df, meta_traj = indexer.index_trajectories()
    assert meta_traj["distinct_iceberg_ids_count"] == 73
    assert meta_traj["all_73_icebergs_present"] is True
    assert "h3_cell" in traj_df.columns


# 9. Iceberg Hazard Mapping
def test_iceberg_hazard_mapper():
    mapper = H3HazardMapper()
    df_hz, meta_hz = mapper.process_hazard_field()
    assert meta_hz["distinct_cells_affected"] > 0
    assert "cell_id" in df_hz.columns
    assert "hazard_score" in df_hz.columns


# 10. Sea-Ice ML Contract Interface
def test_sea_ice_ml_interface():
    provider = MockSeaIceMLProvider()
    forecast = provider.predict_cell(
        cell_id="85b736bffffffff",
        valid_time=datetime(2026, 9, 8, 12, 0, tzinfo=timezone.utc),
        base_sic=25.0,
        lead_hours=48.0,
    )
    assert isinstance(forecast, SeaIceForecastCell)
    assert forecast.sic == 25.0
    assert forecast.forecast_horizon_hours == 48.0
    assert forecast.quality_status == TemporalQualityStatus.MODEL_PREDICTED


# 11. Temporal Alignment & Monotonicity
def test_temporal_alignment():
    aligner = H3TemporalAligner(step_hours=6)
    start_t = datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)
    end_t = start_t + timedelta(days=2)
    times = aligner.generate_canonical_time_index(start_t, end_t)
    assert len(times) == 9  # T+0, 6, 12, 18, 24, 30, 36, 42, 48
    assert times == sorted(times)


# 12. Lookup Service & Navigability
def test_h3_lookup_service():
    service = H3CellLookupService()
    test_lat, test_lon = -60.0, 0.0
    cell_id = service.latlon_to_cell(test_lat, test_lon, resolution=5)
    assert h3.is_valid_cell(cell_id)

    neighbors = service.neighboring_cells(cell_id, ring_size=1)
    assert len(neighbors) == 6
    assert cell_id not in neighbors


# 13. Complete 25-Point Validation Report
def test_25_point_validation_suite():
    validator = H3Validator()
    report = validator.run_all_validations()
    assert report["total_checks"] == 25
    assert report["all_passed"] is True
    assert report["passed_checks"] == 25
