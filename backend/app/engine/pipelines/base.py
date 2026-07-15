"""Base Diffusion Pipeline class.

Provides common methods and VRAM optimizations for all AI engine pipelines.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class BaseDiffusionPipeline:
    """Base class wrapper around Diffusers pipelines.

    Encapsulates standard PyTorch execution configurations and VRAM memory optimization patterns.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the pipeline base.

        Args:
            settings: Unified application configuration.
        """
        self.settings = settings
        self.pipeline: Any = None

    def apply_optimizations(self) -> None:
        """Apply configured memory and compute optimizations to the pipeline.

        Applies xformers, slicing, tiling, and offloading selectively based on GPU config.
        """
        if self.pipeline is None:
            return

        device = self.settings.gpu.device
        is_cuda = torch.cuda.is_available() and device != "cpu"

        if not is_cuda:
            logger.info("Pipeline optimizations skipped: executing on CPU.")
            return

        pipe_name = self.pipeline.__class__.__name__
        is_sdxl_or_flux = "XL" in pipe_name or "Flux" in pipe_name or "Flow" in pipe_name

        # ─── 1. xformers (Requires nvidia GPU, nvml, and installed xformers package) ───
        # Note: Flux/Flow pipelines do not support standard xformers easily
        if self.settings.gpu.xformers and not ("Flux" in pipe_name or "Flow" in pipe_name):
            try:
                self.pipeline.enable_xformers_memory_efficient_attention()
                logger.info("Optimized: xformers memory-efficient attention enabled.")
            except Exception as e:
                logger.warning(
                    "Could not enable xformers attention. "
                    "Make sure xformers is installed correctly. Error: %s",
                    str(e),
                )
                # Fallback to standard PyTorch SDPA if available

        # ─── 2. Attention Slicing (Saves VRAM, slight speed penalty) ───
        if self.settings.gpu.attention_slicing or is_sdxl_or_flux:
            try:
                self.pipeline.enable_attention_slicing()
                logger.info("Optimized: Attention slicing enabled.")
            except Exception as e:
                logger.warning("Could not enable attention slicing: %s", str(e))

        # ─── 3. VAE Slicing (Saves massive VRAM during decode step) ───
        if self.settings.gpu.vae_slicing or is_sdxl_or_flux:
            try:
                self.pipeline.enable_vae_slicing()
                logger.info("Optimized: VAE slicing enabled.")
            except Exception as e:
                logger.warning("Could not enable VAE slicing: %s", str(e))

        # ─── 4. VAE Tiling (For high-resolution image decoding) ───
        if self.settings.gpu.vae_tiling or is_sdxl_or_flux:
            try:
                self.pipeline.enable_vae_tiling()
                logger.info("Optimized: VAE tiling enabled.")
            except Exception as e:
                logger.warning("Could not enable VAE tiling: %s", str(e))

        # ─── 5. Model CPU Offloading (Saves VRAM by keeping inactive modules on RAM) ───
        if self.settings.gpu.cpu_offload or is_sdxl_or_flux:
            try:
                self.pipeline.enable_model_cpu_offload()
                logger.info("Optimized: Model CPU offload enabled.")
            except Exception as e:
                logger.warning("Could not enable model CPU offload: %s", str(e))

        # ─── 6. Sequential CPU Offloading (Aggressive VRAM optimization) ───
        if self.settings.gpu.sequential_cpu_offload:
            try:
                self.pipeline.enable_sequential_cpu_offload()
                logger.info("Optimized: Sequential CPU offload enabled.")
            except Exception as e:
                logger.warning("Could not enable sequential CPU offload: %s", str(e))

        # ─── 7. Torch Compile (JIT compiler, boosts generation speed, slow startup) ───
        if self.settings.gpu.torch_compile:
            try:
                logger.info(
                    "Compiling unet with torch.compile (causes a delay on the first step)..."
                )
                self.pipeline.unet = torch.compile(
                    self.pipeline.unet, mode="reduce-overhead", fullgraph=True
                )
            except Exception as e:
                logger.warning("Failed to compile model: %s", str(e))

    def apply_high_res_optimizations(self, width: int, height: int) -> None:
        """Dynamically apply aggressive VRAM optimizations for high-resolution generations.

        Prevents Out-Of-Memory (OOM) on high-res output by enabling slicing/tiling/offloading.
        """
        if self.pipeline is None:
            return

        device = self.settings.gpu.device
        is_cuda = torch.cuda.is_available() and device != "cpu"
        if not is_cuda:
            return

        pixel_count = width * height

        # 1. High Resolution (> 1024x1024)
        if pixel_count > 1024 * 1024:
            logger.info(
                "High resolution detected (%dx%d). Enabling VAE tiling and attention slicing.",
                width,
                height,
            )
            try:
                self.pipeline.enable_vae_slicing()
                self.pipeline.enable_vae_tiling()
                self.pipeline.enable_attention_slicing()
            except Exception as e:
                logger.warning("Could not enable high-res VAE/attention slicing: %s", str(e))

        # 2. Extreme Resolution (> 2048x2048, like 4K or 8K)
        if pixel_count > 2048 * 2048:
            logger.info(
                "Extreme resolution detected (%dx%d). "
                "Enabling sequential CPU offloading to prevent OOM.",
                width,
                height,
            )
            try:
                self.pipeline.enable_sequential_cpu_offload()
            except Exception as e:
                logger.warning("Could not enable sequential CPU offload: %s", str(e))
