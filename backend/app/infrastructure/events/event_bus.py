"""Event bus implementation.

Provides an in-process, asynchronous Publish-Subscribe event system.
Supports priority queueing of handlers and isolates execution errors.
"""

from __future__ import annotations

import inspect
import logging
from typing import TYPE_CHECKING, Any

from app.core.interfaces.event_bus import IEventBus

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


class SubscriberEntry:
    """Wraps a subscriber handler with its metadata."""

    def __init__(
        self,
        handler: Callable[[Any], Awaitable[None] | None],
        priority: int,
    ) -> None:
        self.handler = handler
        self.priority = priority


class InMemoryEventBus(IEventBus):
    """An in-memory event bus implementation."""

    def __init__(self) -> None:
        # Maps event_type -> list of SubscriberEntry
        self._subscribers: dict[str, list[SubscriberEntry]] = {}

    async def publish(self, event_type: str, payload: Any = None) -> None:
        """Publish an event to all registered subscribers asynchronously.

        Handlers are executed sequentially in order of priority. Errors in handlers
        are isolated, logged, and do not prevent other handlers from executing.
        """
        entries = self._subscribers.get(event_type, [])
        if not entries:
            logger.debug("Published event '%s' with no subscribers.", event_type)
            return

        logger.debug(
            "Publishing event '%s' to %d subscribers.",
            event_type,
            len(entries),
        )

        for entry in entries:
            try:
                if inspect.iscoroutinefunction(entry.handler):
                    await entry.handler(payload)
                else:
                    # Sync handler wrapped or called directly if safe
                    entry.handler(payload)
            except Exception as e:
                logger.error(
                    "Error executing handler %s for event '%s': %s",
                    entry.handler.__name__,
                    event_type,
                    str(e),
                    exc_info=True,
                )

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Awaitable[None] | None],
        priority: int = 100,
    ) -> None:
        """Register a subscriber handler for a specific event type.

        Sorts handlers dynamically so that lower values of priority run first.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []

        # Check if already subscribed to avoid duplicate triggers
        for entry in self._subscribers[event_type]:
            if entry.handler == handler:
                logger.warning(
                    "Handler %s is already subscribed to event '%s'. Skipping.",
                    handler.__name__,
                    event_type,
                )
                return

        entry = SubscriberEntry(handler=handler, priority=priority)
        self._subscribers[event_type].append(entry)

        # Sort by priority ascending
        self._subscribers[event_type].sort(key=lambda e: e.priority)
        logger.debug(
            "Subscribed handler %s to event '%s' (priority: %d).",
            handler.__name__,
            event_type,
            priority,
        )

    def unsubscribe(
        self,
        event_type: str,
        handler: Callable[[Any], Awaitable[None] | None],
    ) -> None:
        """Remove a previously registered subscriber."""
        if event_type not in self._subscribers:
            return

        entries = self._subscribers[event_type]
        for i, entry in enumerate(entries):
            if entry.handler == handler:
                entries.pop(i)
                logger.debug(
                    "Unsubscribed handler %s from event '%s'.",
                    handler.__name__,
                    event_type,
                )
                break
        else:
            logger.warning(
                "Attempted to unsubscribe non-registered handler %s from event '%s'.",
                handler.__name__,
                event_type,
            )
