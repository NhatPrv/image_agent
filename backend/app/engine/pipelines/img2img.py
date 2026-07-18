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
from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionXLImg2ImgPipeline
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
        is_sdxl = is_sdxl_checkpoint(model_path)

        logger.info(
            "Loading model checkpoint for Image-to-Image: %s on device: %s (SDXL: %s)",
            model_path,
            device,
            is_sdxl,
        )
        try:
            loop = asyncio.get_running_loop()

            def _load_pipe():
                pipeline_class = (
                    StableDiffusionXLImg2ImgPipeline if is_sdxl else StableDiffusionImg2ImgPipeline
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
            if "text_encoder_2" in components:
                self.pipeline = StableDiffusionXLImg2ImgPipeline(**components)
            else:
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

        # ─── 0.1 Apply LoRA Weights ───
        lora_inputs = params.extra.get("lora_inputs", [])
        self.apply_loras(lora_inputs)

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
            logger.info("Img2Img seed set dynamically to: %d", seed_used)
        params.extra["seed_used"] = seed_used

        # ─── 4. Determine if Tiled Upscaling is needed ───
        is_high_res = params.width > 1024 or params.height > 1024
        total_steps = params.steps
        start_time = None

        if is_high_res:
            import numpy as np

            # Configure grid for Tiled Img2Img
            tile_size = min(768, params.width, params.height)
            overlap = min(96, tile_size // 8)

            def get_grid_coords(total_size: int, tile_s: int, over: int) -> list[int]:
                if total_size <= tile_s:
                    return [0]
                coords = []
                c = 0
                stride = tile_s - over
                while c + tile_s < total_size:
                    coords.append(c)
                    c += stride
                coords.append(total_size - tile_s)
                return coords

            x_coords = get_grid_coords(params.width, tile_size, overlap)
            y_coords = get_grid_coords(params.height, tile_size, overlap)
            total_tiles = len(x_coords) * len(y_coords)

            # Create 2D feather mask for seamless blending
            mask = np.ones((tile_size, tile_size), dtype=np.float32)
            feather = min(32, overlap // 2)
            for i in range(feather):
                val = (i + 1) / (feather + 1)
                mask[i, :] *= val
                mask[-1 - i, :] *= val
                mask[:, i] *= val
                mask[:, -1 - i] *= val
            mask_3d = np.expand_dims(mask, axis=-1)

            combined_total_steps = total_tiles * total_steps

            # ─── 5. Inference execution (Tiled) ───
            logger.info(
                "Executing Tiled Image-to-Image | Prompt: '%s' | Strength: %.2f | Size: %dx%d (Tiles: %d)",
                params.prompt,
                params.denoise_strength,
                params.width,
                params.height,
                total_tiles,
            )

            try:

                def _run_tiled_inference():
                    # Initialize accumulator canvas
                    canvas = np.zeros((params.height, params.width, 3), dtype=np.float32)
                    weights = np.zeros((params.height, params.width, 1), dtype=np.float32)
                    img_np = np.array(input_image).astype(np.float32) / 255.0

                    t_idx = 0
                    for y in y_coords:
                        for x in x_coords:
                            # Crop tile from input image
                            tile_np = img_np[y : y + tile_size, x : x + tile_size, :3]
                            tile_img = PILImage.fromarray((tile_np * 255.0).astype(np.uint8))

                            # Bind local callback for this tile index
                            def _local_callback(
                                pipe_self,
                                step,
                                timestep,
                                callback_kwargs,
                                current_t_idx=t_idx,
                            ):
                                nonlocal start_time
                                if start_time is None:
                                    start_time = time.perf_counter()

                                if progress_callback:
                                    elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                                    current_combined_step = current_t_idx * total_steps + step
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

                            # Denoise tile
                            output = self.pipeline(
                                prompt=params.prompt,
                                negative_prompt=params.negative_prompt,
                                image=tile_img,
                                strength=params.denoise_strength,
                                num_inference_steps=params.steps,
                                guidance_scale=params.cfg_scale,
                                generator=generator,
                                num_images_per_prompt=params.batch_size,
                                callback_on_step_end=_local_callback,
                                callback_on_step_end_tensor_inputs=["latents"],
                            )

                            output_tile = np.array(output.images[0]).astype(np.float32) / 255.0

                            # Accumulate
                            canvas[y : y + tile_size, x : x + tile_size, :3] += output_tile * mask_3d
                            weights[y : y + tile_size, x : x + tile_size, :] += mask_3d
                            t_idx += 1

                    # Blend and normalize grid
                    final_np = np.where(weights > 0, canvas / weights, img_np)
                    final_np = np.clip(final_np * 255.0, 0, 255).astype(np.uint8)
                    return [PILImage.fromarray(final_np)]

                return await loop.run_in_executor(None, _run_tiled_inference)
            except Exception as e:
                logger.error("Error during tiled inference execution: %s", str(e))
                msg = f"Tiled inference execution failed: {e}"
                raise GenerationError(msg) from e

        else:
            # ─── Standard Progress Tracking Callback ───
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

            # ─── 5. Inference execution (Standard) ───
            logger.info(
                "Executing Standard Image-to-Image | Prompt: '%s' | Strength: %.2f | Size: %dx%d",
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
