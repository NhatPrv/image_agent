"""Image-to-Image Pipeline.

Implements the SD 1.5 Image-to-Image pipeline with support for input images
and denoise strength configurations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import torch
from diffusers import StableDiffusionImg2ImgPipeline
from PIL import Image as PILImage

from app.core.exceptions.base import GenerationError
from app.engine.pipelines.base import BaseDiffusionPipeline
from app.engine.scheduler_factory import SchedulerFactory

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.config.settings import Settings
    from app.core.entities.generation import GenerationParams, GenerationProgress

logger = logging.getLogger(__name__)


class Img2ImgPipeline(BaseDiffusionPipeline):
    """Pipeline for generating images from an input image and prompt."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    async def load(self, model_path: str) -> None:
        is_cuda = torch.cuda.is_available() and self.settings.gpu.device != "cpu"
        # Use float16/bfloat16 only when CUDA is available; fallback to float32 on CPU
        if is_cuda:
            if self.settings.gpu.dtype == "float16":
                dtype = torch.float16
            elif self.settings.gpu.dtype == "bfloat16":
                dtype = torch.bfloat16
            else:
                dtype = torch.float32
        else:
            dtype = torch.float32

        device = "cuda" if is_cuda else "cpu"

        logger.info("Loading model checkpoint for Image-to-Image: %s", model_path)
        try:
            loop = asyncio.get_running_loop()

            def _load_pipe():
                return StableDiffusionImg2ImgPipeline.from_single_file(
                    model_path,
                    torch_dtype=dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                    load_safety_checker=False,
                )

            pipe = await loop.run_in_executor(None, _load_pipe)
            self.pipeline = pipe.to(device)
            self.apply_optimizations()
        except Exception as e:
            logger.error("Failed to load model file %s: %s", model_path, str(e))
            msg = f"Failed loading pipeline checkpoint: {e}"
            raise GenerationError(msg) from e

    def load_from_components(self, components: dict[str, Any]) -> None:
        """Initialize the pipeline by reusing components from another pipeline.

        Prevents reload time and VRAM duplication.
        """
        logger.info("Initializing Image-to-Image pipeline reusing existing components.")
        try:
            self.pipeline = StableDiffusionImg2ImgPipeline(**components)
            self.apply_optimizations()
        except Exception as e:
            logger.error("Failed to create pipeline from components: %s", str(e))
            msg = f"Failed component sharing setup: {e}"
            raise GenerationError(msg) from e

    async def generate(
        self,
        params: GenerationParams,
        generation_id: str,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[Any]:
        """Generate images based on the provided params."""
        if self.pipeline is None:
            msg = "Pipeline is not loaded. Call load() first."
            raise GenerationError(msg)

        if not params.input_image_path:
            msg = "Input image path is required for Image-to-Image generation."
            raise GenerationError(msg)

        # ─── 1. Load and process input image ───
        loop = asyncio.get_running_loop()
        try:

            def _load_img():
                with PILImage.open(params.input_image_path) as img:
                    # Convert to RGB and resize to match settings
                    return img.convert("RGB").resize((params.width, params.height))

            input_image = await loop.run_in_executor(None, _load_img)
        except Exception as e:
            logger.error("Failed to load input image: %s", str(e))
            msg = f"Failed to open input image: {e}"
            raise GenerationError(msg) from e

        # ─── 2. Configure Scheduler ───
        self.pipeline.scheduler = SchedulerFactory.create(
            params.sampler, self.pipeline.scheduler.config
        )

        # ─── 3. Seed configuration ───
        generator = None
        if params.seed >= 0:
            seed_used = params.seed
            generator = torch.Generator(device=self.pipeline.device).manual_seed(params.seed)
        else:
            seed_used = int(time.time() * 1000) % (2**32 - 1)
            generator = torch.Generator(device=self.pipeline.device).manual_seed(seed_used)
            logger.info("Img2Img seed set dynamically to: %d", seed_used)
        params.extra["seed_used"] = seed_used

        # ─── 4. Progress Tracking Callback ───
        total_steps = params.steps
        start_time = time.perf_counter()

        def _step_callback(
            _pipe_self,
            step: int,
            _timestep: int,
            callback_kwargs: dict[str, Any],
        ) -> dict[str, Any]:
            if progress_callback:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                avg_step_time = (elapsed_ms / step) if step > 0 else 0
                est_remaining_ms = int(avg_step_time * (total_steps - step))
                percent = (step / total_steps) * 100.0

                from app.core.entities.generation import GenerationProgress as ProgressEntity

                progress_data = ProgressEntity(
                    generation_id=generation_id,
                    current_step=step,
                    total_steps=total_steps,
                    progress_percent=percent,
                    elapsed_ms=elapsed_ms,
                    estimated_remaining_ms=est_remaining_ms,
                )
                progress_callback(progress_data)
            return callback_kwargs

        # ─── 5. Inference execution ───
        logger.info(
            "Executing Image-to-Image | Prompt: '%s' | Strength: %.2f | Size: %dx%d",
            params.prompt,
            params.denoise_strength,
            params.width,
            params.height,
        )

        try:

            def _run_inference():
                output = self.pipeline(
                    prompt=params.prompt,
                    negative_prompt=params.negative_prompt,
                    image=input_image,
                    strength=params.denoise_strength,
                    num_inference_steps=params.steps,
                    guidance_scale=params.cfg_scale,
                    generator=generator,
                    num_images_per_prompt=params.batch_size,
                    callback_on_step_end=_step_callback,
                    callback_on_step_end_tensor_inputs=["latents"],
                )
                return output.images

            return await loop.run_in_executor(None, _run_inference)
        except Exception as e:
            logger.error("Error during inference execution: %s", str(e))
            msg = f"Inference execution failed: {e}"
            raise GenerationError(msg) from e
