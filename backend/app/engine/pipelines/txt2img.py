"""Text-to-Image Pipeline.

Implements the SD 1.5 Text-to-Image pipeline with step progress reporting.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING, Any

import numpy as np
import torch
from diffusers import StableDiffusionPipeline, StableDiffusionXLPipeline

from app.core.exceptions.base import GenerationError
from app.engine.pipelines.base import BaseDiffusionPipeline
from app.engine.scheduler_factory import SchedulerFactory


def is_sdxl_checkpoint(file_path: str) -> bool:
    if not file_path.endswith(".safetensors"):
        return False
    try:
        import json
        import struct
        from pathlib import Path

        p = Path(file_path)
        with p.open("rb") as f:
            header_size_bytes = f.read(8)
            if len(header_size_bytes) < 8:
                return False
            header_size = struct.unpack("<Q", header_size_bytes)[0]
            header_json_bytes = f.read(header_size)
            header = json.loads(header_json_bytes.decode("utf-8"))
            return any(
                "conditioner.embedders.1" in k or "model.diffusion_model.label_emb" in k
                for k in header
            )
    except Exception:
        return False


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
        is_sdxl = is_sdxl_checkpoint(model_path)

        logger.info(
            "Loading model checkpoint for Text-to-Image: %s on device: %s (SDXL: %s)",
            model_path,
            device,
            is_sdxl,
        )
        try:
            # Run blocking file loading in executor to prevent event loop delay
            loop = asyncio.get_running_loop()

            def _load_pipe():
                # from_single_file handles both .safetensors and .ckpt local checkpoints
                pipeline_class = StableDiffusionXLPipeline if is_sdxl else StableDiffusionPipeline
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

        # ─── 0.2. Optimize and Enhance Prompts for Realism & Quality ───
        prompt = params.prompt
        negative_prompt = params.negative_prompt or ""

        # Default high-quality negative prompt to filter out deformities
        default_negatives = (
            "bad anatomy, deformed, distorted, blurry, low quality, out of focus, "
            "duplicate, watermark, signature, ugly, bad hands, mutated, extra limbs"
        )
        if not negative_prompt.strip():
            negative_prompt = default_negatives
        else:
            if len(negative_prompt.split()) < 5:
                negative_prompt = f"{negative_prompt.strip()}, {default_negatives}"

        # Automatic Prompt Expansion for Quality and Sharpness
        quality_tags = ["detailed", "high quality", "sharp", "resolution", "cinematic"]
        has_quality = any(tag in prompt.lower() for tag in quality_tags)
        if not has_quality:
            prompt_lower = prompt.lower()
            photo_keys = ["photo", "real", "cinematic", "portrait", "landscape"]
            art_keys = ["anime", "manga", "illustration", "drawing", "paint"]

            if any(k in prompt_lower for k in photo_keys):
                prompt = (
                    f"{prompt.strip()}, photorealistic, 8k resolution, extremely detailed, "
                    "sharp focus, cinematic lighting"
                )
            elif any(k in prompt_lower for k in art_keys):
                prompt = (
                    f"{prompt.strip()}, masterpiece, high quality, highly detailed illustration, "
                    "sharp lines, vibrant colors"
                )
            else:
                prompt = f"{prompt.strip()}, highly detailed, high quality, sharp focus"

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
            # Determine base resolution (target 1024px for the larger side)
            max_dim = 1024
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
            start_time = None
            total_steps = params.steps

            def _step_callback_pass1(
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
                        prompt=prompt,
                        negative_prompt=negative_prompt,
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

                # Pass 2: Upscale and run Tiled Img2Img
                from diffusers import StableDiffusionImg2ImgPipeline, StableDiffusionXLImg2ImgPipeline
                from PIL import Image as PILImage
                from PIL import ImageFilter

                # Create shared components Img2Img Pipeline
                is_sdxl = isinstance(self.pipeline, StableDiffusionXLPipeline)
                pipeline_class = StableDiffusionXLImg2ImgPipeline if is_sdxl else StableDiffusionImg2ImgPipeline
                img2img_pipe = pipeline_class(**self.pipeline.components)

                # Disable safety checker on tiled Pass 2 to avoid
                # false-positive black tiles and boost generation speed.
                if hasattr(img2img_pipe, "safety_checker"):
                    img2img_pipe.safety_checker = None
                if hasattr(img2img_pipe, "requires_safety_checker"):
                    img2img_pipe.requires_safety_checker = False

                # Temporarily point self.pipeline to img2img_pipe to apply optimizations
                original_pipe = self.pipeline
                self.pipeline = img2img_pipe
                self.apply_high_res_optimizations(params.width, params.height)

                # Configure Pass 2 grid for Tiled Upscaling
                # Dynamically set tile size to avoid crash on dimensions smaller than 768
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

                strength = 0.55
                pass2_inference_steps = int(total_steps / strength)
                pass2_steps = max(1, int(pass2_inference_steps * strength))
                total_pass2_steps = total_tiles * pass2_steps
                combined_total_steps = total_steps + total_pass2_steps

                def _step_callback_pass2(
                    _pipe_self,
                    step: int,
                    _timestep: int,
                    callback_kwargs: dict[str, Any],
                    tile_idx: int,
                ) -> dict[str, Any]:
                    if progress_callback:
                        elapsed_ms = int((time.perf_counter() - start_time) * 1000.0)
                        current_combined_step = total_steps + tile_idx * pass2_steps + step
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

                # Precompute 2D linear blending mask
                mask_np = np.ones((tile_size, tile_size), dtype=np.float32)
                for i in range(overlap):
                    val = i / overlap
                    mask_np[i, :] *= val
                    mask_np[-1 - i, :] *= val
                    mask_np[:, i] *= val
                    mask_np[:, -1 - i] *= val
                mask_3d = np.expand_dims(mask_np, axis=-1)

                final_images = []
                for base_img in base_images:
                    # Upscale using Lanczos interpolation
                    upscaled_img = base_img.resize(
                        (params.width, params.height),
                        resample=PILImage.Resampling.LANCZOS,
                    )

                    # Apply Unsharp Masking to base upscaled canvas to enhance edges
                    # before the diffusion model injects high-frequency details.
                    sharpened_base = upscaled_img.filter(
                        ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)
                    )

                    def _run_tiled_upscale(img=sharpened_base):
                        # Initialize accumulator canvas
                        canvas = np.zeros((params.height, params.width, 3), dtype=np.float32)
                        weights = np.zeros((params.height, params.width, 1), dtype=np.float32)
                        img_np = np.array(img).astype(np.float32) / 255.0

                        t_idx = 0
                        for y in y_coords:
                            for x in x_coords:
                                # Crop tile from upscaled image
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
                                    return _step_callback_pass2(
                                        pipe_self,
                                        step,
                                        timestep,
                                        callback_kwargs,
                                        current_t_idx,
                                    )

                                # Denoise tile at 512x512 - 100% OOM Safe!
                                output = img2img_pipe(
                                    prompt=prompt,
                                    negative_prompt=negative_prompt,
                                    image=tile_img,
                                    strength=strength,
                                    num_inference_steps=pass2_inference_steps,
                                    guidance_scale=params.cfg_scale,
                                    generator=generator,
                                    callback_on_step_end=_local_callback,
                                    callback_on_step_end_tensor_inputs=["latents"],
                                )

                                output_tile = np.array(output.images[0]).astype(np.float32) / 255.0

                                # Accumulate
                                canvas[y : y + tile_size, x : x + tile_size, :3] += (
                                    output_tile * mask_3d
                                )
                                weights[y : y + tile_size, x : x + tile_size, :] += mask_3d
                                t_idx += 1

                        # Blend and normalize grid
                        final_np = np.where(weights > 0, canvas / weights, img_np)
                        final_np = np.clip(final_np * 255.0, 0, 255).astype(np.uint8)
                        return PILImage.fromarray(final_np)

                    final_img = await loop.run_in_executor(None, _run_tiled_upscale)
                    final_images.append(final_img)

                # Restore original text-to-image pipeline reference
                self.pipeline = original_pipe
                logger.info("Hi-Res Fix generation completed successfully.")
                return final_images

            except Exception as e:
                # Restore original pipeline reference in case of failure
                if "original_pipe" in locals():
                    self.pipeline = original_pipe
                logger.error("Error during Hi-Res Fix execution: %s", str(e))
                msg = f"Hi-Res Fix execution failed: {e}"
                raise GenerationError(msg) from e

        else:
            # ─── Standard Resolution Direct Generation ───
            total_steps = params.steps
            start_time = None

            def _step_callback(
                _pipe_self,
                step: int,
                _timestep: int,
                callback_kwargs: dict[str, Any],
            ) -> dict[str, Any]:
                """Callback triggered by diffusers after each denoising step."""
                nonlocal start_time
                if start_time is None:
                    start_time = time.perf_counter()

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
