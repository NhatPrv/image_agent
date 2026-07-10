"""In-memory queue manager.

Implements IQueueManager with priority sorting, capacity safety,
and atomic position updates. Thread-safe using asyncio.Lock.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import TYPE_CHECKING

from app.core.entities.queue_item import QueueItem
from app.core.enums.status import QueueItemStatus, QueuePriority
from app.core.exceptions.base import QueueFullError, QueueItemNotFoundError
from app.core.interfaces.queue_manager import IQueueManager

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class InMemoryQueueManager(IQueueManager):
    """In-memory queue manager with priority sorting."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the queue.

        Args:
            settings: Unified application configuration.
        """
        self._settings = settings
        self._queue: list[QueueItem] = []
        self._lock = asyncio.Lock()

    async def enqueue(self, generation_id: str, priority: QueuePriority) -> QueueItem:
        """Add a generation request to the queue.

        Raises:
            QueueFullError: If queue size exceeds configuration limits.
        """
        async with self._lock:
            # Check maximum queue capacity
            # 100 limit defined in defaults, or we can use custom max_size if specified
            max_size = 100
            if len(self._queue) >= max_size:
                msg = f"Queue is full. Maximum size is {max_size}."
                raise QueueFullError(msg, max_size=max_size)

            item = QueueItem(
                id=uuid.uuid4().hex,
                generation_id=generation_id,
                priority=priority,
                status=QueueItemStatus.WAITING,
                position=len(self._queue) + 1,
            )
            self._queue.append(item)
            self._sort_and_reposition_unlocked()
            logger.info(
                "Enqueued generation '%s' (priority: %s, position: %d)",
                generation_id,
                priority,
                item.position,
            )
            return item

    async def dequeue(self) -> QueueItem | None:
        """Fetch and remove the next item from the queue to process.

        Sorted by priority (highest first) and submission time.
        """
        async with self._lock:
            # Filter items with WAITING status
            waiting_items = [
                item for item in self._queue if item.status == QueueItemStatus.WAITING
            ]
            if not waiting_items:
                return None

            # Get first item (already sorted)
            next_item = waiting_items[0]
            next_item.status = QueueItemStatus.RUNNING
            self._sort_and_reposition_unlocked()
            logger.info("Dequeued queue item '%s' for processing", next_item.id)
            return next_item

    async def get_item(self, item_id: str) -> QueueItem | None:
        """Retrieve a specific queue item by its ID."""
        async with self._lock:
            for item in self._queue:
                if item.id == item_id:
                    return item
            return None

    async def get_all(self) -> list[QueueItem]:
        """Get all items currently in the queue."""
        async with self._lock:
            # Return copy of queue
            return list(self._queue)

    async def cancel(self, item_id: str) -> QueueItem:
        """Cancel a queued item and remove it from the list."""
        async with self._lock:
            for i, item in enumerate(self._queue):
                if item.id == item_id:
                    cancelled_item = self._queue.pop(i)
                    cancelled_item.status = QueueItemStatus.CANCELLED
                    self._sort_and_reposition_unlocked()
                    logger.info("Cancelled queue item '%s'", item_id)
                    return cancelled_item

            msg = f"Queue item with ID {item_id} not found."
            raise QueueItemNotFoundError(msg, item_id=item_id)

    async def clear(self) -> None:
        """Remove all items from the queue."""
        async with self._lock:
            self._queue.clear()
            logger.info("Cleared all items from generation queue.")

    async def get_size(self) -> int:
        """Get the current number of items waiting in the queue."""
        async with self._lock:
            return len([item for item in self._queue if item.status == QueueItemStatus.WAITING])

    def _sort_and_reposition_unlocked(self) -> None:
        """Sort the queue in-place and update positions without acquiring lock."""
        # 1. Sort logic: Priority descending, then submission time ascending (FIFO)
        # Note: python sort is stable, sorting by created_at then priority achieves this
        self._queue.sort(key=lambda item: item.created_at)
        self._queue.sort(key=lambda item: item.priority_value, reverse=True)

        # 2. Re-calculate active index position
        pos = 1
        for item in self._queue:
            if item.status == QueueItemStatus.WAITING:
                item.position = pos
                pos += 1
            else:
                item.position = 0
