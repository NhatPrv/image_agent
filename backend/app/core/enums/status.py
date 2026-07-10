"""Status enumerations for generation and queue.

Defines lifecycle states for generation requests and queue items.
"""

from __future__ import annotations

from enum import StrEnum


class GenerationStatus(StrEnum):
    """Lifecycle states of a generation request."""

    PENDING = "pending"
    QUEUED = "queued"
    LOADING_MODEL = "loading_model"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueItemStatus(StrEnum):
    """Lifecycle states of a queue item."""

    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueuePriority(StrEnum):
    """Priority levels for queue items."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
