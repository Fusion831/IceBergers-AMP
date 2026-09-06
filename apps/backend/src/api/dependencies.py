"""FastAPI dependency injection providers for AMIP services."""

from __future__ import annotations

from typing import Generator
from functools import lru_cache

from services.environment_service import EnvironmentService
from services.sea_ice_service import SeaIceService
from services.iceberg_service import IcebergService
from services.risk_service import RiskService
from services.routing_service import RoutingService
from services.analysis_service import AnalysisService
from services.historical_service import HistoricalService
from services.mission_service import MissionService


@lru_cache()
def get_env_service() -> EnvironmentService:
    return EnvironmentService()


@lru_cache()
def get_sea_ice_service() -> SeaIceService:
    return SeaIceService()


@lru_cache()
def get_iceberg_service() -> IcebergService:
    return IcebergService()


@lru_cache()
def get_risk_service() -> RiskService:
    return RiskService(
        env_service=get_env_service(),
        sea_ice_service=get_sea_ice_service(),
        iceberg_service=get_iceberg_service(),
    )


@lru_cache()
def get_routing_service() -> RoutingService:
    return RoutingService(risk_service=get_risk_service())


@lru_cache()
def get_analysis_service() -> AnalysisService:
    return AnalysisService(
        risk_service=get_risk_service(),
        sea_ice_service=get_sea_ice_service(),
    )


@lru_cache()
def get_historical_service() -> HistoricalService:
    return HistoricalService(
        sea_ice_service=get_sea_ice_service(),
        iceberg_service=get_iceberg_service(),
        routing_service=get_routing_service(),
    )


@lru_cache()
def get_mission_service() -> MissionService:
    return MissionService(
        env_service=get_env_service(),
        sea_ice_service=get_sea_ice_service(),
        iceberg_service=get_iceberg_service(),
        risk_service=get_risk_service(),
        routing_service=get_routing_service(),
        analysis_service=get_analysis_service(),
    )
