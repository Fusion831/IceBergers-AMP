"""Route optimization, 4D validation, and alternative comparison endpoints."""

from typing import List
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, status
from domain.route import (
    RouteOptimizationRequest,
    RouteOptimizationResponse,
    RouteAlternative,
    RouteComparison,
)
from services.routing_service import RoutingService
from api.dependencies import get_routing_service

router = APIRouter(prefix="/routes", tags=["Routes"])


class RouteCompareRequest(BaseModel):
    route_ids: List[str]


@router.get("/canonical", response_model=RouteOptimizationResponse, status_code=status.HTTP_200_OK)
async def get_canonical_ncpor_routes(
    scenario: str = Query("historical_trend_normal", description="SIC scenario (historical_trend_normal, historical_trend_low_ice, historical_trend_high_ice, ice_knn)"),
    service: RoutingService = Depends(get_routing_service),
) -> RouteOptimizationResponse:
    """Retrieve the canonical NCPOR mission route alternatives (Cape Town -> Bharati -> Maitri -> Cape Town)."""
    return service.get_canonical_ncpor_routes(scenario=scenario)


@router.post("/optimize", response_model=RouteOptimizationResponse, status_code=status.HTTP_200_OK)
async def optimize_routes(
    request: RouteOptimizationRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteOptimizationResponse:
    """Generate 4 geometrically distinct route alternatives (Safest, Fastest, Fuel-Efficient, Balanced)."""
    return service.optimize_routes(request)


@router.get("/{id}", response_model=RouteAlternative)
async def get_route(
    id: str,
    service: RoutingService = Depends(get_routing_service),
) -> RouteAlternative:
    """Retrieve detailed geometry, 4D waypoints, and validated risk metrics for a route."""
    return service.get_route(id)


@router.post("/compare", response_model=RouteComparison)
async def compare_routes(
    body: RouteCompareRequest,
    service: RoutingService = Depends(get_routing_service),
) -> RouteComparison:
    """Compare multiple route alternatives side-by-side on duration, fuel, and risk exposure."""
    return service.compare_routes(body.route_ids)
