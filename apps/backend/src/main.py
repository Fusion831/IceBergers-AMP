"""Antarctic Mission Intelligence Platform (AMIP) FastAPI Application."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from core.config import settings
from core.logging import setup_logging
from core.database import init_db
from core.errors import AMIPBaseError
from api.middleware.request_id import RequestIdMiddleware
from api.middleware.error_handler import amip_error_handler, unhandled_exception_handler
from api.routers import (
    health_router,
    missions_router,
    environment_router,
    sea_ice_router,
    icebergs_router,
    risk_router,
    routes_router,
    stations_router,
    historical_router,
    jobs_router,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: initialize structured logging, database tables, and warm mocks."""
    setup_logging(log_level=settings.log_level, json_format=not settings.debug)
    logger.info(
        "Starting AMIP Backend POC (v%s, mock_mode=%s, env=%s)",
        settings.app_version,
        settings.mock_mode,
        settings.environment,
    )
    # Initialize database tables asynchronously
    try:
        await init_db()
        logger.info("Database schema initialized successfully.")
    except Exception as exc:
        logger.warning("Database initialization warning (will use in-memory/mock state): %s", exc)

    yield

    logger.info("Shutting down AMIP Backend POC.")


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Antarctic Mission Intelligence Platform (AMIP) API",
        description=(
            "Spatiotemporal risk-aware route optimization, sea-ice forecasting, and "
            "decision support platform for Indian Antarctic expeditions (NCPOR / SIH 2026)."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # Middlewares
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestIdMiddleware)

    # Exception handlers (RFC 7807 problem details)
    app.add_exception_handler(AMIPBaseError, amip_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # API Routers under /api/v1
    prefix = "/api/v1"
    app.include_router(health_router, prefix=prefix)
    app.include_router(missions_router, prefix=prefix)
    app.include_router(jobs_router, prefix=prefix)
    app.include_router(environment_router, prefix=prefix)
    app.include_router(sea_ice_router, prefix=prefix)
    app.include_router(icebergs_router, prefix=prefix)
    app.include_router(risk_router, prefix=prefix)
    app.include_router(routes_router, prefix=prefix)
    app.include_router(stations_router, prefix=prefix)
    app.include_router(historical_router, prefix=prefix)

    @app.get("/", include_in_schema=False)
    async def root_redirect() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.debug)
