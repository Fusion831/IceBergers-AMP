"""Antarctic station accessibility windows and ice barrier analysis endpoints."""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from domain.analysis import StationAccessibilityWindow
from services.analysis_service import AnalysisService
from api.dependencies import get_analysis_service

router = APIRouter(prefix="/stations", tags=["Stations"])


@router.get("/accessibility", response_model=StationAccessibilityWindow)
async def get_station_accessibility(
    station_name: str = Query("Bharati", description="Name of Antarctic station (Bharati, Maitri, Syowa, etc.)"),
    reference_time: Optional[datetime] = Query(None),
    service: AnalysisService = Depends(get_analysis_service),
) -> StationAccessibilityWindow:
    """Analyze temporal accessibility windows and ice barrier penetration across 0 to 90 days lead time."""
    ref_time = reference_time or datetime.now(timezone.utc)
    return service.get_station_accessibility(
        station_name=station_name,
        reference_time=ref_time,
    )
