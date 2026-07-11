"""Model metadata repository implementation.

Persists and retrieves ModelInfo records using SQLAlchemy.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.entities.model_info import ModelInfo
from app.core.enums.model_type import (
    ModelArchitecture,
    ModelComponentType,
    ModelFileFormat,
)
from app.core.interfaces.repositories import IModelRepository
from app.infrastructure.database.models import AIModelRecord
from app.infrastructure.database.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyModelRepository(BaseRepository[AIModelRecord], IModelRepository):
    """SQLAlchemy implementation of the IModelRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AIModelRecord)

    async def get_by_id(self, entity_id: str) -> ModelInfo | None:
        db_model = await super().get_by_id(entity_id)
        if db_model is None:
            return None
        return self._to_entity(db_model)

    async def get_by_hash(self, hash_sha256: str) -> ModelInfo | None:
        """Retrieve model metadata by SHA-256 hash."""
        result = await self._session.execute(
            select(AIModelRecord).where(AIModelRecord.hash_sha256 == hash_sha256)
        )
        db_model = result.scalar_one_or_none()
        if db_model is None:
            return None
        return self._to_entity(db_model)

    async def get_by_path(self, path: str) -> ModelInfo | None:
        """Retrieve model metadata by filesystem path."""
        result = await self._session.execute(
            select(AIModelRecord).where(AIModelRecord.path == path)
        )
        db_model = result.scalar_one_or_none()
        if db_model is None:
            return None
        return self._to_entity(db_model)

    async def save(self, entity: ModelInfo) -> None:
        """Insert or update model metadata."""
        db_model = await super().get_by_id(entity.id)

        trig_str = json.dumps(entity.trigger_words) if entity.trigger_words else None
        tags_str = json.dumps(entity.tags) if entity.tags else None
        meta_str = json.dumps(entity.metadata) if entity.metadata else None

        if db_model is None:
            db_model = AIModelRecord(
                id=entity.id,
                name=entity.name,
                filename=entity.filename,
                path=entity.path,
                component_type=entity.component_type,
                architecture=entity.architecture,
                file_format=entity.file_format,
                size_bytes=entity.size_bytes,
                hash_sha256=entity.hash_sha256,
                description=entity.description,
                preview_image_path=entity.preview_image_path,
                trigger_words_json=trig_str,
                tags_json=tags_str,
                is_favorite=entity.is_favorite,
                created_at=entity.created_at,
                last_used_at=entity.last_used_at,
                extra_json=meta_str,
            )
            await super().save(db_model)
        else:
            db_model.name = entity.name
            db_model.filename = entity.filename
            db_model.path = entity.path
            db_model.component_type = entity.component_type
            db_model.architecture = entity.architecture
            db_model.file_format = entity.file_format
            db_model.size_bytes = entity.size_bytes
            db_model.hash_sha256 = entity.hash_sha256
            db_model.description = entity.description
            db_model.preview_image_path = entity.preview_image_path
            db_model.trigger_words_json = trig_str
            db_model.tags_json = tags_str
            db_model.is_favorite = entity.is_favorite
            db_model.last_used_at = entity.last_used_at
            db_model.extra_json = meta_str
            await self._session.flush()

    async def get_all(self) -> list[ModelInfo]:
        """Get all registered models."""
        result = await self._session.execute(select(AIModelRecord))
        return [self._to_entity(row) for row in result.scalars().all()]

    def _to_entity(self, db_model: AIModelRecord) -> ModelInfo:
        """Map ORM AIModelRecord to domain ModelInfo."""
        trigger_words = []
        if db_model.trigger_words_json:
            try:
                trigger_words = json.loads(db_model.trigger_words_json)
            except Exception:
                logger.warning("Failed to deserialize trigger words.")

        tags = []
        if db_model.tags_json:
            try:
                tags = json.loads(db_model.tags_json)
            except Exception:
                logger.warning("Failed to deserialize tags.")

        metadata = {}
        if db_model.extra_json:
            try:
                metadata = json.loads(db_model.extra_json)
            except Exception:
                logger.warning("Failed to deserialize extra configs.")

        return ModelInfo(
            id=db_model.id,
            name=db_model.name,
            filename=db_model.filename,
            path=db_model.path,
            component_type=ModelComponentType(db_model.component_type),
            architecture=ModelArchitecture(db_model.architecture),
            file_format=ModelFileFormat(db_model.file_format),
            size_bytes=db_model.size_bytes,
            hash_sha256=db_model.hash_sha256,
            description=db_model.description,
            preview_image_path=db_model.preview_image_path,
            trigger_words=trigger_words,
            tags=tags,
            is_loaded=False,  # Loaded status is runtime-only in the AI Engine
            is_favorite=db_model.is_favorite,
            created_at=db_model.created_at,
            last_used_at=db_model.last_used_at,
            metadata=metadata,
        )
