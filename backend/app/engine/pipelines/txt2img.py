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

        # ─── 0. Apply dynamic high-resolution VRAM optimizations ───
        self.apply_high_res_optimizations(params.width, params.height)

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

        # Check if high-resolution generation is requested (> 1024 on any side)
        # to trigger the Hi-Res Fix upscaling algorithm
        is_high_res = params.width > 1024 or params.height > 1024

        if is_high_res:
            # Determine base resolution (target 768px for the larger side)
            max_dim = 768
            if params.width >= params.height:
                base_w = max_dim
                base_h = int(max_dim * (params.height / params.width))
            else:
                base_h = max_dim
                base_w = int(max_dim * (params.width / params.height))

            # Round to nearest multiple of 8
            base_w = max(128, (base_w // 8) * 8)
            base_h = max(128, (base_h // 8) * 8)

            logger.info(
                "Hi-Res Fix triggered. Generating base image at %dx%d, then upscaling to %dx%d.",
                base_w,
                base_h,
                params.width,
                params.height,
            )

            # Define step end callback for Pass 1 (0% to 70% progress)
            start_time = time.perf_counter()
            total_steps = params.steps

            def _step_callback_pass1(
                _pipe_self,
                step: int,
                _timestep: int,
                callback_kwargs: dict[str, Any],
            ) -> dict[str, Any]:
                if progress_callback:
                    elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                    # Estimate remaining steps across both passes (Pass 1 + Pass 2)
                    # Pass 2 is an img2img pass which runs (steps * denoising_strength) steps.
                    # Denoising strength: 0.35
                    pass2_steps = max(1, int(total_steps * 0.35))
                    combined_total_steps = total_steps + pass2_steps

                    percent = (step / combined_total_steps) * 100.0

                    from app.core.entities.generation import (
                        GenerationProgress as ProgressEntity,
                    )

                    # Calculate average step time
                    avg_step_time = (elapsed_ms / step) if step > 0 else 0
                    est_remaining_ms = int(avg_step_time * (combined_total_steps - step))

                    progress_data = ProgressEntity(
                        generation_id=generation_id,
                        current_step=step,
                        total_steps=combined_total_steps,
                        progress_percent=percent,
                        elapsed_ms=elapsed_ms,
                        estimated_remaining_ms=est_remaining_ms,
                    )
                    progress_callback(progress_data)
                return callback_kwargs

            # Pass 1: Generate Base Image
            try:
                loop = asyncio.get_running_loop()

                def _run_pass1():
                    output = self.pipeline(
                        prompt=params.prompt,
                        negative_prompt=params.negative_prompt,
                        num_inference_steps=params.steps,
                        guidance_scale=params.cfg_scale,
                        width=base_w,
                        height=base_h,
                        generator=generator,
                        num_images_per_prompt=params.batch_size,
                        callback_on_step_end=_step_callback_pass1,
                        callback_on_step_end_tensor_inputs=["latents"],
                    )
                    return output.images

                base_images = await loop.run_in_executor(None, _run_pass1)

                # Pass 2: Upscale and run Img2Img
                from diffusers import StableDiffusionImg2ImgPipeline
                from PIL import Image as PILImage

                # Create shared components Img2Img Pipeline
                img2img_pipe = StableDiffusionImg2ImgPipeline(**self.pipeline.components)
                # Temporarily point self.pipeline to img2img_pipe to apply optimizations
                original_pipe = self.pipeline
                self.pipeline = img2img_pipe
                self.apply_high_res_optimizations(params.width, params.height)

                # Configure Pass 2 steps end callback (70% to 100% progress)
                pass2_steps = max(1, int(total_steps * 0.35))
                combined_total_steps = total_steps + pass2_steps

                def _step_callback_pass2(
                    _pipe_self,
                    step: int,
                    _timestep: int,
                    callback_kwargs: dict[str, Any],
                ) -> dict[str, Any]:
                    if progress_callback:
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                        current_combined_step = total_steps + step
                        avg_step_time = (
                            (elapsed_ms / current_combined_step)
                            if current_combined_step > 0
                            else 0
                        )
                        est_remaining_ms = int(
                            avg_step_time * (combined_total_steps - current_combined_step)
                        )
                        percent = (current_combined_step / combined_total_steps) * 100.0

                        from app.core.entities.generation import (
                            GenerationProgress as ProgressEntity,
                        )

                        progress_data = ProgressEntity(
                            generation_id=generation_id,
                            current_step=current_combined_step,
                            total_steps=combined_total_steps,
                            progress_percent=percent,
                            elapsed_ms=elapsed_ms,
                            estimated_remaining_ms=est_remaining_ms,
                        )
                        progress_callback(progress_data)
                    return callback_kwargs

                final_images = []
                for base_img in base_images:
                    # Upscale using Lanczos interpolation
                    upscaled_img = base_img.resize(
                        (params.width, params.height),
                        resample=PILImage.Resampling.LANCZOS,
                    )

                    def _run_pass2(img=upscaled_img):
                        output = img2img_pipe(
                            prompt=params.prompt,
                            negative_prompt=params.negative_prompt,
                            image=img,
                            # Low denoising strength to add details but preserve layout
                            strength=0.35,
                            num_inference_steps=params.steps,
                            guidance_scale=params.cfg_scale,
                            generator=generator,
                            callback_on_step_end=_step_callback_pass2,
                            callback_on_step_end_tensor_inputs=["latents"],
                        )
                        return output.images[0]

                    final_img = await loop.run_in_executor(None, _run_pass2)
                    final_images.append(final_img)

                # Restore original text-to-image pipeline reference
                self.pipeline = original_pipe
                logger.info("Hi-Res Fix generation completed successfully.")
                return final_images

            except Exception as e:
                # Restore original pipeline reference in case of failure
                if 'original_pipe' in locals():
                    self.pipeline = original_pipe
                logger.error("Error during Hi-Res Fix execution: %s", str(e))
                msg = f"Hi-Res Fix execution failed: {e}"
                raise GenerationError(msg) from e

        else:
            # ─── Standard Resolution Direct Generation ───
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
                    avg_step_time = (elapsed_ms / step) if step > 0 else 0
                    est_remaining_ms = int(avg_step_time * (total_steps - step))
                    percent = (step / total_steps) * 100.0

                    from app.core.entities.generation import (
                        GenerationProgress as ProgressEntity,
                    )

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

            logger.info(
                "Executing Standard Text-to-Image generation | Prompt: '%s' | "
                "Steps: %d | Size: %dx%d",
                params.prompt,
                params.steps,
                params.width,
                params.height,
            )

            try:
                loop = asyncio.get_running_loop()

                def _run_inference():
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

                return await loop.run_in_executor(None, _run_inference)
            except Exception as e:
                logger.error("Error during inference execution: %s", str(e))
                msg = f"Inference execution failed: {e}"
                raise GenerationError(msg) from e
