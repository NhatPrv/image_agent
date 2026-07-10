"""Queue manager interface.

Defines the contract for the generation queue.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.core.entities.queue_item import QueueItem
    from app.core.enums.status import QueuePriority


class IQueueManager(ABC):
    """Abstract interface for managing the image generation queue."""

    @abstractmethod
    async def enqueue(self, generation_id: str, priority: QueuePriority) -> QueueItem:
        """Add a generation request to the queue.

        Args:
            generation_id: The ID of the generation request.
            priority: The priority level of the request.

        Returns:
            The created QueueItem.

        Raises:
            QueueFullError: If the queue size exceeds capacity limits.
        """

    @abstractmethod
    async def dequeue(self) -> QueueItem | None:
        """Fetch and remove the next item from the queue to process.

        Items are fetched based on priority and submission time.

        Returns:
            The next QueueItem to run, or None if the queue is empty.
        """

    @abstractmethod
    async def get_item(self, item_id: str) -> QueueItem | None:
        """Retrieve a specific queue item by its ID.

        Args:
            item_id: Unique ID of the queue item.

        Returns:
            QueueItem if found, otherwise None.
        """

    @abstractmethod
    async def get_all(self) -> list[QueueItem]:
        """Get all items currently in the queue, sorted by priority and position.

        Returns:
            A list of all QueueItems.
        """

    @abstractmethod
    async def cancel(self, item_id: str) -> QueueItem:
        """Cancel a queued item.

        Args:
            item_id: Unique ID of the queue item.

        Returns:
            The cancelled QueueItem.

        Raises:
            QueueItemNotFoundError: If the item does not exist.
        """

    @abstractmethod
    async def clear(self) -> None:
        """Remove all items from the queue."""

    @abstractmethod
    async def get_size(self) -> int:
        """Get the current number of items waiting in the queue.

        Returns:
            Queue size.
        """
