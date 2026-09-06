"""End-to-End integration test for complete AMIP expedition mission workflow."""

import pytest
from datetime import datetime, timezone
from domain.mission import MissionCreate
from domain.enums import MissionStatus, RouteObjective
from services.mission_service import MissionService


def test_complete_mission_lifecycle_e2e(sample_mission_create: MissionCreate):
    """Critical E2E Test:
    Create mission -> Analyze mission -> Verify 4 distinct routes ->
    Verify risk is present -> Verify metrics -> Verify provenance.
    """
    mission_service = MissionService()

    # 1. Create Mission
    mission = mission_service.create_mission(sample_mission_create)
    assert mission.id.startswith("msn-")
    assert mission.status == MissionStatus.DRAFT
    assert len(mission.destinations) == 2

    # 2. Analyze Mission (orchestrates the complete pipeline)
    analysis_resp = mission_service.analyze_mission(mission.id)
    assert analysis_resp["status"] == MissionStatus.ANALYZED.value
    assert "routes" in analysis_resp
    assert len(analysis_resp["routes"]) == 4

    # 3. Verify 4 distinct route alternatives
    routes = analysis_resp["routes"]
    objectives_found = {r["objective"] for r in routes}
    assert RouteObjective.SAFEST.value in objectives_found
    assert RouteObjective.FASTEST.value in objectives_found
    assert RouteObjective.FUEL_EFFICIENT.value in objectives_found
    assert RouteObjective.BALANCED.value in objectives_found

    # 4. Verify route geometries differ
    geom_safest = [(wp["point"]["latitude"], wp["point"]["longitude"]) for wp in routes[0]["waypoints"]]
    geom_fastest = [(wp["point"]["latitude"], wp["point"]["longitude"]) for wp in routes[1]["waypoints"]]
    assert geom_safest != geom_fastest

    # 5. Verify risk and fuel metrics are present and valid
    for r in routes:
        metrics = r["metrics"]
        assert metrics["distance_nm"] > 100.0
        assert metrics["duration_hours"] > 10.0
        assert metrics["fuel_consumption_tonnes"] > 5.0
        assert 0.0 <= metrics["mean_risk"] <= 1.0
        assert 0.0 <= metrics["max_risk"] <= 1.0
        assert "waypoint_risks" in metrics
        assert len(metrics["waypoint_risks"]) == len(r["waypoints"])

    # 6. Verify station accessibility windows
    analysis_data = analysis_resp["analysis"]
    assert "station_windows" in analysis_data
    assert len(analysis_data["station_windows"]) == 2
    assert analysis_data["overall_accessibility_score"] > 0.0
    assert len(analysis_data["operational_recommendations"]) > 0

    # 7. Verify provenance
    prov = analysis_resp["provenance"]
    assert prov["model_id"] == "AMIP-Mock-Pipeline-v1"
    assert prov["mission_id"] == mission.id
    assert len(prov["datasets"]) > 0

    # 8. Verify get_mission_analysis retrieval
    cached = mission_service.get_mission_analysis(mission.id)
    assert cached["mission_id"] == mission.id
    assert len(cached["routes"]) == 4
