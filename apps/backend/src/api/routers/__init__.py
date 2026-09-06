"""Routers package exporting API routes."""

from api.routers.health import router as health_router
from api.routers.missions import router as missions_router
from api.routers.environment import router as environment_router
from api.routers.sea_ice import router as sea_ice_router
from api.routers.icebergs import router as icebergs_router
from api.routers.risk import router as risk_router
from api.routers.routes import router as routes_router
from api.routers.stations import router as stations_router
from api.routers.historical import router as historical_router
from api.routers.jobs import router as jobs_router

__all__ = [
    "health_router",
    "missions_router",
    "environment_router",
    "sea_ice_router",
    "icebergs_router",
    "risk_router",
    "routes_router",
    "stations_router",
    "historical_router",
    "jobs_router",
]
