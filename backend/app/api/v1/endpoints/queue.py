"""Queue Endpoints.

REST router for active generation priority queue inspection and task cancellation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import QueueItemResponse
from app.di.container import get_queue_manager

if TYPE_CHECKING:
    from app.core.interfaces.queue_manager import IQueueManager

router = APIRouter(prefix="/queue", tags=["Queue"])


@router.get("", response_model=list[QueueItemResponse])
async def list_queue(
    manager: IQueueManager = Depends(get_queue_manager),
) -> list[QueueItemResponse]:
    """Retrieve all prioritized queue items currently waiting or executing."""
    items = await manager.get_all()
    return [QueueItemResponse.model_validate(item) for item in items]


@router.post("/{item_id}/cancel", response_model=QueueItemResponse)
async def cancel_queue_item(
    item_id: str,
    manager: IQueueManager = Depends(get_queue_manager),
) -> QueueItemResponse:
    """Cancel a waiting queue item and remove it from scheduling list."""
    try:
        item = await manager.cancel(item_id)
        return QueueItemResponse.model_validate(item)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to cancel: {e}",
        ) from e


@router.delete("", status_code=status.HTTP_200_OK)
async def clear_queue(
    manager: IQueueManager = Depends(get_queue_manager),
) -> dict[str, str]:
    """Clear all waiting items from the scheduling list."""
    try:
        await manager.clear()
        return {"status": "success", "message": "All items cleared from queue."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear queue: {e}",
        ) from e
