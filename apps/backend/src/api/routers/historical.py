"""Historical replay and hindcast evaluation endpoints with temporal gating."""

from fastapi import APIRouter, Depends, status
from services.historical_service import (
    HistoricalService,
    HistoricalReplayRequest,
    HistoricalEvaluationResult,
)
from api.dependencies import get_historical_service

router = APIRouter(prefix="/historical", tags=["Historical Replay"])


@router.post("/evaluate", response_model=HistoricalEvaluationResult, status_code=status.HTTP_200_OK)
async def evaluate_historical(
    request: HistoricalReplayRequest,
    service: HistoricalService = Depends(get_historical_service),
) -> HistoricalEvaluationResult:
    """Evaluate route performance and forecast skill against historical data with strict temporal cutoff."""
    return service.evaluate_historical(request)
