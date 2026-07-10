"""Repository interfaces.

Defines persistence contracts for all domain objects.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.entities.generation import GenerationEntity
    from app.core.entities.image_record import ImageRecord
    from app.core.entities.model_info import ModelInfo


class IGenerationRepository(ABC):
    """Abstract repository for persisting image generation requests."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> GenerationEntity | None:
        """Retrieve a generation entity by its unique ID."""

    @abstractmethod
    async def save(self, entity: GenerationEntity) -> None:
        """Insert or update a generation entity in the store."""

    @abstractmethod
    async def get_recent(self, limit: int = 50) -> list[GenerationEntity]:
        """Fetch recently created generation entities."""


class IModelRepository(ABC):
    """Abstract repository for persisting local AI model metadata."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> ModelInfo | None:
        """Retrieve model metadata by ID."""

    @abstractmethod
    async def get_by_hash(self, hash_sha256: str) -> ModelInfo | None:
        """Retrieve model metadata by SHA-256 hash."""

    @abstractmethod
    async def save(self, entity: ModelInfo) -> None:
        """Insert or update model metadata."""

    @abstractmethod
    async def get_all(self) -> list[ModelInfo]:
        """Get all registered models."""

    @abstractmethod
    async def delete(self, entity_id: str) -> None:
        """Remove a model record from the store."""


class IImageRepository(ABC):
    """Abstract repository for persisting generated image records."""

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> ImageRecord | None:
        """Retrieve image record by ID."""

    @abstractmethod
    async def save(self, entity: ImageRecord) -> None:
        """Insert or update an image record."""

    @abstractmethod
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

    @abstractmethod
    async def delete(self, entity_id: str) -> None:
        """Remove image record metadata."""


class ISettingsRepository(ABC):
    """Abstract repository for app configuration key-value storage."""

    @abstractmethod
    async def get(self, key: str) -> str | None:
        """Retrieve a setting value by key."""

    @abstractmethod
    async def set(self, key: str, value: str) -> None:
        """Save or update a setting key-value pair."""

    @abstractmethod
    async def get_all(self) -> dict[str, str]:
        """Fetch all saved setting entries."""
