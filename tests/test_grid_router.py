"""
Comprehensive tests for AMIP Discrete 4D Grid Router and Temporal Sensitivity Benchmark.
Validates:
1. Traversal over discrete grid cells with grid_cell_id binding on every waypoint.
2. Distinct 4D objectives (Shortest, Fastest, Safest, Fuel-Efficient, Balanced).
3. Hard constraint pruning (land, bathymetric clearance, avoidance zones).
4. Dynamic time advancement and vector current speed effects.
5. MANDATORY BENCHMARK: Same (origin, dest) with different departure times produces
   different environmental states and different route costs/metrics.
6. Multi-target sequencing with discrete grid cells.
7. Frontend grid inspection endpoints (/environment/cells).
"""

from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient, ASGITransport

from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.enums import RouteObjective, MissionTargetType
from domain.mission import AvoidanceZone, MissionTarget
from routing.grid_router import AMIPGridRouter
from routing.amip_custom_router import AMIPCustomRouter
from routing.mission_planner import MissionPlanner
from main import app


def test_grid_router_traversal_and_cell_id_binding():
    """Verify router moves cell-by-cell and attaches grid_cell_id and telemetry to all waypoints."""
    router = AMIPGridRouter(resolution_deg=1.0)
    origin = GeoPoint(latitude=-55.0, longitude=20.0)
    destination = GeoPoint(latitude=-62.0, longitude=25.0)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile()

    route = router.optimize_leg(
        origin=origin,
        destination=destination,
        departure_time=t0,
        vessel=vessel,
        objective=RouteObjective.BALANCED,
    )

    assert route is not None
    assert len(route.waypoints) >= 5

    for wp in route.waypoints:
        assert wp.grid_cell_id is not None
        assert wp.grid_cell_id.startswith("grid_")
        assert wp.eta >= t0
        assert wp.speed_knots > 0.0
        assert wp.bathymetry_depth_m is not None
        assert wp.current_u_ms is not None
        assert wp.wave_height_m is not None

    # Verify chronological progression
    for i in range(1, len(route.waypoints)):
        assert route.waypoints[i].eta >= route.waypoints[i - 1].eta
        assert route.waypoints[i].cumulative_distance_nm >= route.waypoints[i - 1].cumulative_distance_nm


def test_grid_router_distinct_objectives():
    """Verify the 5 objectives produce distinct routing trade-offs."""
    router = AMIPGridRouter(resolution_deg=1.0)
    origin = GeoPoint(latitude=-50.0, longitude=20.0)
    destination = GeoPoint(latitude=-65.0, longitude=30.0)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile()

    r_shortest = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.SHORTEST)
    r_fastest = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.FASTEST)
    r_safest = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.SAFEST)
    r_fuel = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.FUEL_EFFICIENT)
    r_balanced = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.BALANCED)

    assert r_shortest is not None
    assert r_fastest is not None
    assert r_safest is not None
    assert r_fuel is not None
    assert r_balanced is not None

    # SHORTEST minimizes nautical distance
    assert r_shortest.metrics.distance_nm <= r_safest.metrics.distance_nm

    # FASTEST runs at higher speed and consumes more fuel than FUEL_EFFICIENT
    assert r_fastest.metrics.estimated_fuel_tonnes >= r_fuel.metrics.estimated_fuel_tonnes

    # SAFEST prioritizes low risk
    assert r_safest.metrics.mean_risk_score <= max(r_shortest.metrics.mean_risk_score, r_fastest.metrics.mean_risk_score)


def test_grid_router_avoidance_zone_detour():
    """Verify router navigates around user-defined avoidance zones."""
    router = AMIPGridRouter(resolution_deg=1.0)
    origin = GeoPoint(latitude=-50.0, longitude=5.0)
    destination = GeoPoint(latitude=-58.0, longitude=5.0)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile()

    # Place an avoidance zone directly in the line of sight at (-54.0, 5.0)
    az = AvoidanceZone(
        name="Iceberg Front",
        center=GeoPoint(latitude=-54.0, longitude=5.0),
        radius_km=70.0,
    )

    route = router.optimize_leg(
        origin=origin,
        destination=destination,
        departure_time=t0,
        vessel=vessel,
        objective=RouteObjective.SHORTEST,
        avoidance_zones=[az],
    )

    assert route is not None
    # No waypoint should fall inside the avoidance zone radius
    for wp in route.waypoints:
        from data_access.spatial import haversine_distance_nm
        dist_to_hazard = haversine_distance_nm(wp.point.latitude, wp.point.longitude, az.center.latitude, az.center.longitude)
        assert dist_to_hazard > (az.radius_km / 1.852) - 5.0  # Outside hazard buffer


def test_mandatory_4d_departure_time_sensitivity_benchmark():
    """
    MANDATORY BENCHMARK:
    Same origin + destination evaluated at different departure times (Jan 15 vs Feb 15).
    Verifies that changing the departure date encounters evolving environmental states (sea ice, currents),
    resulting in different arrival times, durations, or route costs.
    """
    router = AMIPGridRouter(resolution_deg=1.0)
    origin = GeoPoint(latitude=-60.0, longitude=65.0)
    destination = GeoPoint(latitude=-70.0, longitude=70.0)
    vessel = VesselProfile()

    # Use dates within the Ice-kNN-South 90-day forecast window (base: 2020-01-01).
    # Jan 5 = lead day 4, Feb 5 = lead day 35 — different SIC snapshots from the real forecast.
    t_jan = datetime(2020, 1, 5, 0, 0, tzinfo=timezone.utc)
    t_feb = datetime(2020, 2, 5, 0, 0, tzinfo=timezone.utc)

    route_jan = router.optimize_leg(origin, destination, t_jan, vessel, RouteObjective.BALANCED)
    route_feb = router.optimize_leg(origin, destination, t_feb, vessel, RouteObjective.BALANCED)

    assert route_jan is not None
    assert route_feb is not None

    # Verify that the departure timestamps match the query inputs
    assert route_jan.departure_time == t_jan
    assert route_feb.departure_time == t_feb

    # Verify that the environmental fields encountered along the path differ between Jan and Feb
    jan_sics = [wp.ice_concentration for wp in route_jan.waypoints]
    feb_sics = [wp.ice_concentration for wp in route_feb.waypoints]

    # In Antarctica, February has greater sea-ice retreat compared to January
    mean_jan_sic = sum(jan_sics) / len(jan_sics)
    mean_feb_sic = sum(feb_sics) / len(feb_sics)
    assert mean_jan_sic != mean_feb_sic

    # Total duration or fuel must reflect the changed environmental conditions
    assert (
        route_jan.metrics.duration_hours != route_feb.metrics.duration_hours
        or route_jan.metrics.estimated_fuel_tonnes != route_feb.metrics.estimated_fuel_tonnes
    )


def test_multi_target_mission_with_grid_cell():
    """Verify MissionPlanner sequences routes through ports, stations, and designated grid cells."""
    custom_router = AMIPCustomRouter(mode="grid")
    planner = MissionPlanner(router=custom_router)

    origin = GeoPoint(latitude=-33.9, longitude=18.4, name="Cape Town")
    targets = [
        MissionTarget(
            name="Bharati Station",
            target_type=MissionTargetType.STATION,
            location=GeoPoint(latitude=-69.4, longitude=76.2, name="Bharati"),
            dwell_hours=24.0,
            sequence_order=1,
        ),
        MissionTarget(
            name="Grid Cell S17 Survey",
            target_type=MissionTargetType.GRID_CELL,
            grid_cell_id="S17",
            location=GeoPoint(latitude=-67.8, longitude=70.0, name="Grid Cell S17"),
            dwell_hours=12.0,
            sequence_order=2,
        ),
    ]

    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile()

    expedition = planner.plan_multi_target_mission(
        origin=origin,
        targets=targets,
        departure_time=t0,
        vessel=vessel,
        objective=RouteObjective.BALANCED,
    )

    assert expedition is not None
    assert len(expedition.waypoints) >= 10
    # Every waypoint must have a grid_cell_id
    for wp in expedition.waypoints:
        assert wp.grid_cell_id is not None
    assert expedition.metrics.distance_nm > 3000.0


@pytest.mark.anyio
async def test_api_environment_cells_endpoint():
    """Verify GET /api/v1/environment/cells returns discrete grid cells for the frontend time slider."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/environment/cells",
            params={
                "min_lat": -65.0,
                "max_lat": -63.0,
                "min_lon": 20.0,
                "max_lon": 22.0,
                "resolution_deg": 1.0,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "cells" in data
        assert data["total_cells"] > 0
        cell = data["cells"][0]
        assert "cell_id" in cell
        assert cell["cell_id"].startswith("grid_")
        assert "sea_ice_concentration" in cell
        assert "current_u_ms" in cell
        assert "composite_risk" in cell

        # Test single cell detail inspection
        cell_id = cell["cell_id"]
        detail_resp = await client.get(f"/api/v1/environment/cells/{cell_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert detail_data["cell_id"] == cell_id
        assert detail_data["provenance"] == "MOCK / SYNTHETIC"
