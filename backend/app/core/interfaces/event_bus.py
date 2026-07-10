"""Event Bus interface.

Defines the contract for the in-process event system.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import Any


class IEventBus(ABC):
    """Abstract interface for publish-subscribe event communication."""

    @abstractmethod
    async def publish(self, event_type: str, payload: Any = None) -> None:
        """Publish an event to all registered subscribers.

        Args:
            event_type: Unique string identifying the event type.
            payload: Optional structured payload containing event details.
        """

    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Awaitable[None] | None],
        priority: int = 100,
    ) -> None:
        """Register a subscriber handler for a specific event type.

        Args:
            event_type: Unique string identifying the event type.
            handler: Callable taking the payload as parameter. Can be async or sync.
            priority: Order of execution (lower values run first).
        """

    @abstractmethod
    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Awaitable[None] | None],
    ) -> None:
        """Remove a previously registered subscriber.

        Args:
            event_type: Unique string identifying the event type.
            handler: Callable to remove.
        """
