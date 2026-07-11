"""API v1 router definition.

Combines routers from various domains into a single API surface.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    downloads,
    generations,
    models,
    queue,
    settings,
    system,
)

router = APIRouter()

# ─── System / Health check endpoint ───


@router.get("/system/health", tags=["System"])
async def health_check() -> dict[str, str]:
    """Basic health check endpoint to verify backend status."""
    return {"status": "ok", "message": "Image Agent Backend is running."}


# ─── Include sub-routers ───
router.include_router(models.router)
router.include_router(generations.router)
router.include_router(queue.router)
router.include_router(settings.router)
router.include_router(system.router)
router.include_router(downloads.router)
# Note: websocket.router is mounted directly at root /ws in main.py
