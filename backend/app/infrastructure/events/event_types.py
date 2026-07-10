"""Event payloads and type definitions.

Defines Pydantic models representing event data payloads.
"""

from __future__ import annotations

from pydantic import BaseModel


class BaseEventPayload(BaseModel):
    """Base class for all event payloads."""


# ─── Generation Events ───


class GenerationQueuedPayload(BaseEventPayload):
    """Payload for generation.queued event."""

    generation_id: str
    prompt: str
    queued_at: str


class GenerationStartedPayload(BaseEventPayload):
    """Payload for generation.started event."""

    generation_id: str
    model_id: str
    started_at: str


class GenerationProgressPayload(BaseEventPayload):
    """Payload for generation.progress event."""

    generation_id: str
    current_step: int
    total_steps: int
    progress_percent: float
    elapsed_ms: int
    preview_image_path: str | None = None


class GenerationCompletedPayload(BaseEventPayload):
    """Payload for generation.completed event."""

    generation_id: str
    output_images: list[str]
    seed_used: int
    completed_at: str
    duration_ms: int


class GenerationFailedPayload(BaseEventPayload):
    """Payload for generation.failed event."""

    generation_id: str
    error_message: str
    failed_at: str


class GenerationCancelledPayload(BaseEventPayload):
    """Payload for generation.cancelled event."""

    generation_id: str
    cancelled_at: str


# ─── Model Events ───


class ModelLoadingPayload(BaseEventPayload):
    """Payload for model.loading event."""

    model_id: str
    model_name: str
    started_at: str


class ModelLoadedPayload(BaseEventPayload):
    """Payload for model.loaded event."""

    model_id: str
    model_name: str
    loaded_at: str
    vram_usage_mb: float


class ModelUnloadedPayload(BaseEventPayload):
    """Payload for model.unloaded event."""

    model_id: str
    unloaded_at: str


class ModelErrorPayload(BaseEventPayload):
    """Payload for model.error event."""

    model_id: str
    error_message: str
    occurred_at: str


# ─── System Events ───


class SystemVRAMWarningPayload(BaseEventPayload):
    """Payload for system.vram_warning event."""

    used_mb: float
    total_mb: float
    percentage: float


class SystemVRAMCriticalPayload(BaseEventPayload):
    """Payload for system.vram_critical event."""

    used_mb: float
    total_mb: float
    percentage: float
    required_mb: float
