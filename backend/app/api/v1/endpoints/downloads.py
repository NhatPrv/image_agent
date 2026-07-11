"""Download API endpoints router.

Handles starting, cancel, and status queries for active model downloads.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.di.container import get_download_service

if TYPE_CHECKING:
    from app.services.download_service import DownloadService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])


class DownloadRequest(BaseModel):
    """Schema for requesting a new model asset download."""

    url: str = Field(..., description="The direct URL link to download from HuggingFace/CivitAI.")
    filename: str = Field(
        ...,
        description="The target output filename (e.g. realisticVision_v60.safetensors).",
    )
    component_type: str = Field(
        "checkpoint",
        description="The type of model component (checkpoint, lora, vae, controlnet).",
    )


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_download(
    request: DownloadRequest,
    download_service: DownloadService = Depends(get_download_service),
) -> dict:
    """Submit a download request to run in the background."""
    try:
        return await download_service.start_download(
            url=request.url,
            filename=request.filename,
            component_type=request.component_type,
        )
    except Exception as e:
        logger.exception("Failed to start download.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit download: {e!s}",
        ) from e


@router.get("", response_model=list[dict])
async def list_downloads(
    download_service: DownloadService = Depends(get_download_service),
) -> list[dict]:
    """Retrieve all active and finished download tasks."""
    return download_service.get_all_tasks()


@router.get("/{task_id}", response_model=dict)
async def get_download_status(
    task_id: str,
    download_service: DownloadService = Depends(get_download_service),
) -> dict:
    """Get status of a specific download task."""
    task = download_service.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Download task '{task_id}' not found.",
        )
    return task


@router.post("/{task_id}/cancel", response_model=dict)
async def cancel_download_task(
    task_id: str,
    download_service: DownloadService = Depends(get_download_service),
) -> dict:
    """Request immediate cancellation of a running download task."""
    cancelled = await download_service.cancel_download(task_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active download task '{task_id}' not found or cannot be cancelled.",
        )
    return {"status": "cancelled", "task_id": task_id}
