"""Image record domain entity.

Represents a generated image file with its metadata.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ImageRecord(BaseModel):
    """Domain entity representing a generated image.

    Stores the output of a generation along with all metadata
    needed to reproduce or search for it later.
    """

    id: str
    generation_id: str
    filename: str
    path: str
    thumbnail_path: str | None = None
    width: int
    height: int
    seed_used: int
    format: str = "png"
    size_bytes: int = 0

    # User interaction
    is_favorite: bool = False
    rating: int | None = Field(default=None, ge=1, le=5)
    tags: list[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Full generation metadata for reproducibility
    metadata: dict[str, Any] = Field(default_factory=dict)
