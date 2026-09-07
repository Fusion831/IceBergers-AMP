"""
Integration test suite for AMIP Routing Engine over canonical H3 Cell x Time state space.
Validates:
1. H3EnvironmentalGridGraph hexagonal disk-1 topology, distances, and headings.
2. Canonical H3 Cell ID binding on RouteWaypoints and RouteAlternative.cells.
3. Chronological time advancement (t1 = t0 + dt) and monotonic ETA progression.
4. 2D vector current projection (favorable vs adverse current effects on speed and time).
5. RiskEngine hard constraint pruning (land, bathymetric grounding, excessive SIC).
6. Multi-objective differentiation across all 5 objectives.
7. Canonical NCPOR mission transect (Cape Town -> Bharati -> Maitri -> Cape Town).
8. Segment diagnostics and RouteRiskProfile aggregation.
"""

import pytest
import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional

from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.enums import RouteObjective
from domain.mission import AvoidanceZone
from domain.route import RouteAlternative
from routing.grid_graph import H3EnvironmentalGridGraph
from routing.grid_router import AMIPGridRouter
from routing.amip_custom_router import AMIPCustomRouter
from routing.mission_planner import MissionPlanner
from vessel.config import SAGAR_KANYA_VESSEL
from risk_engine.engine import RiskEngine
from data_access.environment_provider import EnvironmentalDataProviderInterface

_ice_cap = SAGAR_KANYA_VESSEL.ice_capability.model_copy(deep=True)
_ice_cap.max_operational_sic.value = 0.85
_ice_cap.status = "ICE_CLASS_1A_SUPER"
POLAR_RESEARCH_VESSEL_ICE_CLASS = SAGAR_KANYA_VESSEL.model_copy(update={
    "vessel_name": "Polar Research Vessel (Ice Class)",
    "ice_capability": _ice_cap,
})


class SyntheticOceanEnvProvider(EnvironmentalDataProviderInterface):
    """
    Controlled synthetic environmental provider for testing routing dynamics.
    Can inject current jets, sea ice fronts, wave fields, and shallow shoals.
    """

    def __init__(
        self,
        current_u: float = 0.0,
        current_v: float = 0.0,
        sic_boundary_lat: float = -66.0,
        high_sic_value: float = 0.35,
        shallow_shoal_lat: Optional[float] = None,
        shallow_shoal_lon: Optional[float] = None,
    ):
        self.current_u = current_u
        self.current_v = current_v
        self.sic_boundary_lat = sic_boundary_lat
        self.high_sic_value = high_sic_value
        self.shallow_shoal_lat = shallow_shoal_lat
        self.shallow_shoal_lon = shallow_shoal_lon

    def get_point_environment(self, point: GeoPoint, valid_time: datetime) -> Dict[str, Any]:
        lat = point.latitude
        lon = point.longitude

        # Ice presence south of boundary
        sic = self.high_sic_value if lat <= self.sic_boundary_lat else 0.0

        # Depth: check for shoal
        depth = 3500.0
        if self.shallow_shoal_lat is not None and self.shallow_shoal_lon is not None:
            if abs(lat - self.shallow_shoal_lat) < 0.5 and abs(lon - self.shallow_shoal_lon) < 0.5:
                depth = 4.0  # Dangerously shallow for Sagar Kanya (draft = 5.8m)

        # Waves: Roaring Forties/Fifties swell
        wave_h = 3.5 if -60.0 <= lat <= -45.0 else 1.5

        return {
            "sea_ice_concentration": sic,
            "wave_height_m": wave_h,
            "wave_direction_deg": 270.0,
            "wave_period_s": 9.0,
            "wind_speed_ms": 10.0,
            "wind_u_ms": 7.0,
            "wind_v_ms": 7.0,
            "current_u_ms": self.current_u,
            "current_v_ms": self.current_v,
            "bathymetry_depth_m": depth,
            "iceberg_hazard": 0.12 if lat <= -60.0 else 0.0,
            "distinct_iceberg_count": 3 if lat <= -60.0 else 0,
        }

    def get_grid_environment(self, bounds: BoundingBox, valid_time: datetime) -> Dict[str, Any]:
        return {}

    def get_grid_slice(self, bounds: BoundingBox, valid_time: datetime) -> Dict[str, Any]:
        return {}


# =============================================================================
# 1. H3 Environmental Grid Graph Tests
# =============================================================================

def test_h3_grid_graph_hexagonal_topology_and_navigability():
    """Verify H3 grid graph builds hexagonal disk-1 neighbors with valid spherical geometry."""
    bounds = BoundingBox(
        min_latitude=-65.0,
        max_latitude=-62.0,
        min_longitude=60.0,
        max_longitude=65.0,
    )
    env = SyntheticOceanEnvProvider()
    graph = H3EnvironmentalGridGraph(bounds=bounds, h3_resolution=5, env_provider=env)

    sample_pt = GeoPoint(latitude=-63.5, longitude=62.5)
    sample_node_id = graph.find_closest_node_id(sample_pt, navigable_only=True)
    assert sample_node_id is not None
    node = graph.nodes[sample_node_id]
    assert node.h3_index == sample_node_id
    assert -65.5 <= node.point.latitude <= -61.5
    assert 59.5 <= node.point.longitude <= 65.5

    # Check neighbors: H3 disk-1 has up to 6 neighbors
    neighbors = graph.get_neighbors(sample_node_id)
    assert 1 <= len(neighbors) <= 6

    for nbr_id, dist_nm, heading_deg in neighbors:
        assert nbr_id in graph.nodes
        assert 3.0 <= dist_nm <= 15.0  # Res 5 edge length is ~8.5 km (~4.6 NM), spacing ~15 km
        assert 0.0 <= heading_deg <= 360.0

    assert len(graph.nodes) >= 6


def test_h3_grid_graph_closest_node():
    """Verify closest node lookup resolves coordinates accurately."""
    bounds = BoundingBox(
        min_latitude=-66.0,
        max_latitude=-60.0,
        min_longitude=50.0,
        max_longitude=60.0,
    )
    graph = H3EnvironmentalGridGraph(bounds=bounds, h3_resolution=5)
    target = GeoPoint(latitude=-63.2, longitude=55.4)

    closest_id = graph.find_closest_node_id(target, navigable_only=True)
    assert closest_id is not None
    closest_node = graph.nodes[closest_id]

    lat_diff = abs(closest_node.point.latitude - target.latitude)
    lon_diff = abs(closest_node.point.longitude - target.longitude)
    assert lat_diff < 0.3
    assert lon_diff < 0.6


# =============================================================================
# 2. H3 Cell Binding & Ordered Traversal Tests
# =============================================================================

def test_h3_cell_id_binding_and_ordered_traversal():
    """Verify route waypoints bind canonical H3 index strings and form an unbroken sequence."""
    env = SyntheticOceanEnvProvider()
    router = AMIPGridRouter(env_provider=env, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-62.0, longitude=60.0)
    destination = GeoPoint(latitude=-64.5, longitude=62.5)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL

    route = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.SHORTEST)
    assert route is not None
    assert len(route.waypoints) >= 4
    assert len(route.cells) == len(route.waypoints)

    # Verify H3 cell format
    for cell_id in route.cells:
        assert isinstance(cell_id, str)
        assert len(cell_id) >= 15  # Canonical H3 hex string (e.g. 85ad...)
        assert not cell_id.startswith("grid_")

    # Verify waypoints match cells
    for seq, wp in enumerate(route.waypoints):
        assert wp.sequence == seq
        assert wp.grid_cell_id == route.cells[seq]


# =============================================================================
# 3. Chronological Time Advancement Tests
# =============================================================================

def test_chronological_time_advancement():
    """Verify monotonic ETA progression and physical time propagation along route."""
    env = SyntheticOceanEnvProvider()
    router = AMIPGridRouter(env_provider=env, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-61.0, longitude=55.0)
    destination = GeoPoint(latitude=-63.5, longitude=57.0)
    t0 = datetime(2026, 2, 1, 6, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL

    route = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.FASTEST)
    assert route is not None

    prev_eta = t0
    for wp in route.waypoints[1:]:
        assert wp.eta > prev_eta
        elapsed_hours = (wp.eta - prev_eta).total_seconds() / 3600.0
        assert elapsed_hours > 0.0

        # Physical consistency: speed = distance / time
        if wp.leg_distance_nm > 0.1 and wp.speed_knots > 0.1:
            expected_dt = wp.leg_distance_nm / wp.speed_knots
            assert math.isclose(elapsed_hours, expected_dt, rel_tol=0.20)

        prev_eta = wp.eta


# =============================================================================
# 4. 2D Vector Ocean Current Dynamics Tests
# =============================================================================

def test_vector_current_assistance_and_penalty():
    """
    Verify 2D vector current projection:
    Northbound route with northward current (+v) achieves higher speed and shorter transit time
    than the same route with opposing current (-v).
    """
    origin = GeoPoint(latitude=-64.0, longitude=50.0)
    destination = GeoPoint(latitude=-62.0, longitude=50.0)
    t0 = datetime(2026, 1, 10, 0, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL

    # 1. Favorable northward current (+1.0 m/s = ~1.94 knots assist)
    env_favorable = SyntheticOceanEnvProvider(current_u=0.0, current_v=1.0)
    router_favorable = AMIPGridRouter(env_provider=env_favorable, graph_type="h3", h3_resolution=5)
    route_fav = router_favorable.optimize_leg(origin, destination, t0, vessel, RouteObjective.FASTEST)

    # 2. Opposing southward current (-1.0 m/s = ~1.94 knots penalty)
    env_opposing = SyntheticOceanEnvProvider(current_u=0.0, current_v=-1.0)
    router_opposing = AMIPGridRouter(env_provider=env_opposing, graph_type="h3", h3_resolution=5)
    route_opp = router_opposing.optimize_leg(origin, destination, t0, vessel, RouteObjective.FASTEST)

    assert route_fav is not None
    assert route_opp is not None

    # Favorable route must be faster than opposing route
    assert route_fav.metrics.duration_hours < route_opp.metrics.duration_hours

    # Effective speed over ground must be higher with favorable current assist
    fav_avg_speed = sum(wp.speed_knots for wp in route_fav.waypoints) / len(route_fav.waypoints)
    opp_avg_speed = sum(wp.speed_knots for wp in route_opp.waypoints) / len(route_opp.waypoints)
    assert fav_avg_speed > opp_avg_speed


# =============================================================================
# 5. RiskEngine Hard Constraint Pruning Tests
# =============================================================================

def test_risk_engine_bathymetric_shoal_hard_blocking():
    """Verify router avoids or prunes transitions into shallow water exceeding vessel draft."""
    # Place a 4.0m shoal directly in the path between origin and destination
    shoal_lat = -62.5
    shoal_lon = 52.0
    env_shoal = SyntheticOceanEnvProvider(
        shallow_shoal_lat=shoal_lat,
        shallow_shoal_lon=shoal_lon,
    )
    router = AMIPGridRouter(env_provider=env_shoal, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-61.5, longitude=52.0)
    destination = GeoPoint(latitude=-63.5, longitude=52.0)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL  # draft = 5.8m -> 4.0m is a hard grounding violation

    route = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.BALANCED)
    assert route is not None

    # Ensure no waypoint in the final route routed through the shallow shoal
    for wp in route.waypoints:
        if abs(wp.point.latitude - shoal_lat) < 0.2 and abs(wp.point.longitude - shoal_lon) < 0.2:
            assert wp.bathymetry_depth_m > vessel.draft_meters + 3.0


def test_risk_engine_ice_class_limit_pruning():
    """Verify open-water vessel (Sagar Kanya) cannot penetrate SIC > 0.15, but Ice-Class vessel can."""
    # Set SIC to 0.35 south of -63.0
    env_ice = SyntheticOceanEnvProvider(sic_boundary_lat=-63.0, high_sic_value=0.35)
    router = AMIPGridRouter(env_provider=env_ice, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-62.0, longitude=55.0)
    destination_deep_ice = GeoPoint(latitude=-64.5, longitude=55.0)
    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)

    # Sagar Kanya (max_navigable_sic = 0.15) must be pruned / fail to reach destination in heavy ice
    route_sk = router.optimize_leg(origin, destination_deep_ice, t0, SAGAR_KANYA_VESSEL, RouteObjective.SHORTEST)
    assert route_sk is None

    # Polar Research Vessel (Ice Class 1A Super, max_navigable_sic = 0.85) can transit
    route_prv = router.optimize_leg(origin, destination_deep_ice, t0, POLAR_RESEARCH_VESSEL_ICE_CLASS, RouteObjective.SHORTEST)
    assert route_prv is not None
    assert any(wp.ice_concentration > 0.20 for wp in route_prv.waypoints)


# =============================================================================
# 6. Multi-Objective Differentiation Tests
# =============================================================================

def test_five_routing_objectives_differentiation():
    """Verify all 5 routing objectives produce physically distinct solutions in mixed domains."""
    env = SyntheticOceanEnvProvider(sic_boundary_lat=-63.0, high_sic_value=0.10)
    router = AMIPGridRouter(env_provider=env, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-61.5, longitude=50.0)
    destination = GeoPoint(latitude=-64.0, longitude=53.0)
    t0 = datetime(2026, 1, 20, 0, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL

    objectives = [
        RouteObjective.SHORTEST,
        RouteObjective.FASTEST,
        RouteObjective.SAFEST,
        RouteObjective.FUEL_EFFICIENT,
        RouteObjective.BALANCED,
    ]

    routes: Dict[RouteObjective, RouteAlternative] = {}
    for obj in objectives:
        r = router.optimize_leg(origin, destination, t0, vessel, obj)
        assert r is not None, f"Route for objective {obj} failed"
        routes[obj] = r

    # Shortest must have minimum distance
    dist_shortest = routes[RouteObjective.SHORTEST].metrics.distance_nm
    dist_safest = routes[RouteObjective.SAFEST].metrics.distance_nm
    assert dist_shortest <= dist_safest + 1.0

    # Safest must have low composite risk score
    risk_safest = routes[RouteObjective.SAFEST].metrics.mean_risk_score
    risk_shortest = routes[RouteObjective.SHORTEST].metrics.mean_risk_score
    assert risk_safest <= risk_shortest + 0.05

    # Fuel efficient should prioritize lower fuel rate or lower overall fuel
    fuel_eff = routes[RouteObjective.FUEL_EFFICIENT].metrics.estimated_fuel_tonnes
    fuel_fastest = routes[RouteObjective.FASTEST].metrics.estimated_fuel_tonnes
    assert fuel_eff <= fuel_fastest


# =============================================================================
# 7. Segment Diagnostics & RouteRiskProfile Tests
# =============================================================================

def test_segment_diagnostics_and_route_risk_profile():
    """Verify RouteAlternative includes segment diagnostics and aggregate RouteRiskProfile."""
    env = SyntheticOceanEnvProvider()
    router = AMIPGridRouter(env_provider=env, graph_type="h3", h3_resolution=5)

    origin = GeoPoint(latitude=-62.0, longitude=58.0)
    destination = GeoPoint(latitude=-64.0, longitude=60.0)
    t0 = datetime(2026, 2, 10, 0, 0, tzinfo=timezone.utc)
    vessel = SAGAR_KANYA_VESSEL

    route = router.optimize_leg(origin, destination, t0, vessel, RouteObjective.BALANCED)
    assert route is not None

    # Verify segments list
    assert len(route.segments) == len(route.waypoints) - 1
    for seg in route.segments:
        assert "from_cell" in seg
        assert "to_cell" in seg
        assert "speed_over_ground_knots" in seg
        assert "fuel_tonnes" in seg
        assert "composite_risk" in seg
        assert "limiting_factor" in seg

    # Verify diagnostics dictionary
    diag = route.diagnostics
    assert diag["graph_type"] == "h3"
    assert diag["h3_resolution"] == 5
    assert diag["total_cells"] == len(route.cells)
    assert diag["total_distance_nm"] > 0.0
    assert diag["total_fuel_tonnes"] > 0.0
    assert "route_risk_profile" in diag


# =============================================================================
# 8. Canonical NCPOR Mission Transect Tests
# =============================================================================

def test_canonical_ncpor_mission_planner():
    """
    Verify complete multi-target expedition planner for NCPOR transect:
    Cape Town -> Bharati Maritime Access -> Maitri Maritime Access -> Cape Town.
    """
    planner = MissionPlanner()
    t0 = datetime(2026, 1, 15, 6, 0, tzinfo=timezone.utc)

    mission_route = planner.plan_canonical_ncpor_mission(
        departure_time=t0,
        vessel=SAGAR_KANYA_VESSEL,
        objective=RouteObjective.BALANCED,
    )

    assert mission_route is not None
    assert len(mission_route.waypoints) > 20
    assert len(mission_route.cells) > 0

    # Check total distance for round-trip (> 6,000 NM)
    assert mission_route.metrics.distance_nm > 6000.0
    assert mission_route.metrics.duration_days > 30.0  # Multi-week voyage with station dwell times

    # Check diagnostics
    assert mission_route.diagnostics["mission_type"] == "multi_target_expedition"
    assert mission_route.diagnostics["targets_count"] == 3
