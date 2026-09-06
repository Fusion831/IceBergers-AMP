"""Unit tests for iceberg drift simulation and hazard field generation."""

import pytest
from datetime import datetime, timezone
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.iceberg import IcebergObservation, IcebergSizeClass
from iceberg_physics.mock_drift import MockIcebergDriftEngine
from iceberg_physics.hazard_generator import IcebergHazardGenerator


@pytest.fixture
def test_iceberg() -> IcebergObservation:
    return IcebergObservation(
        iceberg_id="TEST-IB-01",
        name="Test Iceberg Alpha",
        observed_at=datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc),
        location=GeoPoint(latitude=-65.0, longitude=60.0),
        size_class=IcebergSizeClass.LARGE,
        length_m=5000.0,
        width_m=3000.0,
        drift_speed_knots=0.6,
        drift_heading_deg=300.0,
    )


def test_drift_ensemble_generation(test_iceberg: IcebergObservation):
    engine = MockIcebergDriftEngine()
    ensemble = engine.simulate_ensemble(
        observation=test_iceberg,
        forecast_days=10,
        ensemble_size=20,
        step_hours=6,
    )

    assert ensemble.iceberg_id == test_iceberg.iceberg_id
    assert ensemble.ensemble_size == 20
    assert len(ensemble.members) == 20
    assert len(ensemble.median_trajectory) > 10
    assert len(ensemble.p50_corridor) > 10
    assert len(ensemble.p90_corridor) > 10


def test_iceberg_hazard_generator(test_iceberg: IcebergObservation):
    engine = MockIcebergDriftEngine()
    hazard_gen = IcebergHazardGenerator()

    ensemble = engine.simulate_ensemble(
        observation=test_iceberg,
        forecast_days=5,
        ensemble_size=15,
        step_hours=12,
    )

    valid_time = datetime(2026, 1, 4, 0, 0, tzinfo=timezone.utc)
    bbox = BoundingBox(min_latitude=-67.0, max_latitude=-63.0, min_longitude=55.0, max_longitude=65.0)
    grid = GridSpec(rows=10, cols=10)

    hazard_field = hazard_gen.generate_hazard_field(
        ensembles=[ensemble],
        valid_time=valid_time,
        bbox=bbox,
        grid_spec=grid,
    )

    assert len(hazard_field.values) == 10
    assert len(hazard_field.values[0]) == 10
    assert 0.0 <= hazard_field.max_hazard <= 1.0

    # Test corridor intersection
    path = [GeoPoint(latitude=-65.0, longitude=59.0), GeoPoint(latitude=-65.0, longitude=61.0)]
    intersections = hazard_gen.compute_corridor_intersections([ensemble], path)
    assert len(intersections) > 0
