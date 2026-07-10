"""System Service.

Monitors CPU, RAM, GPU, Disk, and VRAM status. Resilient against missing
external libraries by using subprocess fallbacks on Windows.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
import subprocess
import sys
from typing import TYPE_CHECKING, Any

import torch

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from app.engine.vram_manager import VRAMManager

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class SystemService:
    """Service providing hardware resource monitoring statistics."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the System Service."""
        self._settings = settings
        self._vram_manager = VRAMManager(settings)

    def get_system_stats(self) -> dict[str, Any]:
        """Collect current resource metrics (CPU, RAM, GPU, Disk)."""
        # 1. CPU usage
        cpu_usage = self._get_cpu_usage()

        # 2. RAM usage
        ram_used, ram_total = self._get_ram_usage()

        # 3. Disk space
        disk_used, disk_total = self._get_disk_usage()

        # 4. GPU & VRAM info
        gpu_name = "CPU Mode"
        vram_used = 0.0
        vram_total = 0.0
        cuda_available = torch.cuda.is_available()

        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            vram_used, vram_total, _ = self._vram_manager.get_vram_info()

        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version.split()[0],
            "cpu": {
                "usage_percent": cpu_usage,
                "cores": os.cpu_count() or 0,
            },
            "ram": {
                "used_mb": int(ram_used),
                "total_mb": int(ram_total),
                "usage_percent": round((ram_used / ram_total) * 100.0, 1)
                if ram_total > 0
                else 0.0,
            },
            "disk": {
                "used_gb": round(disk_used, 1),
                "total_gb": round(disk_total, 1),
                "usage_percent": round((disk_used / disk_total) * 100.0, 1)
                if disk_total > 0
                else 0.0,
            },
            "gpu": {
                "cuda_available": cuda_available,
                "device_name": gpu_name,
                "vram_used_mb": round(vram_used, 1),
                "vram_total_mb": round(vram_total, 1),
                "vram_usage_percent": round((vram_used / vram_total) * 100.0, 1)
                if vram_total > 0
                else 0.0,
            },
        }

    def _get_cpu_usage(self) -> float:
        """Fetch overall CPU utilization percentage."""
        if HAS_PSUTIL:
            try:
                return psutil.cpu_percent(interval=None) or 0.0
            except Exception:
                pass

        if platform.system() == "Windows":
            try:
                # Fallback: call wmic cpu get loadpercentage
                out = subprocess.check_output(
                    "wmic cpu get loadpercentage /Value",
                    shell=True,
                    text=True,
                )
                for line in out.splitlines():
                    if "LoadPercentage" in line:
                        return float(line.split("=")[1].strip())
            except Exception:
                pass
        return 0.0

    def _get_ram_usage(self) -> tuple[float, float]:
        """Fetch RAM metrics in MB. Return tuple: (used_mb, total_mb)."""
        if HAS_PSUTIL:
            try:
                mem = psutil.virtual_memory()
                return (mem.total - mem.available) / (1024 * 1024), mem.total / (1024 * 1024)
            except Exception:
                pass

        # Windows wmic fallback
        if platform.system() == "Windows":
            try:
                out = subprocess.check_output(
                    "wmic OS get FreePhysicalMemory,TotalVisibleMemorySize /Value",
                    shell=True,
                    text=True,
                )
                free_kb = 0.0
                total_kb = 0.0
                for line in out.splitlines():
                    if "FreePhysicalMemory" in line:
                        free_kb = float(line.split("=")[1].strip())
                    elif "TotalVisibleMemorySize" in line:
                        total_kb = float(line.split("=")[1].strip())
                if total_kb > 0:
                    used_mb = (total_kb - free_kb) / 1024.0
                    total_mb = total_kb / 1024.0
                    return used_mb, total_mb
            except Exception:
                pass

        # Fallback default values (e.g. 8GB dummy)
        return 4096.0, 8192.0

    def _get_disk_usage(self) -> tuple[float, float]:
        """Fetch Disk space metrics in GB. Return tuple: (used_gb, total_gb)."""
        try:
            # Use shutil which is portable and doesn't require psutil
            total, _, free = shutil.disk_usage(".")
            used_gb = (total - free) / (1024 * 1024 * 1024)
            total_gb = total / (1024 * 1024 * 1024)
            return used_gb, total_gb
        except Exception as e:
            logger.warning("Failed to determine disk usage: %s", str(e))
            return 0.0, 1.0
