"""Pytest configuration and global fixtures for AMIP backend tests."""

import sys
from pathlib import Path
import pytest
from datetime import datetime, timezone, timedelta

# Add all package source roots and app source root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent

package_paths = [
    BASE_DIR / "packages" / "domain" / "src",
    BASE_DIR / "packages" / "core" / "src",
    BASE_DIR / "packages" / "data_access" / "src",
    BASE_DIR / "packages" / "models" / "src",
    BASE_DIR / "packages" / "iceberg_physics" / "src",
    BASE_DIR / "packages" / "risk_engine" / "src",
    BASE_DIR / "packages" / "routing" / "src",
    BASE_DIR / "packages" / "services" / "src",
    BASE_DIR / "apps" / "backend" / "src",
]

for p in package_paths:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from domain.coordinates import GeoPoint, BoundingBox
from domain.vessel import VesselProfile
from domain.mission import MissionCreate, PlanningWindow, MissionDestination, MissionPriorities
from domain.enums import IceClass, MissionSeason


@pytest.fixture
def sample_vessel() -> VesselProfile:
    """Default ORV Sagar Kanya vessel profile."""
    return VesselProfile(
        name="ORV Sagar Kanya",
        ice_class=IceClass.ICE_CLASS_1B,
        max_speed_knots=14.0,
        service_speed_knots=11.0,
        draft_meters=5.6,
        length_meters=100.3,
        beam_meters=16.4,
        displacement_tonnes=4192.0,
        ice_clearance_depth_margin_m=3.0,
    )


@pytest.fixture
def sample_mission_create(sample_vessel: VesselProfile) -> MissionCreate:
    """Sample Indian Antarctic expedition mission create payload."""
    now = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    return MissionCreate(
        name="45th Indian Scientific Expedition to Antarctica",
        expedition_code="ISEA-45",
        season=MissionSeason.SUMMER_2026,
        description="Annual resupply and scientific research mission to Bharati and Maitri stations.",
        vessel_profile=sample_vessel,
        planning_window=PlanningWindow(
            earliest_departure=now,
            latest_departure=now + timedelta(days=10),
            latest_return=now + timedelta(days=60),
        ),
        destinations=[
            MissionDestination(
                station_name="Bharati",
                location=GeoPoint(latitude=-69.4072, longitude=76.1911),
                entry_corridor=GeoPoint(latitude=-67.5, longitude=76.0),
                min_stay_days=7,
                preferred_arrival=now + timedelta(days=16),
            ),
            MissionDestination(
                station_name="Maitri",
                location=GeoPoint(latitude=-70.7670, longitude=11.7330),
                entry_corridor=GeoPoint(latitude=-69.5, longitude=12.0),
                min_stay_days=10,
                preferred_arrival=now + timedelta(days=30),
            ),
        ],
        priorities=MissionPriorities(safety=0.45, fuel=0.25, time=0.20, science=0.10),
    )
