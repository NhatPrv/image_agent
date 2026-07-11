"""Generation repository implementation.

Persists and retrieves GenerationEntity records using SQLAlchemy.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.entities.generation import (
    ControlNetConfig,
    GenerationEntity,
    GenerationParams,
    LoRAConfig,
)
from app.core.enums.generation_type import GenerationType
from app.core.enums.scheduler_type import SchedulerType
from app.core.enums.status import GenerationStatus
from app.core.interfaces.repositories import IGenerationRepository
from app.infrastructure.database.models import GenerationModel
from app.infrastructure.database.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyGenerationRepository(BaseRepository[GenerationModel], IGenerationRepository):
    """SQLAlchemy implementation of the IGenerationRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GenerationModel)

    async def get_by_id(self, entity_id: str) -> GenerationEntity | None:
        """Retrieve a GenerationEntity by its unique ID."""
        db_model = await super().get_by_id(entity_id)
        if db_model is None:
            return None
        return self._to_entity(db_model)

    async def save(self, entity: GenerationEntity) -> None:
        """Persist or update a GenerationEntity."""
        db_model = await super().get_by_id(entity.id)

        loras_str = (
            json.dumps([lora.model_dump() for lora in entity.params.loras])
            if entity.params.loras
            else None
        )
        cnet_str = (
            json.dumps(entity.params.controlnet.model_dump()) if entity.params.controlnet else None
        )
        extra_str = json.dumps(entity.params.extra) if entity.params.extra else None
        meta_str = json.dumps(entity.metadata) if entity.metadata else None

        if db_model is None:
            db_model = GenerationModel(
                id=entity.id,
                type=entity.params.type,
                prompt=entity.params.prompt,
                negative_prompt=entity.params.negative_prompt,
                width=entity.params.width,
                height=entity.params.height,
                steps=entity.params.steps,
                cfg_scale=entity.params.cfg_scale,
                seed=entity.params.seed,
                sampler=entity.params.sampler,
                clip_skip=entity.params.clip_skip,
                batch_size=entity.params.batch_size,
                model_id=entity.params.model_id,
                loras_json=loras_str,
                controlnet_json=cnet_str,
                extra_json=extra_str,
                status=entity.status,
                created_at=entity.created_at,
                started_at=entity.started_at,
                completed_at=entity.completed_at,
                duration_ms=entity.duration_ms,
                seed_used=entity.seed_used,
                error_message=entity.error_message,
                metadata_json=meta_str,
            )
            await super().save(db_model)
        else:
            db_model.status = entity.status
            db_model.started_at = entity.started_at
            db_model.completed_at = entity.completed_at
            db_model.duration_ms = entity.duration_ms
            db_model.seed_used = entity.seed_used
            db_model.error_message = entity.error_message
            db_model.loras_json = loras_str
            db_model.controlnet_json = cnet_str
            db_model.extra_json = extra_str
            db_model.metadata_json = meta_str
            # Note: completed outputs are mapped via image records separately in image_repo
            await self._session.flush()

    async def get_recent(self, limit: int = 50) -> list[GenerationEntity]:
        """Fetch recently created generation entities (no offset)."""
        result = await self._session.execute(
            select(GenerationModel).order_by(GenerationModel.created_at.desc()).limit(limit)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    async def get_history(
        self, limit: int = 50, offset: int = 0
    ) -> list[GenerationEntity]:
        """Fetch generation history with pagination support (limit + offset)."""
        result = await self._session.execute(
            select(GenerationModel)
            .order_by(GenerationModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, db_model: GenerationModel) -> GenerationEntity:
        """Map a GenerationModel ORM object to a domain GenerationEntity."""
        loras = None
        if db_model.loras_json:
            try:
                loras_data = json.loads(db_model.loras_json)
                loras = [LoRAConfig(**item) for item in loras_data]
            except Exception:
                logger.warning("Failed to deserialize LoRAs from database record.")

        controlnet = None
        if db_model.controlnet_json:
            try:
                controlnet_data = json.loads(db_model.controlnet_json)
                controlnet = ControlNetConfig(**controlnet_data)
            except Exception:
                logger.warning("Failed to deserialize ControlNet configs.")

        extra = {}
        if db_model.extra_json:
            try:
                extra = json.loads(db_model.extra_json)
            except Exception:
                logger.warning("Failed to deserialize extra configs.")

        metadata = {}
        if db_model.metadata_json:
            try:
                metadata = json.loads(db_model.metadata_json)
            except Exception:
                logger.warning("Failed to deserialize metadata.")

        params = GenerationParams(
            type=GenerationType(db_model.type),
            prompt=db_model.prompt,
            negative_prompt=db_model.negative_prompt,
            width=db_model.width,
            height=db_model.height,
            steps=db_model.steps,
            cfg_scale=db_model.cfg_scale,
            seed=db_model.seed,
            sampler=SchedulerType(db_model.sampler),
            clip_skip=db_model.clip_skip,
            batch_size=db_model.batch_size,
            model_id=db_model.model_id,
            loras=loras,
            controlnet=controlnet,
            extra=extra,
        )

        return GenerationEntity(
            id=db_model.id,
            params=params,
            status=GenerationStatus(db_model.status),
            created_at=db_model.created_at,
            started_at=db_model.started_at,
            completed_at=db_model.completed_at,
            duration_ms=db_model.duration_ms,
            output_images=[],  # Images are queried separately via IImageRepository
            seed_used=db_model.seed_used,
            error_message=db_model.error_message,
            metadata=metadata,
        )
