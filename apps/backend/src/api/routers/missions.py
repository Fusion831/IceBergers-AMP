"""Mission management and orchestration endpoints."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from domain.mission import Mission, MissionCreate
from services.mission_service import MissionService
from api.dependencies import get_mission_service

router = APIRouter(prefix="/missions", tags=["Missions"])


@router.post("", response_model=Mission, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreate,
    service: MissionService = Depends(get_mission_service),
) -> Mission:
    """Register a new Antarctic expedition mission."""
    return service.create_mission(payload)


@router.get("", response_model=List[Mission])
async def list_missions(
    service: MissionService = Depends(get_mission_service),
) -> List[Mission]:
    """List all registered expedition missions."""
    return service.list_missions()


@router.get("/{id}", response_model=Mission)
async def get_mission(
    id: str,
    service: MissionService = Depends(get_mission_service),
) -> Mission:
    """Retrieve detailed metadata for a specific mission."""
    return service.get_mission(id)


@router.post("/{id}/analyze", response_model=Dict[str, Any])
async def analyze_mission(
    id: str,
    service: MissionService = Depends(get_mission_service),
) -> Dict[str, Any]:
    """Execute the end-to-end AMIP pipeline for this mission, generating 4 route alternatives."""
    return service.analyze_mission(id)


@router.get("/{id}/analysis", response_model=Dict[str, Any])
async def get_mission_analysis(
    id: str,
    service: MissionService = Depends(get_mission_service),
) -> Dict[str, Any]:
    """Retrieve cached mission analysis, station windows, and route alternatives."""
    return service.get_mission_analysis(id)
