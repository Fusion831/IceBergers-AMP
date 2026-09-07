"""
Tests for Canonical AMIP Unified Computational Grid and EnvironmentCell Schema.
"""

from datetime import datetime, date
from pathlib import Path
import pytest
from domain.coordinates import GeoPoint, BoundingBox
from data_ingestion.grid.amip_grid import AMIPGrid
from data_ingestion.grid.environment_cell import EnvironmentCell
from data_ingestion.grid.unified_provider import AMIPUnifiedEnvironmentalProvider
from data_ingestion.nsidc.interface import NSIDCSeaIceInterface


def test_amip_grid_indexing():
    bbox = BoundingBox(
        min_latitude=-75.0,
        max_latitude=-50.0,
        min_longitude=0.0,
        max_longitude=90.0,
    )
    grid = AMIPGrid(bbox=bbox, resolution_deg=0.5)

    assert grid.n_rows == 50
    assert grid.n_cols == 180

    # Query Bharati Station (~ -69.4°S, 76.2°E)
    cell = grid.find_cell(-69.4, 76.2)
    assert cell is not None
    assert cell.cell_id.startswith("c_")
    assert cell.lat_min <= -69.4 <= cell.lat_max
    assert cell.lon_min <= 76.2 <= cell.lon_max

    # Query point outside bounds
    assert grid.find_cell(0.0, 0.0) is None


def test_environment_cell_schema():
    cell = EnvironmentCell(
        cell_id="c_0010_0020",
        valid_time=datetime(2024, 1, 1, 12, 0, 0),
        latitude=-65.5,
        longitude=45.2,
        lat_min=-66.0,
        lat_max=-65.0,
        lon_min=45.0,
        lon_max=46.0,
        sea_ice_concentration=42.5,
        current_u_ms=0.15,
        current_v_ms=-0.05,
        wind_speed_ms=12.4,
        is_land=False,
        is_navigable=True,
        provenance={"sic_source": "NSIDC_G02202_v6"},
    )

    assert cell.cell_id == "c_0010_0020"
    assert cell.sea_ice_concentration == 42.5
    assert cell.is_navigable is True
    assert cell.provenance["sic_source"] == "NSIDC_G02202_v6"


def test_unified_environmental_provider():
    provider = AMIPUnifiedEnvironmentalProvider()

    # Query Cape Town (Open Ocean, far north)
    pt_ocean = GeoPoint(latitude=-55.0, longitude=20.0)
    t = datetime(2024, 1, 1, 0, 0, 0)
    env = provider.get_point_environment(pt_ocean, t)

    assert "sea_ice_concentration" in env
    assert "current_u_ms" in env
    assert "wind_speed_ms" in env
    assert "bathymetry_depth_m" in env

    # Query EnvironmentCell
    cell_env = provider.get_environment_cell(pt_ocean, t)
    assert cell_env is not None
    assert cell_env.latitude is not None
    assert cell_env.sea_ice_concentration is not None
