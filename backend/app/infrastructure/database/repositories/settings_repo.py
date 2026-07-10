"""Settings repository implementation.

Persists and retrieves application settings using SQLAlchemy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from app.core.interfaces.repositories import ISettingsRepository
from app.infrastructure.database.models import SettingModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SQLAlchemySettingsRepository(ISettingsRepository):
    """SQLAlchemy implementation of the ISettingsRepository interface."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: The active SQLAlchemy async session.
        """
        self._session = session

    async def get(self, key: str) -> str | None:
        """Retrieve a setting value by key."""
        result = await self._session.execute(select(SettingModel).where(SettingModel.key == key))
        db_model = result.scalar_one_or_none()
        return db_model.value if db_model is not None else None

    async def set(self, key: str, value: str) -> None:
        """Save or update a setting key-value pair."""
        result = await self._session.execute(select(SettingModel).where(SettingModel.key == key))
        db_model = result.scalar_one_or_none()

        if db_model is None:
            db_model = SettingModel(key=key, value=value)
            self._session.add(db_model)
        else:
            db_model.value = value

        await self._session.flush()

    async def get_all(self) -> dict[str, str]:
        """Fetch all saved setting entries."""
        result = await self._session.execute(select(SettingModel))
        return {row.key: row.value for row in result.scalars().all()}
