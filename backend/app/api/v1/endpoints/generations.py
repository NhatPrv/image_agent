"""Generations Endpoints.

REST router for submitting generations and retrieving historical data records.
"""

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.schemas import GenerateRequest, GenerationResponse
from app.core.entities.generation import GenerationParams
from app.di.container import get_generation_service

if TYPE_CHECKING:
    from app.services.generation_service import GenerationService

router = APIRouter(prefix="/generations", tags=["Generations"])

# Ensure GenerationResponse TypeAdapter is initialized to prevent
# "not fully defined" errors when returning list[GenerationResponse].
GenerationResponse.model_rebuild()


@router.post("", response_model=GenerationResponse, status_code=status.HTTP_201_CREATED)
async def create_generation(
    payload: GenerateRequest,
    service: "GenerationService" = Depends(get_generation_service),
) -> GenerationResponse:
    """Submit a generation request to the priority queue."""
    # Convert DTO schema to core GenerationParams entity helper
    params = GenerationParams(
        prompt=payload.prompt,
        negative_prompt=payload.negative_prompt,
        width=payload.width,
        height=payload.height,
        steps=payload.steps,
        cfg_scale=payload.cfg_scale,
        seed=payload.seed,
        sampler=payload.sampler,
        model_id=payload.model_id,
        type=payload.type,
        input_image_path=payload.input_image_path,
        denoise_strength=payload.denoise_strength,
        batch_size=1,  # Support single generation per request initially
    )

    try:
        entity = await service.create_generation(params, payload.priority)
        # Convert entity to dict, then manually convert params to dict
        entity_dict = entity.model_dump()
        entity_dict["params"] = entity.params.model_dump()
        return GenerationResponse(**entity_dict)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation submission failed: {e}",
        ) from e


@router.get("/history", response_model=list[GenerationResponse])
async def list_history(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: "GenerationService" = Depends(get_generation_service),
) -> list[GenerationResponse]:
    """Retrieve historical logs of all generations with offset pagination."""
    entities = await service.get_all_generations(limit=limit, offset=offset)
    return [GenerationResponse.model_validate(e) for e in entities]


@router.get("/{generation_id}", response_model=GenerationResponse)
async def get_generation_status(
    generation_id: str,
    service: "GenerationService" = Depends(get_generation_service),
) -> GenerationResponse:
    """Retrieve metadata details and file output paths for a single generation."""
    try:
        entity = await service.get_generation(generation_id)
        return GenerationResponse.model_validate(entity)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Record not found: {e}",
        ) from e
