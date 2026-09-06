"""Environmental physical layers endpoints (SST, wind, ocean currents, waves, bathymetry)."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from domain.coordinates import GeoPoint, BoundingBox
from domain.environment import GridSlice, PointEnvironment
from services.environment_service import EnvironmentService
from api.dependencies import get_env_service

router = APIRouter(prefix="/environment", tags=["Environment"])


@router.get("/slice", response_model=GridSlice)
async def get_environment_slice(
    valid_time: Optional[datetime] = Query(None, description="ISO valid time for environment"),
    min_lat: float = Query(-75.0),
    max_lat: float = Query(-50.0),
    min_lon: float = Query(0.0),
    max_lon: float = Query(80.0),
    service: EnvironmentService = Depends(get_env_service),
) -> GridSlice:
    """Retrieve 2D physical ocean and atmospheric grid slice."""
    target_time = valid_time or datetime.now(timezone.utc)
    bbox = BoundingBox(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon,
    )
    return service.get_slice(valid_time=target_time, bbox=bbox)


@router.get("/point", response_model=PointEnvironment)
async def get_environment_point(
    lat: float = Query(..., description="Latitude (-90 to 90)"),
    lon: float = Query(..., description="Longitude (-180 to 180)"),
    valid_time: Optional[datetime] = Query(None),
    service: EnvironmentService = Depends(get_env_service),
) -> PointEnvironment:
    """Retrieve environmental conditions at a single geographic point."""
    target_time = valid_time or datetime.now(timezone.utc)
    pt = GeoPoint(latitude=lat, longitude=lon)
    return service.get_point(point=pt, valid_time=target_time)
