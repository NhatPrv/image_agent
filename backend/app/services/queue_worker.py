"""Queue Worker.

Background task worker that polls the prioritized queue and routes
generation tasks sequentially.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

from app.core.enums.status import GenerationStatus

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.core.interfaces.ai_engine import IAIEngine
    from app.core.interfaces.queue_manager import IQueueManager

logger = logging.getLogger(__name__)


class QueueWorker:
    """Worker running sequentially in background to execute queued generations."""

    def __init__(
        self,
        queue_manager: IQueueManager,
        ai_engine: IAIEngine,
        services_context_maker: Callable[[], Any],
    ) -> None:
        """Initialize the Queue Worker."""
        self._queue_manager = queue_manager
        self._ai_engine = ai_engine
        self._services_context_maker = services_context_maker

        self._worker_task: asyncio.Task | None = None
        self._is_running = False

    def start(self) -> None:
        """Launch the worker loop in the background."""
        if self._is_running:
            return

        self._is_running = True
        self._worker_task = asyncio.create_task(self._loop())
        logger.info("Queue Worker started successfully.")

    async def stop(self) -> None:
        """Gracefully request stopping of the worker task."""
        if not self._is_running:
            return

        logger.info("Stopping Queue Worker gracefully...")
        self._is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._worker_task
        logger.info("Queue Worker stopped.")

    async def _loop(self) -> None:
        """Sequentially process items from the queue manager."""
        while self._is_running:
            try:
                # 1. Fetch next waiting item
                item = await self._queue_manager.dequeue()
                if item is None:
                    # Queue is empty, rest a bit
                    await asyncio.sleep(1.0)
                    continue

                logger.info(
                    "Processing queue item '%s' for generation '%s'", item.id, item.generation_id
                )

                # Acquire fresh session context per queue execution
                async with self._services_context_maker() as (generation_service, model_service):
                    # 2. Get generation parameters
                    try:
                        generation = await generation_service.get_generation(item.generation_id)
                    except Exception as e:
                        logger.error(
                            "Failed to retrieve generation %s for queue item: %s",
                            item.generation_id,
                            str(e),
                        )
                        await self._queue_manager.complete(item.id)
                        continue

                    # 3. Model auto-swap orchestrator
                    target_model_id = generation.params.model_id
                    active_model = self._ai_engine.get_loaded_model()

                    try:
                        if active_model is None or active_model.id != target_model_id:
                            logger.info(
                                "Queue Worker: Auto-swapping loaded model to '%s'", target_model_id
                            )
                            await model_service.load_model(target_model_id)

                        # 4. Trigger generation execution
                        await generation_service.execute_generation(generation.id, item.id)

                    except Exception as e:
                        logger.error("Failure running queue item generation: %s", str(e))
                        # Ensure status update in DB if loading failed before
                        # execute_generation could catch it
                        try:
                            generation.status = GenerationStatus.FAILED
                            generation.error_message = f"Model load or setup failure: {e}"
                            await generation_service.update_generation(generation)
                        except Exception:
                            pass
                        # Assure queue item is cleaned up
                        with contextlib.suppress(Exception):
                            await self._queue_manager.complete(item.id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Unexpected error in Queue Worker loop: %s", str(e))
                await asyncio.sleep(2.0)
