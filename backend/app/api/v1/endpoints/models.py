"""Models Endpoints.

REST router for model scanning, list querying, and GPU VRAM loading state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import ModelInfoResponse, ModelLoadRequest
from app.di.container import get_model_service

if TYPE_CHECKING:
    from app.services.model_service import ModelService

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=list[ModelInfoResponse])
async def list_models(
    service: ModelService = Depends(get_model_service),
) -> list[ModelInfoResponse]:
    """Retrieve list of all registered models from the database."""
    return await service.get_all_models()


@router.post("/scan", response_model=list[ModelInfoResponse])
async def scan_models(
    service: ModelService = Depends(get_model_service),
) -> list[ModelInfoResponse]:
    """Trigger recursive model folder scan and register new models."""
    try:
        return await service.scan_and_register_models()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scanning failed: {e}",
        ) from e


@router.get("/active", response_model=ModelInfoResponse | None)
async def get_active_model(
    service: ModelService = Depends(get_model_service),
) -> ModelInfoResponse | None:
    """Retrieve details of the active model currently residing in memory."""
    return await service.get_active_model()


@router.post("/load", status_code=status.HTTP_200_OK)
async def load_model(
    payload: ModelLoadRequest,
    service: ModelService = Depends(get_model_service),
) -> dict[str, str]:
    """Load a specific model into GPU VRAM."""
    try:
        await service.load_model(payload.model_id)
        return {"status": "success", "message": f"Model '{payload.model_id}' loaded."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loading failed: {e}",
        ) from e


@router.post("/unload", status_code=status.HTTP_200_OK)
async def unload_model(
    service: ModelService = Depends(get_model_service),
) -> dict[str, str]:
    """Unload active model and purge GPU CUDA memory block cache."""
    try:
        await service.unload_model()
        return {"status": "success", "message": "Model unloaded."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unloading failed: {e}",
        ) from e
