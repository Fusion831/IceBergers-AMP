"""Unit tests for hard constraints, soft costs, and composite risk engine."""

import pytest
from datetime import datetime, timezone
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.vessel import VesselProfile
from domain.risk import RiskWeightsConfig
from risk_engine.constraints import HardConstraintChecker
from risk_engine.soft_costs import SoftCostCalculator
from risk_engine.engine import RiskEngine
from services.environment_service import EnvironmentService
from services.sea_ice_service import SeaIceService
from services.iceberg_service import IcebergService


def test_hard_constraints():
    checker = HardConstraintChecker()
    vessel = VesselProfile(draft_meters=5.6, ice_clearance_depth_margin_m=3.0)  # threshold 8.6m

    # Shallow water violation (e.g. 5m depth)
    is_viol, reason = checker.check_point(
        point=GeoPoint(latitude=-65.0, longitude=50.0),
        depth_m=5.0,
        sic=0.1,
        iceberg_dist_nm=5.0,
        vessel=vessel,
    )
    assert is_viol is True
    assert "Shallow bathymetry" in reason

    # Land mask violation
    is_viol, reason = checker.check_point(
        point=GeoPoint(latitude=-72.0, longitude=50.0),
        depth_m=100.0,
        sic=0.1,
        iceberg_dist_nm=5.0,
        vessel=vessel,
        is_land=True,
    )
    assert is_viol is True
    assert "Land/ice shelf barrier" in reason

    # Safe deep water point
    is_viol, reason = checker.check_point(
        point=GeoPoint(latitude=-60.0, longitude=50.0),
        depth_m=3000.0,
        sic=0.1,
        iceberg_dist_nm=5.0,
        vessel=vessel,
        is_land=False,
    )
    assert is_viol is False


def test_composite_risk_engine():
    engine = RiskEngine()
    env_service = EnvironmentService()
    sea_ice_service = SeaIceService()
    iceberg_service = IcebergService()

    valid_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    bbox = BoundingBox(min_latitude=-70.0, max_latitude=-60.0, min_longitude=60.0, max_longitude=80.0)
    grid = GridSpec(rows=8, cols=8)

    env_slice = env_service.get_slice(valid_time, bbox, grid)
    sic_res = sea_ice_service.get_forecast(valid_time, horizon_days=14, bbox=bbox, grid_spec=grid)
    hazard_field = iceberg_service.get_hazard_field(valid_time, bbox, grid)

    risk_field = engine.evaluate_grid(
        valid_time=valid_time,
        env_slice=env_slice,
        sea_ice_forecast=sic_res,
        iceberg_hazard=hazard_field,
    )

    assert len(risk_field.values) == 8
    assert len(risk_field.values[0]) == 8
    assert 0.0 <= risk_field.mean_risk <= 1.0
    assert risk_field.p95_risk >= risk_field.mean_risk
