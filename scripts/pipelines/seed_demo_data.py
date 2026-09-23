import sys
from pathlib import Path

# Add all package and app source directories to sys.path for standalone execution
ROOT = Path(__file__).resolve().parent.parent
for pkg_dir in (ROOT / "packages").glob("*/src"):
    if str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))
app_src = ROOT / "apps" / "backend" / "src"
if str(app_src) not in sys.path:
    sys.path.insert(0, str(app_src))

import asyncio
import logging
from datetime import datetime, timezone, timedelta

from domain.coordinates import GeoPoint
from domain.vessel import VesselProfile
from domain.mission import MissionCreate, PlanningWindow, MissionDestination, MissionPriorities, MissionTarget, AvoidanceZone
from domain.enums import MissionSeason, MissionTargetType
from services.mission_service import MissionService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_demo_data")


def seed() -> None:
    logger.info("Seeding AMIP POC demonstration data...")
    service = MissionService()

    now = datetime(2026, 1, 15, 0, 0, tzinfo=timezone.utc)
    vessel = VesselProfile()

    mission_dto = MissionCreate(
        name="45th Indian Scientific Expedition to Antarctica (ISEA-45)",
        expedition_code="ISEA-45-DEMO",
        season=MissionSeason.SUMMER_2026,
        description="Multi-target expedition from Cape Town to Bharati, Prydz Bay science site, Grid Cell S17, and Maitri.",
        vessel_profile=vessel,
        planning_window=PlanningWindow(
            earliest_departure=now,
            latest_departure=now + timedelta(days=10),
            latest_return=now + timedelta(days=65),
        ),
        destinations=[
            MissionDestination(
                station_name="Bharati",
                location=GeoPoint(latitude=-69.4072, longitude=76.1911),
                entry_corridor=GeoPoint(latitude=-67.5, longitude=76.0),
                min_stay_days=10,
                preferred_arrival=now + timedelta(days=18),
            ),
            MissionDestination(
                station_name="Maitri",
                location=GeoPoint(latitude=-70.7670, longitude=11.7330),
                entry_corridor=GeoPoint(latitude=-69.5, longitude=12.0),
                min_stay_days=14,
                preferred_arrival=now + timedelta(days=35),
            ),
        ],
        targets=[
            MissionTarget(
                name="Bharati Station Logistics Point",
                target_type=MissionTargetType.STATION,
                location=GeoPoint(latitude=-69.4072, longitude=76.1911, name="Bharati Station"),
                dwell_hours=48.0,
                sequence_order=1,
            ),
            MissionTarget(
                name="Prydz Bay Science Survey",
                target_type=MissionTargetType.SCIENCE_SITE,
                location=GeoPoint(latitude=-68.2, longitude=74.5, name="Science Area Alpha"),
                dwell_hours=24.0,
                sequence_order=2,
            ),
            MissionTarget(
                name="Satellite Sea-Ice Ground Truth Cell S17",
                target_type=MissionTargetType.GRID_CELL,
                grid_cell_id="S17",
                location=GeoPoint(latitude=-67.8, longitude=70.0, name="Grid Cell S17"),
                dwell_hours=12.0,
                sequence_order=3,
            ),
            MissionTarget(
                name="Maitri Station Access Corridor",
                target_type=MissionTargetType.STATION,
                location=GeoPoint(latitude=-70.7670, longitude=11.7330, name="Maitri Station"),
                dwell_hours=72.0,
                sequence_order=4,
            ),
        ],
        avoidance_zones=[
            AvoidanceZone(
                name="Bouvet Iceberg Calving Hazard Zone",
                center=GeoPoint(latitude=-54.4, longitude=3.4),
                radius_km=45.0,
                reason="Active tabular iceberg calving front and grounding shoals",
            )
        ],
        priorities=MissionPriorities(safety=0.40, fuel=0.30, time=0.20, science=0.10),
    )

    mission = service.create_mission(mission_dto)
    logger.info("Created demo mission: %s (%s)", mission.id, mission.name)

    logger.info("Executing end-to-end mission analysis pipeline...")
    result = service.analyze_mission(mission.id)
    logger.info(
        "Analysis complete! Generated %d distinct route alternatives. Recommended route: %s",
        len(result["routes"]),
        result["recommended_route_id"],
    )
    for r in result["routes"]:
        logger.info(
            "  -> Objective: %-15s | Distance: %6.1f NM | Duration: %5.1f hrs | Fuel: %5.1f t | Mean Risk: %.3f",
            r["objective"],
            r["metrics"]["distance_nm"],
            r["metrics"]["duration_hours"],
            r["metrics"]["fuel_consumption_tonnes"],
            r["metrics"]["mean_risk"],
        )

    logger.info("Demonstration data seeded successfully.")


if __name__ == "__main__":
    seed()
