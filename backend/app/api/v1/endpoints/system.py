"""System Endpoints.

REST router for querying platform information and resource monitoring stats.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import SystemStatsResponse
from app.di.container import get_system_service

if TYPE_CHECKING:
    from app.services.system_service import SystemService

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/info", response_model=SystemStatsResponse)
async def get_system_info(
    service: SystemService = Depends(get_system_service),
) -> SystemStatsResponse:
    """Retrieve active platform specs and resource consumption stats (CPU, RAM, GPU, Disk)."""
    try:
        stats = service.get_system_stats()
        return SystemStatsResponse.model_validate(stats)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed retrieving system info: {e}",
        ) from e
