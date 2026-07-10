"""GPU VRAM Manager.

Monitors GPU VRAM usage using NVML and PyTorch. Establishes safety checks
and provides warning triggers for potential Out-Of-Memory (OOM) states.
"""

from __future__ import annotations

import gc
import logging
from typing import TYPE_CHECKING

import torch

try:
    import pynvml

    HAS_PYNVML = True
except ImportError:
    HAS_PYNVML = False

import contextlib

from app.core.exceptions.base import CUDAError, VRAMInsufficientError

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class VRAMManager:
    """Manages and monitors GPU memory.

    Provides monitoring capabilities and safety triggers to prevent CUDA OOM issues.
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize the VRAM manager.

        Args:
            settings: Unified application configuration.
        """
        self._settings = settings
        self._nvml_initialized = False

        if HAS_PYNVML:
            try:
                pynvml.nvmlInit()
                self._nvml_initialized = True
                logger.info("NVML initialized successfully for GPU monitoring.")
            except Exception as e:
                logger.warning("Failed to initialize NVML. Falling back to PyTorch: %s", str(e))

    def __del__(self) -> None:
        """Clean up NVML bindings on destruction."""
        if self._nvml_initialized:
            with contextlib.suppress(Exception):
                pynvml.nvmlShutdown()

    def get_vram_info(self) -> tuple[float, float, float]:
        """Get VRAM usage status.

        Returns:
            A tuple containing: (used_mb, total_mb, free_mb)
        """
        if not torch.cuda.is_available():
            # Return empty/fallback values if running on CPU
            return 0.0, 0.0, 0.0

        if self._nvml_initialized:
            try:
                # Use NVML to get absolute system-wide GPU memory
                device_idx = torch.cuda.current_device()
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_idx)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                used_mb = info.used / (1024 * 1024)
                total_mb = info.total / (1024 * 1024)
                free_mb = info.free / (1024 * 1024)
                return used_mb, total_mb, free_mb
            except Exception as e:
                logger.warning("NVML read failed, falling back to PyTorch: %s", str(e))

        # Fallback: PyTorch tracking (tracks PyTorch-allocated memory, not system-wide)
        total_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
        torch.cuda.memory_allocated(0) / (1024 * 1024)
        reserved_mb = torch.cuda.memory_reserved(0) / (1024 * 1024)

        # Estimate used as reserved, and free as total - reserved
        return reserved_mb, total_mb, total_mb - reserved_mb

    def get_vram_percentage(self) -> float:
        """Get VRAM usage percentage (0.0 to 100.0)."""
        used_mb, total_mb, _ = self.get_vram_info()
        if total_mb <= 0.0:
            return 0.0
        return (used_mb / total_mb) * 100.0

    def check_vram_safety(self, required_mb: float) -> None:
        """Verify if the GPU has enough free VRAM for an operation.

        Args:
            required_mb: Estimated VRAM needed in MB.

        Raises:
            VRAMInsufficientError: If memory is below safe threshold.
        """
        if not torch.cuda.is_available():
            if self._settings.gpu.device != "cpu":
                msg = "CUDA is not available. Please run in CPU mode."
                raise CUDAError(msg)
            return

        used_mb, total_mb, free_mb = self.get_vram_info()

        # Calculate maximum usable VRAM threshold based on configuration
        max_usable = min(self._settings.gpu.max_vram_usage_mb, total_mb)
        current_available = max(0.0, max_usable - used_mb)

        logger.debug(
            "VRAM check │ Required: %.1fMB, System Free: %.1fMB, App Available: %.1fMB",
            required_mb,
            free_mb,
            current_available,
        )

        if required_mb > current_available:
            logger.warning(
                "OOM Risk! Insufficient VRAM. Required: %.1fMB, Available: %.1fMB",
                required_mb,
                current_available,
            )
            msg = (
                f"Required VRAM ({required_mb:.0f}MB) exceeds available VRAM "
                f"({current_available:.0f}MB) on card limit ({max_usable:.0f}MB)."
            )
            raise VRAMInsufficientError(
                msg,
                required_mb=int(required_mb),
                available_mb=int(current_available),
            )

    def clean_memory(self) -> None:
        """Clean PyTorch memory cache and garbage collect unused tensors.

        Forces release of cached CUDA blocks back to the OS.
        """
        if not torch.cuda.is_available():
            return

        logger.debug("Executing PyTorch garbage collection and clearing CUDA cache.")
        gc.collect()
        torch.cuda.empty_cache()

        # Reset peak memory stats to start tracking clean
        torch.cuda.reset_peak_memory_stats()
