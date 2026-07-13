"""Unit tests for the AI Engine Core.

Mocks file headers and GPU configurations to test ModelLoader,
SchedulerFactory, and VRAMManager.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from diffusers import DPMSolverMultistepScheduler, EulerAncestralDiscreteScheduler

from app.config.settings import Settings
from app.core.enums.model_type import ModelArchitecture, ModelComponentType, ModelFileFormat
from app.core.enums.scheduler_type import SchedulerType
from app.engine.model_loader import ModelLoader
from app.engine.scheduler_factory import SchedulerFactory
from app.engine.vram_manager import VRAMManager

# ─── Scheduler Factory Tests ───


def test_scheduler_factory_maps_correctly():
    """Verify that SchedulerType maps to the correct Diffusers class."""
    # Mock a basic scheduler configuration dictionary
    mock_config = {
        "num_train_timesteps": 1000,
        "beta_start": 0.00085,
        "beta_end": 0.012,
        "beta_schedule": "scaled_linear",
    }

    # Test Euler Ancestral Discrete Scheduler
    euler_a_sched = SchedulerFactory.create(SchedulerType.EULER_A, mock_config)
    assert isinstance(euler_a_sched, EulerAncestralDiscreteScheduler)

    # Test DPM++ 2M Karras Scheduler
    dpm_karras_sched = SchedulerFactory.create(SchedulerType.DPM_PP_2M_KARRAS, mock_config)
    assert isinstance(dpm_karras_sched, DPMSolverMultistepScheduler)
    assert dpm_karras_sched.config.get("use_karras_sigmas") is True


# ─── VRAM Manager Tests ───


@patch("torch.cuda.is_available")
@patch("torch.cuda.get_device_properties")
def test_vram_manager_monitoring(mock_get_properties, mock_is_available):
    """Verify VRAMManager returns memory numbers correctly."""
    mock_is_available.return_value = True

    # Mock 8GB device properties
    mock_device = MagicMock()
    mock_device.total_memory = 8 * 1024 * 1024 * 1024
    mock_get_properties.return_value = mock_device

    settings = Settings()
    # Mock max usage to 6GB
    settings.gpu.max_vram_usage_mb = 6000.0

    manager = VRAMManager(settings)
    manager._nvml_initialized = False

    # Verify get_vram_info fallback (PyTorch values)
    with (
        patch("torch.cuda.memory_allocated", return_value=0),
        patch("torch.cuda.memory_reserved", return_value=2 * 1024 * 1024 * 1024),
    ):
        used, total, free = manager.get_vram_info()
        assert total == 8192.0
        assert used == 2048.0
        assert free == 6144.0


# ─── Model Loader Tests ───


@pytest.mark.asyncio
@patch("app.engine.model_loader.SafetensorsHeaderParser.read_header")
@patch("pathlib.Path.stat")
@patch("pathlib.Path.exists")
async def test_model_loader_detects_sd15(mock_exists, mock_stat, mock_read_header):
    """Verify ModelLoader parses headers and detects SD 1.5 architecture."""
    mock_exists.return_value = True

    # Mock stat size to 2GB
    mock_size = MagicMock()
    mock_size.st_size = 2 * 1024 * 1024 * 1024
    mock_stat.return_value = mock_size

    # Mock safetensors keys for SD 1.5
    mock_read_header.return_value = {
        "model.diffusion_model.input_blocks.0.0.weight": {"shape": [320, 4, 3, 3]},
        "__metadata__": {"format": "pt"},
    }

    settings = Settings()
    loader = ModelLoader(settings)

    model_path = Path("C:/models/checkpoints/dreamshaper.safetensors")
    info = await loader.get_model_info(model_path)

    assert info.name == "dreamshaper"
    assert info.file_format == ModelFileFormat.SAFETENSORS
    assert info.component_type == ModelComponentType.CHECKPOINT
    assert info.architecture == ModelArchitecture.SD_1_5
    assert info.size_bytes == 2 * 1024 * 1024 * 1024
