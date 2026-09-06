"""Sea-ice concentration, uncertainty, and baseline benchmark endpoints."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query
from domain.coordinates import BoundingBox
from domain.sea_ice import SeaIcePredictionResult
from services.sea_ice_service import SeaIceService
from api.dependencies import get_sea_ice_service

router = APIRouter(prefix="/sea-ice", tags=["Sea Ice"])


@router.get("/forecast", response_model=SeaIcePredictionResult)
async def get_sea_ice_forecast(
    reference_time: Optional[datetime] = Query(None),
    horizon_days: int = Query(14, ge=0, le=90, description="Lead time in days: 0, 7, 14, 30, 60, 90"),
    min_lat: float = Query(-75.0),
    max_lat: float = Query(-55.0),
    min_lon: float = Query(0.0),
    max_lon: float = Query(80.0),
    model_id: Optional[str] = Query(None),
    service: SeaIceService = Depends(get_sea_ice_service),
) -> SeaIcePredictionResult:
    """Produce deterministic sea-ice concentration and uncertainty grid."""
    ref_time = reference_time or datetime.now(timezone.utc)
    bbox = BoundingBox(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon,
    )
    return service.get_forecast(
        reference_time=ref_time,
        horizon_days=horizon_days,
        bbox=bbox,
        model_id=model_id,
    )


@router.get("/baselines", response_model=Dict[str, Any])
async def get_sea_ice_baselines(
    reference_time: Optional[datetime] = Query(None),
    horizon_days: int = Query(14, ge=0, le=90),
    min_lat: float = Query(-75.0),
    max_lat: float = Query(-55.0),
    min_lon: float = Query(0.0),
    max_lon: float = Query(80.0),
    service: SeaIceService = Depends(get_sea_ice_service),
) -> Dict[str, Any]:
    """Compare ML sea-ice model with Persistence and Climatology baselines (MAE, RMSE, Brier score)."""
    ref_time = reference_time or datetime.now(timezone.utc)
    bbox = BoundingBox(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon,
    )
    return service.get_baseline_comparison(
        reference_time=ref_time,
        horizon_days=horizon_days,
        bbox=bbox,
    )
