"""Request logging middleware.

Logs request information and duration for API performance tracking.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from fastapi import Request, Response
    from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI Middleware to log incoming HTTP requests and responses."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        start_time = time.perf_counter()

        # Log request receipt
        method = request.method
        url = request.url.path
        logger.debug("Received request: %s %s", method, url)

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000.0

            # Log response stats
            status_code = response.status_code
            log_level = logging.INFO if status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                "Request completed: %s %s %d (duration: %.2fms)",
                method,
                url,
                status_code,
                duration_ms,
            )
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error(
                "Request failed: %s %s (duration: %.2fms) │ Error: %s",
                method,
                url,
                duration_ms,
                str(e),
                exc_info=True,
            )
            raise e
