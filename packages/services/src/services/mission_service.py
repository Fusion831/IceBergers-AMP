"""Mission Service orchestrating the complete AMIP pipeline: Environment -> Sea-Ice -> Iceberg -> Risk -> Routes -> 4D Validation -> Analysis."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from domain.coordinates import GeoPoint
from domain.mission import Mission, MissionCreate
from domain.vessel import VesselProfile
from domain.enums import MissionStatus, RouteObjective
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
)
from domain.analysis import MissionAnalysisResult
from domain.provenance import ModelRunRecord, DatasetProvenance
from core.errors import NotFoundError, ValidationError
from services.environment_service import EnvironmentService
from services.sea_ice_service import SeaIceService
from services.iceberg_service import IcebergService
from services.risk_service import RiskService
from services.routing_service import RoutingService
from services.analysis_service import AnalysisService

logger = logging.getLogger(__name__)


class MissionService:
    """Coordinates the end-to-end Antarctic mission intelligence workflow."""

    def __init__(
        self,
        env_service: Optional[EnvironmentService] = None,
        sea_ice_service: Optional[SeaIceService] = None,
        iceberg_service: Optional[IcebergService] = None,
        risk_service: Optional[RiskService] = None,
        routing_service: Optional[RoutingService] = None,
        analysis_service: Optional[AnalysisService] = None,
    ) -> None:
        self.env_service = env_service or EnvironmentService()
        self.sea_ice_service = sea_ice_service or SeaIceService()
        self.iceberg_service = iceberg_service or IcebergService()
        self.risk_service = risk_service or RiskService()
        self.routing_service = routing_service or RoutingService()
        self.analysis_service = analysis_service or AnalysisService()

        # In-memory storage for POC (sync with DB where active)
        self._missions: Dict[str, Mission] = {}
        self._analyses: Dict[str, MissionAnalysisResult] = {}
        self._mission_routes: Dict[str, List[RouteAlternative]] = {}
        self._provenance_records: Dict[str, List[ModelRunRecord]] = {}

    def create_mission(self, create_dto: MissionCreate) -> Mission:
        """Create a new Antarctic expedition mission."""
        mission_id = f"msn-{uuid.uuid4().hex[:8]}"
        mission = Mission(
            id=mission_id,
            name=create_dto.name,
            expedition_code=create_dto.expedition_code,
            season=create_dto.season,
            description=create_dto.description,
            vessel_profile=create_dto.vessel_profile or VesselProfile(),
            planning_window=create_dto.planning_window,
            destinations=create_dto.destinations,
            targets=create_dto.targets,
            avoidance_zones=create_dto.avoidance_zones,
            priorities=create_dto.priorities,
            status=MissionStatus.DRAFT,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._missions[mission_id] = mission
        logger.info(f"Created mission {mission_id}: {mission.name}")
        return mission

    def get_mission(self, mission_id: str) -> Mission:
        """Retrieve mission details by ID."""
        if mission_id not in self._missions:
            raise NotFoundError(f"Mission '{mission_id}' not found.")
        return self._missions[mission_id]

    def list_missions(self) -> List[Mission]:
        """List all registered missions."""
        return list(self._missions.values())

    def analyze_mission(self, mission_id: str) -> Dict[str, Any]:
        """Executes the complete AMIP pipeline synchronously for the mission."""
        mission = self.get_mission(mission_id)
        mission.status = MissionStatus.ANALYZING
        self._missions[mission_id] = mission

        vessel = mission.vessel_profile
        departure_time = mission.planning_window.earliest_departure
        primary_dest = mission.destinations[0]

        # 1. Environment & Risk are computed inside routing_service and analysis_service
        # 2. Run Route Optimization across 5 objectives: SHORTEST, FASTEST, SAFEST, FUEL_EFFICIENT, BALANCED
        opt_request = RouteOptimizationRequest(
            origin=mission.origin or primary_dest.entry_corridor,
            destination=primary_dest.location,
            departure_time=departure_time,
            vessel_profile=vessel,
            targets=mission.targets,
            avoidance_zones=mission.avoidance_zones,
            risk_weights=None,
            objectives=[
                RouteObjective.SHORTEST,
                RouteObjective.FASTEST,
                RouteObjective.SAFEST,
                RouteObjective.FUEL_EFFICIENT,
                RouteObjective.BALANCED,
            ],
        )

        routes_resp = self.routing_service.optimize_routes(opt_request)
        self._mission_routes[mission_id] = routes_resp.routes

        # 3. Station accessibility & mission feasibility analysis
        analysis_result = self.analysis_service.analyze_mission(mission, vessel)
        self._analyses[mission_id] = analysis_result

        # 4. Record provenance
        run_record = ModelRunRecord(
            run_id=f"run-{uuid.uuid4().hex[:8]}",
            mission_id=mission_id,
            model_id="AMIP-Mock-Pipeline-v1",
            model_version="1.0.0-poc",
            parameters={
                "departure_time": departure_time.isoformat(),
                "destinations": [d.station_name for d in mission.destinations],
                "vessel": vessel.name,
            },
            datasets=[
                DatasetProvenance(
                    dataset_id="copernicus-seaice-poc",
                    source="OSI-SAF / AMSR2 Mock",
                    version="2026.1",
                    coverage_start=departure_time - timedelta(days=30),
                    coverage_end=departure_time + timedelta(days=90),
                )
            ],
            executed_at=datetime.now(timezone.utc),
            execution_duration_seconds=1.2,
            git_commit="HEAD",
        )
        self._provenance_records.setdefault(mission_id, []).append(run_record)

        mission.status = MissionStatus.ANALYZED
        mission.updated_at = datetime.now(timezone.utc)
        self._missions[mission_id] = mission

        return {
            "mission_id": mission_id,
            "status": mission.status.value,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "analysis": analysis_result.model_dump(),
            "routes": [r.model_dump() for r in routes_resp.routes],
            "recommended_route_id": routes_resp.recommended_route_id,
            "provenance": run_record.model_dump(),
        }

    def get_mission_analysis(self, mission_id: str) -> Dict[str, Any]:
        """Fetch previously computed mission analysis and route alternatives."""
        mission = self.get_mission(mission_id)
        if mission_id not in self._analyses:
            raise NotFoundError(f"No analysis found for mission '{mission_id}'. Please call /analyze first.")

        analysis = self._analyses[mission_id]
        routes = self._mission_routes.get(mission_id, [])

        return {
            "mission_id": mission_id,
            "status": mission.status.value,
            "analysis": analysis.model_dump(),
            "routes": [r.model_dump() for r in routes],
            "provenance": [p.model_dump() for p in self._provenance_records.get(mission_id, [])],
        }
