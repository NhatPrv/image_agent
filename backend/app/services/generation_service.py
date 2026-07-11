"""Generation Service.

Coordinates the queuing, executing, database logging, and publishing
of image generation tasks.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.entities.generation import GenerationEntity
from app.core.entities.image_record import ImageRecord
from app.core.enums.status import GenerationStatus
from app.core.exceptions.base import GenerationError, GenerationNotFoundError
import json
from datetime import datetime
from pathlib import Path

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.core.entities.generation import GenerationParams, GenerationProgress
    from app.core.enums.status import QueuePriority
    from app.core.interfaces.ai_engine import IAIEngine
    from app.core.interfaces.event_bus import IEventBus
    from app.core.interfaces.queue_manager import IQueueManager
    from app.core.interfaces.repositories import IGenerationRepository, IImageRepository
    from app.core.interfaces.storage import IStorage

logger = logging.getLogger(__name__)


class GenerationService:
    """Service that orchestrates the lifetime of a generation request."""

    def __init__(
        self,
        settings: Settings,
        generation_repo: IGenerationRepository,
        image_repo: IImageRepository,
        queue_manager: IQueueManager,
        ai_engine: IAIEngine,
        storage: IStorage,
        event_bus: IEventBus,
    ) -> None:
        """Initialize the Generation Service."""
        self._settings = settings
        self._generation_repo = generation_repo
        self._image_repo = image_repo
        self._queue_manager = queue_manager
        self._engine = ai_engine
        self._storage = storage
        self._event_bus = event_bus

    async def get_generation(self, generation_id: str) -> GenerationEntity:
        """Get generation record by ID."""
        entity = await self._generation_repo.get_by_id(generation_id)
        if not entity:
            msg = f"Generation request '{generation_id}' not found."
            raise GenerationNotFoundError(msg, generation_id=generation_id)
        return entity

    async def get_all_generations(
        self, limit: int = 50, offset: int = 0
    ) -> list[GenerationEntity]:
        """Fetch past generations with pagination."""
        return await self._generation_repo.get_history(limit=limit, offset=offset)

    async def create_generation(
        self,
        params: GenerationParams,
        priority: QueuePriority,
    ) -> GenerationEntity:
        """Create a generation request, save it to DB, and push to Queue."""
        # 1. Parameter limits validation
        if (
            params.width < 128
            or params.width > 2048
            or params.height < 128
            or params.height > 2048
        ):
            msg = "Width and height must be between 128 and 2048 pixels."
            raise GenerationError(msg)

        # 2. Map Entity
        entity = GenerationEntity.create(params)

        # 3. Save to database
        await self._generation_repo.save(entity)

        # 4. Push to Priority Queue
        await self._queue_manager.enqueue(entity.id, priority)

        # 5. Emit event
        await self._event_bus.publish(
            "generation.queued",
            {
                "generation_id": entity.id,
                "priority": priority,
                "created_at": entity.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        return entity

    async def execute_generation(self, generation_id: str, queue_item_id: str) -> None:
        """Perform the actual model inference and save outputs."""
        entity = await self._generation_repo.get_by_id(generation_id)
        if not entity:
            msg = f"Generation record '{generation_id}' not found."
            raise GenerationNotFoundError(msg, generation_id=generation_id)

        # Update status to RUNNING in database
        entity.status = GenerationStatus.RUNNING
        await self._generation_repo.update(entity)

        start_time = time.perf_counter()

        # Define progress event bridge
        def _on_progress(progress: GenerationProgress):
            # Publish event to event bus to notify WebSocket clients in real-time.
            # The pipeline runs in loop.run_in_executor, which executes in a thread pool.
            # Therefore, we cannot directly await self._event_bus.publish.
            # Instead, we schedule it back into the main event loop.
            import asyncio

            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self._event_bus.publish(
                        "generation.progress",
                        {
                            "generation_id": progress.generation_id,
                            "current_step": progress.current_step,
                            "total_steps": progress.total_steps,
                            "progress_percent": progress.progress_percent,
                            "elapsed_ms": progress.elapsed_ms,
                            "estimated_remaining_ms": progress.estimated_remaining_ms,
                        },
                    ),
                    loop,
                )

        try:
            # Add generation_id to params extra dict to thread it down
            entity.params.extra["generation_id"] = generation_id

            # Execute generation inside AI engine
            image_paths = await self._engine.generate(entity.params, _on_progress)

            duration_ms = int((time.perf_counter() - start_time) * 1000.0)

            # ─── Process successful outputs ───
            image_records: list[ImageRecord] = []
            for path in image_paths:
                file_path = Path(path)
                thumbnail_path = self._storage.get_thumbnail_path(path)

                record = ImageRecord(
                    id=file_path.stem,
                    generation_id=generation_id,
                    path=path,
                    thumbnail_path=thumbnail_path,
                    width=entity.params.width,
                    height=entity.params.height,
                    format=file_path.suffix.replace(".", "").upper(),
                    size_bytes=file_path.stat().st_size if file_path.exists() else 0,
                )
                await self._image_repo.save(record)
                image_records.append(record)

            # Update DB generation details
            entity.status = GenerationStatus.COMPLETED
            entity.completed_at = (
                entity.created_at
            )  # placeholder datetime, updated by update method
            entity.duration_ms = duration_ms
            await self._generation_repo.update(entity)

            # Persist generation metadata alongside outputs for easier auditing.
            try:
                if image_paths:
                    out_dir = Path(image_paths[0]).parent
                    meta = {
                        "generation_id": generation_id,
                        "prompt": entity.params.prompt,
                        "negative_prompt": entity.params.negative_prompt,
                        "model_id": entity.params.model_id,
                        "params": entity.params.model_dump(),
                        "status": "completed",
                        "images": image_paths,
                        "duration_ms": duration_ms,
                        "created_at": entity.created_at.isoformat(),
                        "completed_at": datetime.utcnow().isoformat(),
                    }

                    meta_path = out_dir / f"{generation_id}.json"
                    loop = __import__("asyncio").get_running_loop()

                    def _write_meta():
                        with open(meta_path, "w", encoding="utf-8") as f:
                            json.dump(meta, f, ensure_ascii=False, indent=2)

                    await loop.run_in_executor(None, _write_meta)
                    logger.info("Wrote generation metadata: %s", meta_path)
            except Exception:
                logger.warning("Failed to write generation metadata file.")

            # Complete queue item
            await self._queue_manager.complete(queue_item_id)

        except Exception as e:
            logger.error("Generation execution failed: %s", str(e))
            entity.status = GenerationStatus.FAILED
            entity.error_message = str(e)
            await self._generation_repo.update(entity)

            # Write failure metadata for debugging
            try:
                out_dir = Path(self._settings.paths.outputs_dir) / "failed_generations"
                out_dir.mkdir(parents=True, exist_ok=True)
                meta = {
                    "generation_id": generation_id,
                    "prompt": entity.params.prompt,
                    "negative_prompt": entity.params.negative_prompt,
                    "model_id": entity.params.model_id,
                    "params": entity.params.model_dump(),
                    "status": "failed",
                    "error": str(e),
                    "created_at": entity.created_at.isoformat(),
                    "failed_at": datetime.utcnow().isoformat(),
                }
                meta_path = out_dir / f"{generation_id}.json"
                loop = __import__("asyncio").get_running_loop()

                def _write_fail():
                    with open(meta_path, "w", encoding="utf-8") as f:
                        json.dump(meta, f, ensure_ascii=False, indent=2)

                await loop.run_in_executor(None, _write_fail)
                logger.info("Wrote failed generation metadata: %s", meta_path)
            except Exception:
                logger.warning("Failed to write failed generation metadata file.")

            # Make sure we clean up the queue item on failure too
            await self._queue_manager.complete(queue_item_id)
            raise e

    async def update_generation(self, generation: GenerationEntity) -> None:
        """Update a generation record."""
        await self._generation_repo.update(generation)
