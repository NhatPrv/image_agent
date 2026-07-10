"""Base repository class.

Provides common asynchronous database query helpers using SQLAlchemy.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Generic, TypeVar

from sqlalchemy import select

from app.infrastructure.database.connection import Base

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing basic CRUD operations."""

    def __init__(self, session: AsyncSession, model_class: type[ModelType]) -> None:
        """Initialize the repository.

        Args:
            session: The active SQLAlchemy async session.
            model_class: The ORM model class targeted by this repository.
        """
        self._session = session
        self._model_class = model_class

    async def get_by_id(self, entity_id: str) -> ModelType | None:
        """Fetch a record by its string primary key."""
        result = await self._session.execute(
            select(self._model_class).where(self._model_class.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def save(self, db_model: ModelType) -> None:
        """Insert or merge a record inside the active session context.

        Note: Does not call commit() itself, session commits are managed
        by unit-of-work or transactional middleware patterns.
        """
        self._session.add(db_model)
        await self._session.flush()

    async def delete(self, entity_id: str) -> None:
        """Delete a record matching the primary key."""
        db_model = await self.get_by_id(entity_id)
        if db_model is not None:
            await self._session.delete(db_model)
            await self._session.flush()
        else:
            logger.warning(
                "Attempted to delete non-existent %s: %s",
                self._model_class.__name__,
                entity_id,
            )
