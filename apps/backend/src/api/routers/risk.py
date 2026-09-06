"""Composite risk field R(x,y,t) and point evaluation endpoints."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, Query, Body
from domain.coordinates import GeoPoint, BoundingBox
from domain.risk import RiskField, PointRiskQuery
from services.risk_service import RiskService
from api.dependencies import get_risk_service

router = APIRouter(prefix="/risk", tags=["Risk"])


@router.get("/map", response_model=RiskField)
async def get_risk_map(
    valid_time: Optional[datetime] = Query(None),
    horizon_days: int = Query(14, ge=0, le=90),
    min_lat: float = Query(-75.0),
    max_lat: float = Query(-55.0),
    min_lon: float = Query(0.0),
    max_lon: float = Query(80.0),
    service: RiskService = Depends(get_risk_service),
) -> RiskField:
    """Generate 2D composite risk field R(x,y,t) integrating sea ice, iceberg hazard, and storms."""
    target_time = valid_time or datetime.now(timezone.utc)
    bbox = BoundingBox(
        min_latitude=min_lat,
        max_latitude=max_lat,
        min_longitude=min_lon,
        max_longitude=max_lon,
    )
    return service.get_risk_field(
        valid_time=target_time,
        bbox=bbox,
        horizon_days=horizon_days,
    )


@router.post("/point", response_model=Dict[str, Any])
async def evaluate_point_risk(
    query: PointRiskQuery,
    service: RiskService = Depends(get_risk_service),
) -> Dict[str, Any]:
    """Evaluate composite risk and explainable factor attribution at a specific point and time."""
    return service.evaluate_point_risk(
        point=query.point,
        valid_time=query.valid_time,
        vessel=query.vessel_profile,
        weights=query.risk_weights,
    )
