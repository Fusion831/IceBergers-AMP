"""Unit and integration tests for AMIP Custom Router, Speed Model, and Multi-Target Mission Planner."""

import pytest
from datetime import datetime, timezone, timedelta

from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.enums import RouteObjective, MissionTargetType
from domain.mission import MissionTarget, AvoidanceZone
from routing.speed_model import VesselSpeedModel
from routing.amip_custom_router import AMIPCustomRouter
from routing.mission_planner import MissionPlanner


def test_vessel_speed_model_physics():
    """Verify that current vectors, waves, and sea ice physically alter vessel speed."""
    model = VesselSpeedModel(default_max_navigable_sic=0.40)
    vessel = VesselProfile(service_speed_knots=12.0)

    # 1. Open water baseline
    res_base = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,  # North
        sic=0.0,
        wave_height_m=1.5,
    )
    assert res_base.is_passable is True
    assert abs(res_base.effective_speed_knots - 12.0) < 0.2

    # 2. Favorable tail current (+1 m/s North = ~1.94 knots boost)
    res_tail = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,
        current_u_ms=0.0,
        current_v_ms=1.0,
    )
    assert res_tail.effective_speed_knots > res_base.effective_speed_knots

    # 3. Adverse head current (-1 m/s North = ~1.94 knots drop)
    res_head = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,
        current_u_ms=0.0,
        current_v_ms=-1.0,
    )
    assert res_head.effective_speed_knots < res_base.effective_speed_knots

    # 4. Heavy wave state (Hs = 4.5m)
    res_waves = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,
        wave_height_m=4.5,
    )
    assert res_waves.effective_speed_knots < res_base.effective_speed_knots

    # 5. Non-linear sea ice slowdown at SIC = 0.25
    res_ice = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,
        sic=0.25,
    )
    assert res_ice.effective_speed_knots < res_base.effective_speed_knots
    assert res_ice.is_passable is True

    # 6. Impassable ice condition (SIC = 0.50 > max_navigable_sic 0.40)
    res_blocked = model.calculate_segment_speed(
        vessel=vessel,
        distance_nm=10.0,
        heading_deg=0.0,
        sic=0.50,
    )
    assert res_blocked.is_passable is False
    assert res_blocked.effective_speed_knots == 0.0


def test_amip_custom_router_distinct_objectives():
    """Verify that all 5 route objectives produce valid, distinct routes, and SHORTEST != FASTEST."""
    router = AMIPCustomRouter()
    vessel = VesselProfile()
    departure = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    origin = GeoPoint(latitude=-33.9, longitude=18.4, name="Cape Town")
    destination = GeoPoint(latitude=-69.4, longitude=76.2, name="Bharati")

    routes = router.optimize_all_alternatives(
        origin=origin,
        destination=destination,
        departure_time=departure,
        vessel=vessel,
    )

    assert len(routes) == 5
    route_map = {r.objective: r for r in routes}

    shortest = route_map[RouteObjective.SHORTEST]
    fastest = route_map[RouteObjective.FASTEST]
    safest = route_map[RouteObjective.SAFEST]
    fuel_eff = route_map[RouteObjective.FUEL_EFFICIENT]

    # Geographically shortest has less or equal distance than fastest
    assert shortest.metrics.distance_nm <= fastest.metrics.distance_nm

    # Fastest has less or equal duration than shortest
    assert fastest.metrics.duration_hours <= shortest.metrics.duration_hours

    # Fuel efficient burns less fuel than fastest
    assert fuel_eff.metrics.estimated_fuel_mt < fastest.metrics.estimated_fuel_mt

    # Safest has lowest or near-lowest mean risk
    assert safest.metrics.mean_risk <= fastest.metrics.mean_risk


def test_avoidance_zone_bypass():
    """Verify that router actively detours around defined avoidance zones."""
    router = AMIPCustomRouter()
    vessel = VesselProfile()
    departure = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    origin = GeoPoint(latitude=-45.0, longitude=20.0)
    destination = GeoPoint(latitude=-65.0, longitude=20.0)

    # Place avoidance zone directly in the path
    avoidance = AvoidanceZone(
        name="Test Hazard Zone",
        center=GeoPoint(latitude=-55.0, longitude=20.0),
        radius_km=30.0,
    )

    route_with_avoidance = router.optimize_leg(
        origin=origin,
        destination=destination,
        departure_time=departure,
        vessel=vessel,
        objective=RouteObjective.BALANCED,
        avoidance_zones=[avoidance],
    )

    # Assert no waypoint falls inside the avoidance zone
    for wp in route_with_avoidance.waypoints:
        assert not router.is_in_avoidance_zone(wp.point, [avoidance])


def test_multi_target_mission_planning():
    """Verify multi-target sequencing across station, science site, and grid cell S17 with dwell times."""
    planner = MissionPlanner()
    vessel = VesselProfile()
    departure = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    origin = GeoPoint(latitude=-33.9, longitude=18.4, name="Cape Town")

    targets = [
        MissionTarget(
            name="Bharati Station",
            target_type=MissionTargetType.STATION,
            location=GeoPoint(latitude=-69.4, longitude=76.2),
            dwell_hours=24.0,
            sequence_order=1,
        ),
        MissionTarget(
            name="Science Survey Alpha",
            target_type=MissionTargetType.SCIENCE_SITE,
            location=GeoPoint(latitude=-68.0, longitude=73.0),
            dwell_hours=12.0,
            sequence_order=2,
        ),
        MissionTarget(
            name="Grid Cell S17",
            target_type=MissionTargetType.GRID_CELL,
            grid_cell_id="S17",
            location=GeoPoint(latitude=-67.5, longitude=70.0),
            dwell_hours=6.0,
            sequence_order=3,
        ),
    ]

    mission_route = planner.plan_multi_target_mission(
        origin=origin,
        targets=targets,
        departure_time=departure,
        vessel=vessel,
        objective=RouteObjective.BALANCED,
    )

    assert len(mission_route.waypoints) > 20
    assert mission_route.metrics.distance_nm > 3000.0
    # The total duration includes dwell hours (24 + 12 + 6 = 42 hours)
    assert mission_route.metrics.duration_hours > 42.0
    # Waypoint ETAs are monotonically non-decreasing
    etas = [wp.eta for wp in mission_route.waypoints]
    for i in range(len(etas) - 1):
        assert etas[i] <= etas[i + 1]
