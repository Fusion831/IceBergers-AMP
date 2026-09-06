"""Unit tests for deterministic mock sea-ice model and baselines."""

import pytest
from datetime import datetime, timezone
from domain.coordinates import BoundingBox, GridSpec
from models.sea_ice.mock_model import MockSeaIceModel
from models.sea_ice.baselines import PersistenceBaseline, ClimatologyBaseline, compute_baseline_comparison


def test_mock_sea_ice_determinism():
    model = MockSeaIceModel()
    ref_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    bbox = BoundingBox(min_latitude=-70.0, max_latitude=-60.0, min_longitude=60.0, max_longitude=80.0)
    grid = GridSpec(rows=10, cols=10)

    res1 = model.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)
    res2 = model.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)

    assert res1.forecast.values == res2.forecast.values
    assert res1.uncertainty.values == res2.uncertainty.values
    assert res1.ice_edge_geojson["type"] == "FeatureCollection"


def test_mock_sea_ice_uncertainty_growth():
    model = MockSeaIceModel()
    ref_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    bbox = BoundingBox(min_latitude=-70.0, max_latitude=-60.0, min_longitude=60.0, max_longitude=80.0)
    grid = GridSpec(rows=8, cols=8)

    t0 = model.predict(ref_time, horizon_days=0, bbox=bbox, grid_spec=grid)
    t14 = model.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)
    t90 = model.predict(ref_time, horizon_days=90, bbox=bbox, grid_spec=grid)

    mean_unc_t0 = sum(sum(r) for r in t0.uncertainty.values) / 64.0
    mean_unc_t14 = sum(sum(r) for r in t14.uncertainty.values) / 64.0
    mean_unc_t90 = sum(sum(r) for r in t90.uncertainty.values) / 64.0

    # Uncertainty strictly expands with lead time horizon
    assert mean_unc_t0 < mean_unc_t14 < mean_unc_t90


def test_baseline_comparison():
    model = MockSeaIceModel()
    persistence = PersistenceBaseline()
    climatology = ClimatologyBaseline()

    ref_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    bbox = BoundingBox(min_latitude=-70.0, max_latitude=-60.0, min_longitude=60.0, max_longitude=80.0)
    grid = GridSpec(rows=5, cols=5)

    fc = model.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)
    ps = persistence.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)
    cm = climatology.predict(ref_time, horizon_days=14, bbox=bbox, grid_spec=grid)

    comp = compute_baseline_comparison(fc, ps, cm)

    assert comp.mean_absolute_error >= 0.0
    assert comp.root_mean_squared_error >= comp.mean_absolute_error
    assert 0.0 <= comp.brier_score <= 1.0
