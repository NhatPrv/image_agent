"""API v1 router definition.

Combines routers from various domains into a single API surface.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


# ─── System / Health check endpoint ───


@router.get("/system/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint to verify backend status."""
    return {"status": "ok", "message": "Image Agent Backend is running."}
