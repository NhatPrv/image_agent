"""Cancellation Registry.

Global thread-safe registry tracking cancelled generation IDs to interrupt long-running GPU operations.
"""

import threading

_cancelled_ids: set[str] = set()
_lock = threading.Lock()


def register_cancellation(gen_id: str) -> None:
    """Mark a generation or queue ID as cancelled."""
    if not gen_id:
        return
    with _lock:
        _cancelled_ids.add(gen_id)


def is_cancelled(gen_id: str) -> bool:
    """Check if a generation or queue ID has been marked as cancelled."""
    if not gen_id:
        return False
    with _lock:
        return gen_id in _cancelled_ids


def unregister_cancellation(gen_id: str) -> None:
    """Remove a generation or queue ID from the cancellation set."""
    if not gen_id:
        return
    with _lock:
        _cancelled_ids.discard(gen_id)
