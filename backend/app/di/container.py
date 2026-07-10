"""Dependency Injection container.

Defines provider functions using FastAPI's Depends pattern.
Allows swap-in of mock implementations during unit testing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends

from app.config.settings import Settings, get_settings
from app.engine.engine_manager import AIEngineManager
from app.engine.model_loader import ModelLoader
from app.infrastructure.database.connection import db_manager
from app.infrastructure.database.repositories.generation_repo import (
    SQLAlchemyGenerationRepository,
)
from app.infrastructure.database.repositories.image_repo import (
    SQLAlchemyImageRepository,
)
from app.infrastructure.database.repositories.model_repo import (
    SQLAlchemyModelRepository,
)
from app.infrastructure.database.repositories.settings_repo import (
    SQLAlchemySettingsRepository,
)
from app.infrastructure.events.event_bus import InMemoryEventBus
from app.infrastructure.queue.queue_manager import InMemoryQueueManager
from app.infrastructure.storage.local_storage import LocalFileStorage

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.interfaces.ai_engine import IAIEngine
    from app.core.interfaces.event_bus import IEventBus
    from app.core.interfaces.model_loader import IModelLoader
    from app.core.interfaces.queue_manager import IQueueManager
    from app.core.interfaces.repositories import (
        IGenerationRepository,
        IImageRepository,
        IModelRepository,
        ISettingsRepository,
    )
    from app.core.interfaces.storage import IStorage

# ─── Singleton instances for global systems ───
_event_bus: IEventBus | None = None
_queue_manager: IQueueManager | None = None
_storage_manager: IStorage | None = None
_ai_engine: IAIEngine | None = None


# ─── Configuration Provider ───


def get_settings_dep() -> Settings:
    """Provide global Settings instance."""
    return get_settings()


# ─── Infrastructure Providers ───


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session per request."""
    async for session in db_manager.get_session():
        yield session


def get_event_bus() -> IEventBus:
    """Provide the global Event Bus singleton."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus


def get_queue_manager(settings: Settings = Depends(get_settings_dep)) -> IQueueManager:
    """Provide the global Queue Manager singleton."""
    global _queue_manager
    if _queue_manager is None:
        _queue_manager = InMemoryQueueManager(settings)
    return _queue_manager


def get_storage(settings: Settings = Depends(get_settings_dep)) -> IStorage:
    """Provide the global Storage manager singleton."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = LocalFileStorage(settings)
    return _storage_manager


# ─── Repository Providers ───


def get_generation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IGenerationRepository:
    """Provide a generation repository instance."""
    return SQLAlchemyGenerationRepository(session)


def get_model_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IModelRepository:
    """Provide a model repository instance."""
    return SQLAlchemyModelRepository(session)


def get_image_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IImageRepository:
    """Provide an image repository instance."""
    return SQLAlchemyImageRepository(session)


def get_settings_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ISettingsRepository:
    """Provide a settings repository instance."""
    return SQLAlchemySettingsRepository(session)


def get_model_loader(
    settings: Settings = Depends(get_settings_dep),
) -> IModelLoader:
    """Provide the Model Loader service."""
    return ModelLoader(settings)


def get_ai_engine(
    settings: Settings = Depends(get_settings_dep),
    event_bus: IEventBus = Depends(get_event_bus),
    storage: IStorage = Depends(get_storage),
) -> IAIEngine:
    """Provide the AI Engine Manager singleton."""
    global _ai_engine
    if _ai_engine is None:
        _ai_engine = AIEngineManager(settings, event_bus, storage)
    return _ai_engine
