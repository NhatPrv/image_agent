"""Model information domain entity.

Represents metadata about an AI model file on disk.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.enums.model_type import (
    ModelArchitecture,
    ModelComponentType,
    ModelFileFormat,
)


class ModelInfo(BaseModel):
    """Domain entity representing an AI model's metadata.

    Contains all information about a model file without loading
    the actual model weights into memory.
    """

    id: str
    name: str
    filename: str
    path: str
    component_type: ModelComponentType = ModelComponentType.CHECKPOINT
    architecture: ModelArchitecture = ModelArchitecture.UNKNOWN
    file_format: ModelFileFormat = ModelFileFormat.SAFETENSORS
    size_bytes: int = 0
    hash_sha256: str = ""

    # Display info
    description: str = ""
    preview_image_path: str | None = None
    trigger_words: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)

    # Status
    is_loaded: bool = False
    is_favorite: bool = False

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: datetime | None = None

    # Extra metadata from model file
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def size_mb(self) -> float:
        """Get model size in megabytes."""
        return self.size_bytes / (1024 * 1024)

    @property
    def size_gb(self) -> float:
        """Get model size in gigabytes."""
        return self.size_bytes / (1024 * 1024 * 1024)

    @property
    def display_size(self) -> str:
        """Get human-readable file size string."""
        if self.size_gb >= 1.0:
            return f"{self.size_gb:.1f} GB"
        return f"{self.size_mb:.0f} MB"
