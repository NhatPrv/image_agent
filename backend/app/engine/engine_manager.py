"""AI Engine Manager.

Facade that implements IAIEngine. Manages model lifecycles, pipeline routing,
VRAM optimization, and persistence of output images.
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Any

from app.core.enums.generation_type import GenerationType
from app.core.exceptions.base import EngineError, ModelNotLoadedError
from app.core.interfaces.ai_engine import IAIEngine
from app.engine.pipelines.img2img import Img2ImgPipeline
from app.engine.pipelines.txt2img import Txt2ImgPipeline
from app.engine.vram_manager import VRAMManager

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.config.settings import Settings
    from app.core.entities.generation import GenerationParams, GenerationProgress
    from app.core.entities.model_info import ModelInfo
    from app.core.interfaces.event_bus import IEventBus
    from app.core.interfaces.storage import IStorage

logger = logging.getLogger(__name__)


class AIEngineManager(IAIEngine):
    """Facade orchestrating the active diffusers pipelines and memory states."""

    def __init__(
        self,
        settings: Settings,
        event_bus: IEventBus,
        storage: IStorage,
    ) -> None:
        """Initialize the Engine Manager.

        Args:
            settings: Unified application configuration.
            event_bus: Event bus for lifecycle notifications.
            storage: File storage manager.
        """
        self._settings = settings
        self._event_bus = event_bus
        self._storage = storage

        self._vram_manager = VRAMManager(settings)

        # Pipelines
        self._active_model_info: ModelInfo | None = None
        self._txt2img_pipeline: Txt2ImgPipeline | None = None
        self._img2img_pipeline: Img2ImgPipeline | None = None

    async def generate(
        self,
        params: GenerationParams,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[str]:
        """Generate images based on parameters, save to storage, and return file paths."""
        if not self.is_model_loaded() or self._active_model_info is None:
            raise ModelNotLoadedError

        generation_id = params.extra.get("generation_id", "gen_" + str(int(time.time())))

        # ─── 1. Pipeline Routing ───
        model_path = self._active_model_info.path
        start_time = time.perf_counter()

        try:
            # Emit starting event
            await self._event_bus.publish(
                "generation.started",
                {
                    "generation_id": generation_id,
                    "model_id": self._active_model_info.id,
                    "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

            pil_images = []
            if params.type == GenerationType.TEXT_TO_IMAGE:
                # Setup txt2img if not already initialized
                if self._txt2img_pipeline is None:
                    self._txt2img_pipeline = Txt2ImgPipeline(self._settings)
                    await self._txt2img_pipeline.load(model_path)

                pil_images = await self._txt2img_pipeline.generate(
                    params, generation_id, progress_callback
                )
                dir_name = "txt2img"
            elif params.type == GenerationType.IMAGE_TO_IMAGE:
                # Share components from txt2img if loaded to save time/VRAM
                if self._img2img_pipeline is None:
                    self._img2img_pipeline = Img2ImgPipeline(self._settings)
                    has_txt2img = (
                        self._txt2img_pipeline is not None
                        and self._txt2img_pipeline.pipeline is not None
                    )
                    if has_txt2img:
                        self._img2img_pipeline.load_from_components(
                            self._txt2img_pipeline.pipeline.components
                        )
                    else:
                        await self._img2img_pipeline.load(model_path)

                pil_images = await self._img2img_pipeline.generate(
                    params, generation_id, progress_callback
                )
                dir_name = "img2img"
            else:
                msg = f"Generation type '{params.type}' not supported in this version."
                raise EngineError(msg)

            # ─── 2. Image Persistence & Output Processing ───
            output_paths: list[str] = []
            for i, img in enumerate(pil_images):
                img_path = await self._storage.save_image(
                    image=img,
                    directory_name=dir_name,
                    filename_prefix=f"output_{i}",
                    save_format="png",
                )
                # Create corresponding thumbnail
                await self._storage.save_thumbnail(img_path)
                output_paths.append(img_path)

            duration_ms = int((time.perf_counter() - start_time) * 1000.0)

            # Emit completed event
            await self._event_bus.publish(
                "generation.completed",
                {
                    "generation_id": generation_id,
                    "output_images": output_paths,
                    # Replace with actual generator seed if parsed dynamically
                    "seed_used": params.seed,
                    "completed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "duration_ms": duration_ms,
                },
            )
            return output_paths

        except Exception as e:
            logger.error("Generation failed in engine manager: %s", str(e))
            await self._event_bus.publish(
                "generation.failed",
                {
                    "generation_id": generation_id,
                    "error_message": str(e),
                    "failed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            raise e

    async def load_model(self, model: ModelInfo) -> None:
        """Load a new model checkpoint into GPU VRAM.

        Clears current pipelines first to prevent memory collision.
        """
        # If the same model is already loaded, skip reload
        if self._active_model_info is not None and self._active_model_info.path == model.path:
            logger.info("Model '%s' is already active. Skipping reload.", model.name)
            return

        # 1. Unload existing model
        await self.unload_model()

        # 2. Check memory thresholds
        # Estimate size: default estimate SD 1.5 is 2GB, SDXL is 6.5GB
        estimated_req_mb = 2000.0
        if model.architecture == "sdxl":
            estimated_req_mb = 6500.0

        self._vram_manager.check_vram_safety(estimated_req_mb)

        logger.info("Loading model into GPU VRAM: %s (%s)", model.name, model.architecture)
        await self._event_bus.publish(
            "model.loading",
            {
                "model_id": model.id,
                "model_name": model.name,
                "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

        try:
            # We initialize and load txt2img first as default
            self._txt2img_pipeline = Txt2ImgPipeline(self._settings)
            await self._txt2img_pipeline.load(model.path)

            self._active_model_info = model

            # Fetch VRAM status post-load
            used_mb, total_mb, _ = self._vram_manager.get_vram_info()
            logger.info(
                "Model loaded successfully. Current GPU VRAM usage: %.1fMB / %.1fMB (%.1f%%)",
                used_mb,
                total_mb,
                (used_mb / total_mb) * 100.0 if total_mb > 0 else 0.0,
            )

            await self._event_bus.publish(
                "model.loaded",
                {
                    "model_id": model.id,
                    "model_name": model.name,
                    "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "vram_usage_mb": used_mb,
                },
            )
        except Exception as e:
            logger.error("Failed to load model %s: %s", model.name, str(e))
            await self._event_bus.publish(
                "model.error",
                {
                    "model_id": model.id,
                    "error_message": str(e),
                    "occurred_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            )
            # Re-raise
            raise e

    async def unload_model(self) -> None:
        """Unload active pipelines and garbage collect GPU memory."""
        if self._active_model_info is None:
            return

        logger.info("Unloading model and clearing GPU VRAM: %s", self._active_model_info.name)

        # 1. Delete pipeline references to free tensors
        self._txt2img_pipeline = None
        self._img2img_pipeline = None

        # 2. Force PyTorch garbage collection and empty CUDA cache
        self._vram_manager.clean_memory()

        old_model_id = self._active_model_info.id
        self._active_model_info = None

        await self._event_bus.publish(
            "model.unloaded",
            {
                "model_id": old_model_id,
                "unloaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    def get_loaded_model(self) -> ModelInfo | None:
        """Retrieve the currently active model info."""
        return self._active_model_info

    def is_model_loaded(self) -> bool:
        """Check if any model is active in memory."""
        return self._active_model_info is not None
