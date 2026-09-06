"""Iceberg observations and Lagrangian drift trajectory ensemble endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from domain.coordinates import BoundingBox
from domain.iceberg import IcebergObservation, IcebergTrajectoryEnsemble
from services.iceberg_service import IcebergService
from api.dependencies import get_iceberg_service

router = APIRouter(prefix="/icebergs", tags=["Icebergs"])


@router.get("", response_model=List[IcebergObservation])
async def list_icebergs(
    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    service: IcebergService = Depends(get_iceberg_service),
) -> List[IcebergObservation]:
    """Retrieve active iceberg observations (NIC / SAR / Sentinel)."""
    bbox = None
    if all(v is not None for v in (min_lat, max_lat, min_lon, max_lon)):
        bbox = BoundingBox(
            min_latitude=min_lat,
            max_latitude=max_lat,
            min_longitude=min_lon,
            max_longitude=max_lon,
        )
    return service.list_observations(bbox=bbox)


@router.get("/{id}/trajectory", response_model=IcebergTrajectoryEnsemble)
async def get_iceberg_trajectory(
    id: str,
    forecast_days: int = Query(30, ge=1, le=90),
    ensemble_size: int = Query(50, ge=10, le=100),
    service: IcebergService = Depends(get_iceberg_service),
) -> IcebergTrajectoryEnsemble:
    """Compute 50-member Lagrangian stochastic drift trajectory ensemble with 50% & 90% corridors."""
    return service.get_trajectory_ensemble(
        iceberg_id=id,
        forecast_days=forecast_days,
        ensemble_size=ensemble_size,
    )
