"""Generation Service.

Coordinates the queuing, executing, database logging, and publishing
of image generation tasks.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.entities.generation import GenerationEntity
from app.core.entities.image_record import ImageRecord
from app.core.enums.status import GenerationStatus
from app.core.exceptions.base import GenerationError, GenerationNotFoundError

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

    async def sync_output_folder_to_db(self) -> None:
        """Scan outputs directory recursively for JSON metadata files and import missing records into the database."""
        logger.info("Starting synchronization of outputs directory to database...")
        outputs_dir = Path(self._settings.paths.outputs_dir).resolve()
        if not outputs_dir.exists():
            logger.info("Outputs directory does not exist. Skipping synchronization.")
            return

        json_files = []
        for path in outputs_dir.rglob("*.json"):
            if "failed_generations" in path.parts or "thumbnails" in path.parts:
                continue
            json_files.append(path)

        logger.info("Found %d metadata JSON files to check.", len(json_files))

        synced_count = 0
        for json_path in json_files:
            try:
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)

                gen_id = data.get("generation_id")
                if not gen_id or "params" not in data:
                    continue

                # Check if it already exists in database
                existing = await self._generation_repo.get_by_id(gen_id)
                if existing:
                    continue

                # It does not exist, let's recreate the GenerationEntity and ImageRecords
                from app.core.entities.generation import GenerationParams

                params_data = data["params"]

                # Reconstruct GenerationParams
                params = GenerationParams(
                    prompt=params_data.get("prompt", ""),
                    negative_prompt=params_data.get("negative_prompt", ""),
                    width=params_data.get("width", 512),
                    height=params_data.get("height", 512),
                    steps=params_data.get("steps", 20),
                    cfg_scale=params_data.get("cfg_scale", 7.0),
                    seed=params_data.get("seed", -1),
                    sampler=params_data.get("sampler", "euler_a"),
                    model_id=params_data.get("model_id", ""),
                    type=params_data.get("type", "txt2img"),
                    input_image_path=params_data.get("input_image_path"),
                    mask_image_path=params_data.get("mask_image_path"),
                    denoise_strength=params_data.get("denoise_strength", 0.75),
                    batch_size=params_data.get("batch_size", 1),
                )

                # Check if all images in this json file actually exist on disk.
                # If they do not exist, we should clean up the orphan JSON metadata file!
                images_paths = data.get("images", [])
                valid_images = []
                for img_path_str in images_paths:
                    img_file_path = Path(img_path_str)
                    if not img_file_path.is_absolute():
                        img_file_path = outputs_dir / img_file_path
                    if img_file_path.exists():
                        valid_images.append(img_file_path)

                if not valid_images:
                    try:
                        json_path.unlink()
                        logger.info(
                            "Deleted orphan metadata JSON file (image missing): %s", json_path
                        )
                    except Exception as e:
                        logger.warning(
                            "Failed to delete orphan JSON file %s: %s", json_path, str(e)
                        )
                    continue

                created_at_str = data.get("created_at")
                completed_at_str = data.get("completed_at")

                created_at = (
                    datetime.fromisoformat(created_at_str) if created_at_str else datetime.utcnow()
                )
                completed_at = (
                    datetime.fromisoformat(completed_at_str) if completed_at_str else None
                )

                entity = GenerationEntity(
                    id=gen_id,
                    type=params.type,
                    params=params,
                    status=GenerationStatus.COMPLETED,
                    created_at=created_at,
                    started_at=created_at,
                    completed_at=completed_at,
                    duration_ms=data.get("duration_ms", 0),
                    seed_used=params.seed,
                    error_message=None,
                )

                # Save GenerationEntity to DB
                await self._generation_repo.save(entity)

                # Reconstruct ImageRecords and save them

                for img_path_str in images_paths:
                    img_file_path = Path(img_path_str)

                    # Store relative paths to outputs_dir for the frontend static files mapping
                    try:
                        rel_path = str(img_file_path.resolve().relative_to(outputs_dir))
                    except ValueError:
                        rel_path = img_file_path.name

                    thumbnail_path = self._storage.get_thumbnail_path(str(img_file_path))
                    try:
                        rel_thumb_path = str(
                            Path(thumbnail_path).resolve().relative_to(outputs_dir)
                        )
                    except ValueError:
                        rel_thumb_path = None

                    record = ImageRecord(
                        id=img_file_path.stem,
                        generation_id=gen_id,
                        filename=img_file_path.name,
                        path=rel_path,
                        thumbnail_path=rel_thumb_path,
                        width=params.width,
                        height=params.height,
                        seed_used=params.seed,
                        format=img_file_path.suffix.replace(".", "").upper(),
                        size_bytes=img_file_path.stat().st_size if img_file_path.exists() else 0,
                    )
                    await self._image_repo.save(record)

                synced_count += 1
            except Exception as e:
                logger.warning("Failed to sync json file %s: %s", json_path, str(e))

        logger.info(
            "Phase 1: Synchronization completed. Successfully imported %d new records.",
            synced_count,
        )

        # ─── Phase 2: Scan for all raw image files that are not in the database ───
        logger.info("Starting Phase 2: Scanning raw image files...")
        image_extensions = ("*.png", "*.jpg", "*.jpeg", "*.webp")
        image_files = []
        for ext in image_extensions:
            for path in outputs_dir.rglob(ext):
                if "failed_generations" in path.parts or "thumbnails" in path.parts:
                    continue
                image_files.append(path)

        logger.info("Found %d image files to check in outputs folder.", len(image_files))

        image_synced_count = 0
        for img_path in image_files:
            try:
                # Check if this image already exists in the image repo
                existing_img = await self._image_repo.get_by_id(img_path.stem)
                if existing_img:
                    continue

                # Skip if JSON counterpart exists to let Phase 1 handle it or avoid duplicate attempts
                json_counterpart = img_path.with_suffix(".json")
                if json_counterpart.exists():
                    continue

                # Import it as a placeholder generation
                from PIL import Image as PILImage

                width, height = 512, 512
                try:
                    with PILImage.open(img_path) as pil_img:
                        width, height = pil_img.size
                except Exception:
                    pass

                mtime = img_path.stat().st_mtime
                created_at = datetime.fromtimestamp(mtime)

                # Reconstruct GenerationParams
                from app.core.entities.generation import GenerationParams

                params = GenerationParams(
                    prompt=img_path.name,
                    negative_prompt="",
                    width=width,
                    height=height,
                    steps=20,
                    cfg_scale=7.0,
                    seed=-1,
                    sampler="euler_a",
                    model_id="",
                    type="txt2img" if "txt2img" in img_path.parts else "img2img",
                    batch_size=1,
                )

                gen_id = f"gen_{img_path.stem}"

                # Reconstruct GenerationEntity
                entity = GenerationEntity(
                    id=gen_id,
                    type=params.type,
                    params=params,
                    status=GenerationStatus.COMPLETED,
                    created_at=created_at,
                    started_at=created_at,
                    completed_at=created_at,
                    duration_ms=0,
                    seed_used=-1,
                    error_message=None,
                )

                # Save GenerationEntity to DB
                await self._generation_repo.save(entity)

                # Reconstruct relative path for image and thumbnail
                try:
                    rel_path = str(img_path.resolve().relative_to(outputs_dir))
                except ValueError:
                    rel_path = img_path.name

                thumbnail_path = self._storage.get_thumbnail_path(str(img_path))
                # Generate thumbnail if missing
                if not Path(thumbnail_path).exists():
                    try:
                        await self._storage.save_thumbnail(str(img_path))
                    except Exception:
                        pass

                try:
                    rel_thumb_path = str(Path(thumbnail_path).resolve().relative_to(outputs_dir))
                except ValueError:
                    rel_thumb_path = None

                record = ImageRecord(
                    id=img_path.stem,
                    generation_id=gen_id,
                    filename=img_path.name,
                    path=rel_path,
                    thumbnail_path=rel_thumb_path,
                    width=width,
                    height=height,
                    seed_used=-1,
                    format=img_path.suffix.replace(".", "").upper(),
                    size_bytes=img_path.stat().st_size if img_path.exists() else 0,
                    created_at=created_at,
                )
                await self._image_repo.save(record)
                image_synced_count += 1
            except Exception as e:
                logger.warning("Failed to sync raw image file %s: %s", img_path, str(e))

        logger.info(
            "Phase 2: Image synchronization completed. Successfully imported %d new images.",
            image_synced_count,
        )

    async def create_generation(
        self,
        params: GenerationParams,
        priority: QueuePriority,
    ) -> GenerationEntity:
        """Create a generation request, save it to DB, and push to Queue."""
        # 1. Parameter limits validation
        if (
            params.width < 128
            or params.width > 8192
            or params.height < 128
            or params.height > 8192
        ):
            msg = "Width and height must be between 128 and 8192 pixels."
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
        entity.status = GenerationStatus.GENERATING
        await self._generation_repo.update(entity)
        # Commit to release database write lock during GPU inference
        await self._generation_repo._session.commit()

        start_time = time.perf_counter()

        # Capture the main event loop reference before entering executor
        _main_loop = asyncio.get_running_loop()

        # Define progress event bridge
        def _on_progress(progress: GenerationProgress):
            # Publish event to event bus to notify WebSocket clients in real-time.
            # The pipeline runs in loop.run_in_executor, which executes in a thread pool.
            # Therefore, we cannot directly await self._event_bus.publish.
            # Instead, we schedule it back into the main event loop using the
            # captured _main_loop reference.
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
                _main_loop,
            )

        try:
            # Add generation_id to params extra dict to thread it down
            entity.params.extra["generation_id"] = generation_id

            # Execute generation inside AI engine
            image_paths = await self._engine.generate(entity.params, _on_progress)

            duration_ms = int((time.perf_counter() - start_time) * 1000.0)

            # ─── Process successful outputs ───
            image_records: list[ImageRecord] = []
            outputs_dir = Path(self._settings.paths.outputs_dir).resolve()

            # Retrieve the seed used during this generation from params.extra
            seed_used = entity.params.extra.get("seed_used", entity.params.seed)
            if seed_used is None or seed_used < 0:
                seed_used = 0

            for path in image_paths:
                file_path = Path(path)
                thumbnail_path = self._storage.get_thumbnail_path(path)

                # Store relative paths to outputs_dir for the frontend static files mapping
                rel_path = str(file_path.resolve().relative_to(outputs_dir))
                rel_thumb_path = str(Path(thumbnail_path).resolve().relative_to(outputs_dir))

                record = ImageRecord(
                    id=file_path.stem,
                    generation_id=generation_id,
                    filename=file_path.name,
                    path=rel_path,
                    thumbnail_path=rel_thumb_path,
                    width=entity.params.width,
                    height=entity.params.height,
                    seed_used=seed_used,
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
            entity.seed_used = seed_used
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

            # Emit completed event with image records and queue_item_id
            await self._event_bus.publish(
                "generation.completed",
                {
                    "generation_id": generation_id,
                    "queue_item_id": queue_item_id,
                    "completed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "duration_ms": duration_ms,
                    "images": [
                        {
                            "id": img.id,
                            "generation_id": img.generation_id,
                            "path": img.path,
                            "thumbnail_path": img.thumbnail_path,
                            "width": img.width,
                            "height": img.height,
                            "format": img.format,
                            "size_bytes": img.size_bytes,
                            "created_at": img.created_at.strftime("%Y-%m-%dT%H:%M:%SZ")
                            if img.created_at
                            else None,
                        }
                        for img in image_records
                    ],
                },
            )

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

    async def delete_generation(self, generation_id: str) -> None:
        """Delete a generation, its associated images, and all files from disk."""
        entity = await self._generation_repo.get_by_id(generation_id)
        if not entity:
            msg = f"Generation record '{generation_id}' not found."
            raise GenerationNotFoundError(msg, generation_id=generation_id)

        # 1. Delete image files and thumbnails from disk
        for img in entity.output_images:
            try:
                # delete_image expects a relative path or absolute path
                await self._storage.delete_image(img.path)
            except Exception as e:
                logger.warning("Failed to delete image file %s: %s", img.path, str(e))

        # 2. Delete metadata JSON files from disk
        outputs_dir = Path(self._settings.paths.outputs_dir).resolve()
        for img in entity.output_images:
            if img.path:
                abs_img_path = outputs_dir / img.path
                json_path = abs_img_path.parent / f"{generation_id}.json"
                if json_path.exists():
                    try:
                        json_path.unlink()
                        logger.info("Deleted metadata JSON file: %s", json_path)
                    except Exception as e:
                        logger.warning("Failed to delete JSON file %s: %s", json_path, str(e))

        # Also search for a failed generation JSON file
        failed_json_path = outputs_dir / "failed_generations" / f"{generation_id}.json"
        if failed_json_path.exists():
            try:
                failed_json_path.unlink()
                logger.info("Deleted failed generation JSON file: %s", failed_json_path)
            except Exception as e:
                logger.warning(
                    "Failed to delete failed JSON file %s: %s", failed_json_path, str(e)
                )

        # 3. Delete database records
        # SQLAlchemy cascade="all, delete-orphan" handles the ImageModels
        await self._generation_repo.delete(generation_id)
        logger.info("Successfully deleted generation record: %s", generation_id)

    async def optimize_prompt(self, prompt: str) -> str:
        """Call local Ollama instance to translate and optimize the image generation prompt."""
        import httpx

        ollama_url = "http://127.0.0.1:11434"

        # 1. Fetch available models to find the best candidate
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{ollama_url}/api/tags")
                data = res.json()
                models = [m["name"] for m in data.get("models", [])]
        except Exception as e:
            raise RuntimeError(
                f"Ollama is not running. Please start Ollama on your machine first. (Error: {e})"
            )

        # Select model (prefer llama3.1:8b, then qwen2.5-coder:7b, then whatever is available)
        selected_model = None
        for preferred in ["llama3.1:8b", "qwen2.5-coder:7b", "llama3.1", "qwen2.5-coder"]:
            # Match partial name
            for m in models:
                if preferred in m:
                    selected_model = m
                    break
            if selected_model:
                break

        if not selected_model and models:
            # Fallback to first model that is not Nomics embedding
            for m in models:
                if "embed" not in m:
                    selected_model = m
                    break

        if not selected_model:
            raise RuntimeError("No suitable text generation model found in Ollama.")

        # 2. Call Ollama generate API
        system_prompt = (
            "You are a Stable Diffusion prompt optimization expert. "
            "Your task is to take the user's input prompt (which may be in Vietnamese or English) "
            "and convert it into an optimized, highly detailed, comma-separated English prompt "
            "suitable for Stable Diffusion XL.\n"
            "Rules:\n"
            "1. Translate the prompt to English if it is in another language.\n"
            "2. Expand it to include descriptive keywords for style, lighting, camera settings, and level of detail.\n"
            "3. Keep the output concise and under 50 words (comma-separated tags are preferred).\n"
            "4. Respond ONLY with the optimized English prompt. Do not include any explanations, introduction, quotes, or conversational filler."
        )

        prompt_message = f"User input prompt to optimize:\n{prompt}"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{ollama_url}/api/chat",
                    json={
                        "model": selected_model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt_message},
                        ],
                        "options": {
                            "temperature": 0.3,
                            "top_p": 0.9,
                        },
                        "stream": False,
                    },
                )
                response_data = response.json()
                optimized = response_data.get("message", {}).get("content", "").strip()
                # Clean up wrapping quotes if any
                if (optimized.startswith('"') and optimized.endswith('"')) or (
                    optimized.startswith("'") and optimized.endswith("'")
                ):
                    optimized = optimized[1:-1].strip()
                return optimized if optimized else prompt
        except httpx.TimeoutException as e:
            logger.warning("Ollama request timed out (60s limit reached): %s", str(e))
            raise RuntimeError(
                "Ollama request timed out. The local model might be loading slowly into memory. Please try again in a few seconds."
            ) from e
        except Exception as e:
            logger.warning("Ollama request failed: %s", str(e))
            raise RuntimeError(f"Ollama prompt optimization request failed: {e}") from e
