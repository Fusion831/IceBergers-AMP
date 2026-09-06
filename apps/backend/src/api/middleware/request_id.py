"""Request ID and timing middleware for structured tracing."""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response
import structlog


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assigns unique X-Request-ID to each incoming request and measures response latency."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=req_id, path=request.url.path, method=request.method)

        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = str(process_time_ms)
        return response
