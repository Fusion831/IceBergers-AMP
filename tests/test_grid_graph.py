"""
Unit tests for EnvironmentalGridGraph (Stage 1).
Validates structured cell IDs, constraint pruning, avoidance zone detours, and geodesic neighbor connectivity.
"""

from datetime import datetime, timezone
import pytest

from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.mission import AvoidanceZone
from routing.grid_graph import EnvironmentalGridGraph


def test_structured_cell_ids_and_resolution():
    """Verify grid cells follow grid_{res}_{row}_{col} format and store coordinates."""
    bounds = BoundingBox(
        min_latitude=-65.0,
        max_latitude=-60.0,
        min_longitude=10.0,
        max_longitude=15.0,
    )
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0)

    # 6 rows (-65 to -60), 6 cols (10 to 15) -> 36 nodes
    assert len(graph.nodes) == 36
    assert "grid_100_r0_c0" in graph.nodes
    node_0 = graph.nodes["grid_100_r0_c0"]
    assert node_0.point.latitude == -65.0
    assert node_0.point.longitude == 10.0
    assert node_0.resolution_deg == 1.0


def test_aliases_and_closest_node_lookup():
    """Verify named targets (like S17 or Bharati) can be resolved to discrete grid cells."""
    bounds = BoundingBox(
        min_latitude=-70.0,
        max_latitude=-66.0,
        min_longitude=68.0,
        max_longitude=78.0,
    )
    aliases = {
        "S17": (-67.8, 70.0),
        "BHARATI": (-69.4, 76.2),
    }
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0, aliases=aliases)

    assert "S17" in graph.aliases
    s17_node_id = graph.aliases["S17"]
    assert graph.nodes[s17_node_id].alias == "S17"

    # Closest node lookup
    query_pt = GeoPoint(latitude=-67.75, longitude=70.1)
    found_id = graph.find_closest_node_id(query_pt)
    assert found_id == s17_node_id


def test_hard_constraints_land_and_depth():
    """Verify land/ice-shelf and shallow bathymetry under-keel clearance pruning."""
    bounds = BoundingBox(
        min_latitude=-75.0,
        max_latitude=-65.0,
        min_longitude=20.0,
        max_longitude=30.0,
    )
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0)
    vessel = VesselProfile(draft_m=8.5)

    graph.apply_hard_constraints(vessel=vessel)

    # South of -72S is land/ice-shelf in mock bathymetry
    for node in graph.nodes.values():
        if node.point.latitude <= -73.0:
            assert not node.is_navigable
            assert node.exclusion_reason in ("LAND_MASK", "ICE_SHELF", f"SHALLOW_DEPTH_{node.depth_m:.0f}m")


def test_avoidance_zone_pruning():
    """Verify nodes within an active avoidance zone are marked unnavigable."""
    bounds = BoundingBox(
        min_latitude=-56.0,
        max_latitude=-52.0,
        min_longitude=1.0,
        max_longitude=6.0,
    )
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0)
    vessel = VesselProfile()

    zone = AvoidanceZone(
        name="Bouvet Hazard Front",
        center=GeoPoint(latitude=-54.0, longitude=3.0),
        radius_km=60.0,
    )

    graph.apply_hard_constraints(vessel=vessel, avoidance_zones=[zone])

    # Node near (-54.0, 3.0) must be excluded
    hazard_node_id = graph.find_closest_node_id(GeoPoint(latitude=-54.0, longitude=3.0))
    assert not graph.nodes[hazard_node_id].is_navigable
    assert graph.nodes[hazard_node_id].exclusion_reason == "AVOIDANCE_ZONE"


def test_geodesic_8_neighbor_connectivity():
    """Verify 8-directional neighbor expansion with true Haversine distance and heading."""
    bounds = BoundingBox(
        min_latitude=-55.0,
        max_latitude=-50.0,
        min_longitude=20.0,
        max_longitude=25.0,
    )
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0)
    vessel = VesselProfile()
    graph.apply_hard_constraints(vessel=vessel)

    # Center node
    center_id = graph.find_closest_node_id(GeoPoint(latitude=-52.0, longitude=22.0))
    neighbors = graph.get_neighbors(center_id)

    # In open water, a center node should have 8 neighbors
    assert len(neighbors) == 8
    for n_id, dist_nm, heading_deg in neighbors:
        assert dist_nm > 0.0
        assert 0.0 <= heading_deg < 360.0


def test_to_environment_cell():
    """Verify conversion of node to complete EnvironmentCell schema."""
    bounds = BoundingBox(
        min_latitude=-60.0,
        max_latitude=-58.0,
        min_longitude=20.0,
        max_longitude=22.0,
    )
    graph = EnvironmentalGridGraph(bounds=bounds, resolution_deg=1.0)
    node_id = list(graph.nodes.keys())[0]

    t0 = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    cell = graph.to_environment_cell(node_id, t0)

    assert cell.cell_id == node_id
    assert cell.timestamp == t0
    assert cell.bathymetry_depth_m > 0
    assert cell.provenance == "MOCK / SYNTHETIC"
