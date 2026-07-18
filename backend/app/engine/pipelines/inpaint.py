"""Inpainting Pipeline.

Implements the SD 1.5 Inpainting pipeline with step progress reporting
and VRAM optimizations.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import torch
from diffusers import StableDiffusionInpaintPipeline, StableDiffusionXLInpaintPipeline
from PIL import Image as PILImage

from app.core.exceptions.base import GenerationError
from app.engine.pipelines.base import BaseDiffusionPipeline
from app.engine.pipelines.txt2img import is_sdxl_checkpoint
from app.engine.scheduler_factory import SchedulerFactory

if TYPE_CHECKING:
    from collections.abc import Callable

    from app.config.settings import Settings
    from app.core.entities.generation import GenerationParams, GenerationProgress

logger = logging.getLogger(__name__)


class InpaintPipeline(BaseDiffusionPipeline):
    """Pipeline for generating content inside a masked region of an image."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)

    async def load(self, model_path: str) -> None:
        is_cuda = torch.cuda.is_available() and self.settings.gpu.device != "cpu"
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
        is_sdxl = is_sdxl_checkpoint(model_path)

        logger.info(
            "Loading model checkpoint for Inpainting: %s on device: %s (SDXL: %s)",
            model_path,
            device,
            is_sdxl,
        )
        try:
            loop = asyncio.get_running_loop()

            def _load_pipe():
                pipeline_class = (
                    StableDiffusionXLInpaintPipeline if is_sdxl else StableDiffusionInpaintPipeline
                )
                kwargs = {
                    "torch_dtype": dtype,
                    "low_cpu_mem_usage": is_sdxl,
                }
                if not is_sdxl:
                    kwargs.update(
                        {
                            "safety_checker": None,
                            "requires_safety_checker": False,
                            "load_safety_checker": False,
                        }
                    )
                return pipeline_class.from_single_file(model_path, **kwargs)

            pipe = await loop.run_in_executor(None, _load_pipe)
            self.pipeline = pipe
            if not (
                self.settings.gpu.cpu_offload
                or self.settings.gpu.sequential_cpu_offload
                or is_sdxl
            ):
                self.pipeline = pipe.to(device)

            self.apply_optimizations()
            logger.info("Inpainting pipeline loaded successfully.")
        except Exception as e:
            logger.error("Failed to load model file %s for Inpainting: %s", model_path, str(e))
            msg = f"Failed loading pipeline checkpoint: {e}"
            raise GenerationError(msg) from e

    def load_from_components(self, components: dict[str, Any]) -> None:
        """Initialize the pipeline by reusing components from another pipeline.

        Prevents reload time and VRAM duplication.
        """
        logger.info("Initializing Inpainting pipeline reusing existing components.")
        try:
            if "text_encoder_2" in components:
                self.pipeline = StableDiffusionXLInpaintPipeline(**components)
            else:
                self.pipeline = StableDiffusionInpaintPipeline(**components)
            self.apply_optimizations()
        except Exception as e:
            logger.error("Failed to create inpainting pipeline from components: %s", str(e))
            msg = f"Failed component sharing setup: {e}"
            raise GenerationError(msg) from e

    async def generate(
        self,
        params: GenerationParams,
        generation_id: str,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[Any]:
        """Generate images based on the provided parameters."""
        if self.pipeline is None:
            msg = "Pipeline is not loaded. Call load() first."
            raise GenerationError(msg)

        # ─── 0.1 Apply LoRA Weights ───
        lora_inputs = params.extra.get("lora_inputs", [])
        self.apply_loras(lora_inputs)

        if not params.input_image_path or not params.mask_image_path:
            msg = "Both input image path and mask image path are required for Inpainting."
            raise GenerationError(msg)

        # ─── 1. Load and process input and mask images ───
        loop = asyncio.get_running_loop()
        try:

            def _load_images():
                with (
                    PILImage.open(params.input_image_path) as init_img,
                    PILImage.open(params.mask_image_path) as mask_img,
                ):
                    # Convert input image to RGB and resize
                    init_processed = init_img.convert("RGB").resize((params.width, params.height))
                    # Convert mask image to grayscale and resize
                    mask_processed = mask_img.convert("L").resize((params.width, params.height))
                    return init_processed, mask_processed

            input_image, mask_image = await loop.run_in_executor(None, _load_images)
        except Exception as e:
            logger.error("Failed to load or process input/mask images: %s", str(e))
            msg = f"Failed processing inpaint images: {e}"
            raise GenerationError(msg) from e

        # ─── 1.5 Apply dynamic high-resolution VRAM optimizations ───
        self.apply_high_res_optimizations(params.width, params.height)

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
            logger.info("Inpainting seed set dynamically to: %d", seed_used)
        params.extra["seed_used"] = seed_used

        # ─── 4. Progress Tracking Callback ───
        total_steps = params.steps
        start_time = None

        def _step_callback(
            _pipe_self,
            step: int,
            _timestep: int,
            callback_kwargs: dict[str, Any],
        ) -> dict[str, Any]:
            nonlocal start_time
            if start_time is None:
                start_time = time.perf_counter()

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
            "Executing Inpainting | Prompt: '%s' | Size: %dx%d",
            params.prompt,
            params.width,
            params.height,
        )

        try:

            def _run_inference():
                output = self.pipeline(
                    prompt=params.prompt,
                    negative_prompt=params.negative_prompt,
                    image=input_image,
                    mask_image=mask_image,
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
            logger.error("Error during inpainting execution: %s", str(e))
            msg = f"Inference execution failed: {e}"
            raise GenerationError(msg) from e
