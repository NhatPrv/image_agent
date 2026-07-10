"""Image record repository implementation.

Persists and retrieves ImageRecord metadata using SQLAlchemy.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select

from app.core.entities.image_record import ImageRecord
from app.core.interfaces.repositories import IImageRepository
from app.infrastructure.database.models import ImageModel
from app.infrastructure.database.repositories.base import BaseRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SQLAlchemyImageRepository(BaseRepository[ImageModel], IImageRepository):
    """SQLAlchemy implementation of the IImageRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ImageModel)

    async def get_by_id(self, entity_id: str) -> ImageRecord | None:
        db_model = await super().get_by_id(entity_id)
        if db_model is None:
            return None
        return self._to_entity(db_model)

    async def save(self, entity: ImageRecord) -> None:
        """Insert or update an image record."""
        db_model = await super().get_by_id(entity.id)

        tags_str = json.dumps(entity.tags) if entity.tags else None
        meta_str = json.dumps(entity.metadata) if entity.metadata else None

        if db_model is None:
            db_model = ImageModel(
                id=entity.id,
                generation_id=entity.generation_id,
                filename=entity.filename,
                path=entity.path,
                thumbnail_path=entity.thumbnail_path,
                width=entity.width,
                height=entity.height,
                seed_used=entity.seed_used,
                format=entity.format,
                size_bytes=entity.size_bytes,
                is_favorite=entity.is_favorite,
                rating=entity.rating,
                tags_json=tags_str,
                created_at=entity.created_at,
                metadata_json=meta_str,
            )
            await super().save(db_model)
        else:
            db_model.is_favorite = entity.is_favorite
            db_model.rating = entity.rating
            db_model.tags_json = tags_str
            db_model.metadata_json = meta_str
            await self._session.flush()

    async def get_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        is_favorite: bool | None = None,
    ) -> tuple[list[ImageRecord], int]:
        """Fetch a paginated list of image records.

        Returns:
            A tuple of (list of ImageRecords, total count matching filter).
        """
        offset = (page - 1) * page_size
        query = select(ImageModel)

        if is_favorite is not None:
            query = query.where(ImageModel.is_favorite == is_favorite)

        # Count query
        count_query = select(func.count()).select_from(query.subquery())
        total_count_result = await self._session.execute(count_query)
        total_count = total_count_result.scalar_one()

        # Data query
        query = query.order_by(ImageModel.created_at.desc()).offset(offset).limit(page_size)
        data_result = await self._session.execute(query)
        records = [self._to_entity(row) for row in data_result.scalars().all()]

        return records, total_count

    def _to_entity(self, db_model: ImageModel) -> ImageRecord:
        """Map ORM ImageModel to domain ImageRecord."""
        tags = []
        if db_model.tags_json:
            try:
                tags = json.loads(db_model.tags_json)
            except Exception:
                logger.warning("Failed to deserialize tags for image %s", db_model.id)

        metadata = {}
        if db_model.metadata_json:
            try:
                metadata = json.loads(db_model.metadata_json)
            except Exception:
                logger.warning("Failed to deserialize metadata for image %s", db_model.id)

        return ImageRecord(
            id=db_model.id,
            generation_id=db_model.generation_id,
            filename=db_model.filename,
            path=db_model.path,
            thumbnail_path=db_model.thumbnail_path,
            width=db_model.width,
            height=db_model.height,
            seed_used=db_model.seed_used,
            format=db_model.format,
            size_bytes=db_model.size_bytes,
            is_favorite=db_model.is_favorite,
            rating=db_model.rating,
            tags=tags,
            created_at=db_model.created_at,
            metadata=metadata,
        )
