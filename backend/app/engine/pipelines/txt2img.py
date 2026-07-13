"""Text-to-Image Pipeline.

Implements the SD 1.5 Text-to-Image pipeline with step progress reporting.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import torch
from diffusers import StableDiffusionPipeline

from app.core.exceptions.base import GenerationError
from app.engine.pipelines.base import BaseDiffusionPipeline
from app.engine.scheduler_factory import SchedulerFactory

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.config.settings import Settings
    from app.core.entities.generation import GenerationParams, GenerationProgress

logger = logging.getLogger(__name__)


class Txt2ImgPipeline(BaseDiffusionPipeline):
    """Pipeline for generating images from text prompts using Stable Diffusion."""

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

        logger.info(
            "Loading model checkpoint for Text-to-Image: %s on device: %s",
            model_path,
            device,
        )
        try:
            # Run blocking file loading in executor to prevent event loop delay
            loop = asyncio.get_running_loop()

            def _load_pipe():
                # from_single_file handles both .safetensors and .ckpt local checkpoints
                return StableDiffusionPipeline.from_single_file(
                    model_path,
                    torch_dtype=dtype,
                    safety_checker=None,
                    requires_safety_checker=False,
                    load_safety_checker=False,
                )

            pipe = await loop.run_in_executor(None, _load_pipe)
            self.pipeline = pipe.to(device)

            # Apply configurations
            self.apply_optimizations()
            logger.info("Text-to-Image pipeline loaded successfully.")
        except Exception as e:
            logger.error("Failed to load model file %s: %s", model_path, str(e))
            msg = f"Failed loading pipeline checkpoint: {e}"
            raise GenerationError(msg) from e

    async def generate(
        self,
        params: GenerationParams,
        generation_id: str,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[Any]:
        """Generate images based on the provided params.

        Args:
            params: Domain parameters.
            generation_id: ID of the generation request.
            progress_callback: Callback to notify step progress.

        Returns:
            A list of PIL Images.
        """
        if self.pipeline is None:
            msg = "Pipeline is not loaded. Call load() first."
            raise GenerationError(msg)

        # ─── 1. Configure Scheduler / Sampler ───
        self.pipeline.scheduler = SchedulerFactory.create(
            params.sampler, self.pipeline.scheduler.config
        )

        # ─── 2. Seed configuration ───
        generator = None
        if params.seed >= 0:
            seed_used = params.seed
            generator = torch.Generator(device=self.pipeline.device).manual_seed(params.seed)
        else:
            # Random seed
            seed_used = int(time.time() * 1000) % (2**32 - 1)
            generator = torch.Generator(device=self.pipeline.device).manual_seed(seed_used)
            logger.info("Generation seed set dynamically to: %d", seed_used)
        params.extra["seed_used"] = seed_used

        # ─── 3. Progress Tracking Callback ───
        total_steps = params.steps
        start_time = time.perf_counter()

        def _step_callback(
            _pipe_self,
            step: int,
            _timestep: int,
            callback_kwargs: dict[str, Any],
        ) -> dict[str, Any]:
            """Callback triggered by diffusers after each denoising step."""
            if progress_callback:
                elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                # Simple linear remaining time estimation
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

        # ─── 4. Inference execution ───
        logger.info(
            "Executing Text-to-Image generation | Prompt: '%s' | Steps: %d | Size: %dx%d",
            params.prompt,
            params.steps,
            params.width,
            params.height,
        )

        try:
            loop = asyncio.get_running_loop()

            def _run_inference():
                # We use callback_on_step_end for progress updates
                output = self.pipeline(
                    prompt=params.prompt,
                    negative_prompt=params.negative_prompt,
                    num_inference_steps=params.steps,
                    guidance_scale=params.cfg_scale,
                    width=params.width,
                    height=params.height,
                    generator=generator,
                    num_images_per_prompt=params.batch_size,
                    callback_on_step_end=_step_callback,
                    callback_on_step_end_tensor_inputs=["latents"],
                )
                return output.images

            # Run inference in executor - capture loop reference so callback
            # can schedule async tasks on the main event loop from any thread.
            result = await loop.run_in_executor(None, _run_inference)
            return result
        except Exception as e:
            logger.error("Error during inference execution: %s", str(e))
            msg = f"Inference execution failed: {e}"
            raise GenerationError(msg) from e
