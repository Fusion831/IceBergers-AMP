"""RFC 7807 problem details error handler for FastAPI."""

import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from core.errors import AMIPBaseError

logger = logging.getLogger(__name__)


async def amip_error_handler(request: Request, exc: AMIPBaseError) -> JSONResponse:
    """Catches custom domain AMIP exceptions and returns RFC 7807 JSON."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"Content-Type": "application/problem+json"},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catches unexpected exceptions with 500 status."""
    logger.exception("Unhandled server error: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "type": "urn:amip:error:internal",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred while processing the mission request.",
            "instance": request.url.path,
        },
        headers={"Content-Type": "application/problem+json"},
    )
