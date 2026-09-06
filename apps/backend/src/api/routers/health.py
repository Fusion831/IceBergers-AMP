"""Health check and service status endpoints."""

from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter
from core.config import settings

router = APIRouter(tags=["System"])


@router.get("/health", response_model=Dict[str, Any])
async def get_health() -> Dict[str, Any]:
    """System health status, version, mock mode, and timestamp."""
    return {
        "status": "healthy",
        "service": "AMIP Backend POC",
        "version": settings.app_version,
        "environment": settings.environment,
        "mock_mode": settings.mock_mode,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "sea_ice_model": "AMIP-Mock-UNet-v1",
            "iceberg_engine": "MockLagrangianDrift-50",
            "risk_engine": "CompositeRisk-v1",
            "route_optimizer": "MockRouteOptimizer-4Way",
        },
    }
