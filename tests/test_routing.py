"""Unit tests for naval fuel model, mock route optimizer, and 4D route validation."""

import pytest
from datetime import datetime, timezone
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from routing.fuel_model import NavalArchitectureFuelModel
from routing.mock_optimizer import MockRouteOptimizer
from routing.validator import RouteValidator
from services.risk_service import RiskService


def test_naval_fuel_model(sample_vessel: VesselProfile):
    fuel_model = NavalArchitectureFuelModel()

    # Open water at 11 knots
    burn_open = fuel_model.estimate_leg_fuel(
        vessel=sample_vessel,
        distance_nm=100.0,
        speed_knots=11.0,
        sic=0.0,
        wave_height_m=1.5,
    )

    # In 60% sea ice at 11 knots (ice resistance adds significant fuel burn)
    burn_ice = fuel_model.estimate_leg_fuel(
        vessel=sample_vessel,
        distance_nm=100.0,
        speed_knots=11.0,
        sic=0.6,
        wave_height_m=1.5,
    )

    assert burn_open > 0.0
    assert burn_ice > burn_open * 1.5  # Significant ice resistance increase


def test_four_distinct_routes_generated(sample_vessel: VesselProfile):
    optimizer = MockRouteOptimizer()
    risk_service = RiskService()
    start_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Transect from southern ocean corridor towards Bharati
    start = GeoPoint(latitude=-55.0, longitude=65.0)
    dest = GeoPoint(latitude=-69.4, longitude=76.2)

    risk_field = risk_service.get_risk_field(valid_time=start_time, vessel=sample_vessel)

    r_safest = optimizer.optimize(start, dest, start_time, RouteObjective.SAFEST, sample_vessel, risk_field)
    r_fastest = optimizer.optimize(start, dest, start_time, RouteObjective.FASTEST, sample_vessel, risk_field)
    r_fuel = optimizer.optimize(start, dest, start_time, RouteObjective.FUEL_EFFICIENT, sample_vessel, risk_field)
    r_balanced = optimizer.optimize(start, dest, start_time, RouteObjective.BALANCED, sample_vessel, risk_field)

    # 1. Geometries must be genuinely distinct!
    coords_safest = [(wp.point.latitude, wp.point.longitude) for wp in r_safest.waypoints]
    coords_fastest = [(wp.point.latitude, wp.point.longitude) for wp in r_fastest.waypoints]
    coords_fuel = [(wp.point.latitude, wp.point.longitude) for wp in r_fuel.waypoints]
    coords_balanced = [(wp.point.latitude, wp.point.longitude) for wp in r_balanced.waypoints]

    assert coords_safest != coords_fastest
    assert coords_safest != coords_fuel
    assert coords_fastest != coords_balanced

    # 2. Objective properties hold
    assert r_fastest.metrics.duration_hours < r_safest.metrics.duration_hours
    assert r_safest.metrics.mean_risk <= r_fastest.metrics.mean_risk
    assert r_fuel.metrics.fuel_consumption_tonnes < r_fastest.metrics.fuel_consumption_tonnes


def test_4d_route_validator(sample_vessel: VesselProfile):
    optimizer = MockRouteOptimizer()
    validator = RouteValidator()
    risk_service = RiskService()
    start_time = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    start = GeoPoint(latitude=-55.0, longitude=65.0)
    dest = GeoPoint(latitude=-69.4, longitude=76.2)

    risk_field = risk_service.get_risk_field(valid_time=start_time, vessel=sample_vessel)
    route = optimizer.optimize(start, dest, start_time, RouteObjective.BALANCED, sample_vessel, risk_field)

    summary = validator.validate_route(route, risk_field, sample_vessel)

    assert summary.waypoint_count == len(route.waypoints)
    assert 0.0 <= summary.mean_risk <= 1.0
    assert summary.max_risk >= summary.mean_risk
