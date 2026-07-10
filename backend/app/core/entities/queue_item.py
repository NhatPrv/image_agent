"""Queue item domain entity.

Represents an item in the generation queue.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums.status import QueueItemStatus, QueuePriority


class QueueItem(BaseModel):
    """Domain entity representing a queue entry.

    Each queue item wraps a generation_id and adds queue-specific
    metadata like priority, position, and timing.
    """

    id: str
    generation_id: str
    priority: QueuePriority = QueuePriority.NORMAL
    status: QueueItemStatus = QueueItemStatus.WAITING
    position: int = 0

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Error tracking
    error_message: str | None = None
    retry_count: int = 0
    max_retries: int = 0

    @property
    def priority_value(self) -> int:
        """Numeric priority for sorting (higher = more urgent)."""
        return {
            QueuePriority.LOW: 0,
            QueuePriority.NORMAL: 1,
            QueuePriority.HIGH: 2,
            QueuePriority.URGENT: 3,
        }[self.priority]
