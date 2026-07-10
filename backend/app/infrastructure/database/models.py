"""Database ORM models.

SQLAlchemy mappings for persisting application state.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.connection import Base


class GenerationModel(Base):
    """Database record for image generation requests."""

    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[str] = mapped_column(Text, default="")
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    steps: Mapped[int] = mapped_column(Integer, nullable=False)
    cfg_scale: Mapped[float] = mapped_column(Float, nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    sampler: Mapped[str] = mapped_column(String(50), nullable=False)
    clip_skip: Mapped[int] = mapped_column(Integer, default=1)
    batch_size: Mapped[int] = mapped_column(Integer, default=1)
    model_id: Mapped[str] = mapped_column(String(36), default="")

    # JSON fields stored as TEXT columns
    loras_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    controlnet_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Status & Logging
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seed_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    images: Mapped[list[ImageModel]] = relationship(
        "ImageModel",
        back_populates="generation",
        cascade="all, delete-orphan",
    )
    queue_item: Mapped[QueueItemModel | None] = relationship(
        "QueueItemModel",
        back_populates="generation",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AIModelRecord(Base):
    """Database record for scanned AI model checkpoints/loras/etc."""

    __tablename__ = "models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    component_type: Mapped[str] = mapped_column(String(50), nullable=False)
    architecture: Mapped[str] = mapped_column(String(50), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    hash_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Metadata
    description: Mapped[str] = mapped_column(Text, default="")
    preview_image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    trigger_words_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Flag statuses
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Extra JSON
    extra_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class ImageModel(Base):
    """Database record for generated output images."""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    seed_used: Mapped[int] = mapped_column(Integer, nullable=False)
    format: Mapped[str] = mapped_column(String(10), default="png")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Interactive details
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Custom attributes / reproducibility info
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    generation: Mapped[GenerationModel] = relationship(
        "GenerationModel",
        back_populates="images",
    )


class QueueItemModel(Base):
    """Database record representing queued requests."""

    __tablename__ = "queue_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    generation_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    priority: Mapped[str] = mapped_column(String(20), default="normal")
    status: Mapped[str] = mapped_column(String(20), default="waiting")
    position: Mapped[int] = mapped_column(Integer, default=0)

    # Timing
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationship
    generation: Mapped[GenerationModel] = relationship(
        "GenerationModel",
        back_populates="queue_item",
    )


class SettingModel(Base):
    """Database record for configuration settings."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
