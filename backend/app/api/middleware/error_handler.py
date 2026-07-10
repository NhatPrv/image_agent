"""Global error handler middleware.

Intercepts custom ImageAgentErrors and returns structured JSON responses.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi.responses import JSONResponse

from app.core.exceptions.base import ImageAgentError

if TYPE_CHECKING:
    from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)


def setup_error_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application instance.

    Args:
        app: The target FastAPI application.
    """

    @app.exception_handler(ImageAgentError)
    async def image_agent_exception_handler(
        _request: Request,
        exc: ImageAgentError,
    ) -> JSONResponse:
        """Handle custom application-specific errors."""
        logger.warning(
            "Application error [%s]: %s (details: %s)",
            exc.error_code,
            exc.message,
            exc.details,
        )
        return JSONResponse(
            status_code=400,
            content=exc.to_dict(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Fallback handler for uncaught python errors."""
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred on the server.",
                    "details": {"original_error": str(exc)},
                }
            },
        )
