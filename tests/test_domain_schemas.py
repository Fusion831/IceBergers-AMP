"""Unit tests for domain schemas and coordinates."""

import pytest
from datetime import datetime, timezone
from domain.coordinates import GeoPoint, BoundingBox, GridSpec
from domain.vessel import VesselProfile
from domain.enums import IceClass, RouteObjective
from domain.mission import MissionCreate


def test_geopoint_validation():
    p = GeoPoint(latitude=-69.4, longitude=76.2)
    assert p.latitude == -69.4
    assert p.longitude == 76.2

    with pytest.raises(ValueError):
        GeoPoint(latitude=95.0, longitude=0.0)

    with pytest.raises(ValueError):
        GeoPoint(latitude=-70.0, longitude=200.0)


def test_bounding_box_containment():
    bbox = BoundingBox(
        min_latitude=-75.0,
        max_latitude=-50.0,
        min_longitude=0.0,
        max_longitude=90.0,
    )
    inside_pt = GeoPoint(latitude=-65.0, longitude=45.0)
    outside_pt = GeoPoint(latitude=-40.0, longitude=45.0)

    assert bbox.contains(inside_pt) is True
    assert bbox.contains(outside_pt) is False


def test_vessel_profile_defaults(sample_vessel: VesselProfile):
    assert sample_vessel.name == "ORV Sagar Kanya"
    assert sample_vessel.ice_class == IceClass.ICE_CLASS_1B
    assert sample_vessel.draft_meters == 5.6
    assert sample_vessel.safe_clearance_depth_m == 8.6  # 5.6 + 3.0 margin
    assert sample_vessel.max_speed_knots == 14.0


def test_mission_create_schema(sample_mission_create: MissionCreate):
    assert sample_mission_create.expedition_code == "ISEA-45"
    assert len(sample_mission_create.destinations) == 2
    assert sample_mission_create.destinations[0].station_name == "Bharati"
    assert sample_mission_create.priorities.safety == 0.45
