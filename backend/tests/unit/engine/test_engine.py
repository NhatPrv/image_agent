"""Unit tests for the AI Engine Core.

Mocks file headers and GPU configurations to test ModelLoader,
SchedulerFactory, and VRAMManager.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

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


def test_apply_loras_on_pipeline():
    """Verify that BaseDiffusionPipeline.apply_loras loads and sets adapters properly."""
    from app.engine.pipelines.base import BaseDiffusionPipeline

    settings = Settings()
    pipe_wrapper = BaseDiffusionPipeline(settings)

    # Mock diffusers pipeline object
    mock_pipe = MagicMock()
    pipe_wrapper.pipeline = mock_pipe

    # Call apply_loras with no inputs
    pipe_wrapper.apply_loras(None)
    mock_pipe.unload_lora_weights.assert_called_once()
    mock_pipe.load_lora_weights.assert_not_called()

    # Reset mocks
    mock_pipe.reset_mock()

    # Call apply_loras with some LoRAs
    lora_inputs = [("path/to/lora1.safetensors", 0.75), ("path/to/lora2.safetensors", 0.5)]
    pipe_wrapper.apply_loras(lora_inputs)

    assert mock_pipe.unload_lora_weights.call_count == 1
    assert mock_pipe.load_lora_weights.call_count == 2
    import os
    expected_dir = os.path.normpath("path/to")
    mock_pipe.load_lora_weights.assert_any_call(expected_dir, weight_name="lora1.safetensors", adapter_name="adapter_0")
    mock_pipe.load_lora_weights.assert_any_call(expected_dir, weight_name="lora2.safetensors", adapter_name="adapter_1")

    mock_pipe.set_adapters.assert_called_once_with(["adapter_0", "adapter_1"], adapter_weights=[0.75, 0.5])


@pytest.mark.asyncio
@patch("app.engine.engine_manager.Img2ImgPipeline")
async def test_engine_manager_upscale_dispatch(mock_img2img_class):
    """Verify EngineManager correctly dispatches GenerationType.UPSCALE requests to Img2ImgPipeline."""
    from app.engine.engine_manager import AIEngineManager
    from app.core.entities.generation import GenerationParams
    from app.core.enums.generation_type import GenerationType
    from app.core.entities.model_info import ModelInfo
    from PIL import Image

    # Mock settings, event_bus, storage
    settings = Settings()
    event_bus = AsyncMock()
    storage = AsyncMock()
    # Mock storage saving to return a path
    storage.save_image = AsyncMock(return_value="path/to/upscaled.png")

    manager = AIEngineManager(settings, event_bus, storage)

    # Set active model
    mock_model = ModelInfo(
        id="model_123",
        name="Dreamshaper",
        filename="dreamshaper.safetensors",
        path="C:/models/checkpoints/dreamshaper.safetensors",
        component_type=ModelComponentType.CHECKPOINT,
        architecture=ModelArchitecture.SD_1_5,
        file_format=ModelFileFormat.SAFETENSORS,
        size_bytes=2147483648,
        hash_sha256="hash",
    )
    manager._active_model_info = mock_model

    # Mock img2img pipeline instance
    mock_pipeline_inst = MagicMock()
    mock_pipeline_inst.load = AsyncMock()
    mock_img2img_class.return_value = mock_pipeline_inst
    
    # Return a PIL Image when generating
    mock_image = Image.new("RGB", (1024, 1024))
    mock_pipeline_inst.generate = AsyncMock(return_value=[mock_image])

    # Parameters for upscale
    params = GenerationParams(
        prompt="masterpiece",
        negative_prompt="",
        width=1024,
        height=1024,
        steps=25,
        cfg_scale=7.0,
        seed=-1,
        sampler=SchedulerType.EULER_A,
        model_id="model_123",
        type=GenerationType.UPSCALE,
        input_image_path="path/to/input.png",
        denoise_strength=0.25,
    )

    params.extra["generation_id"] = "gen_123"
    await manager.generate(params, None)

    # Assertions
    # 1. Pipeline instance is created
    mock_img2img_class.assert_called_once_with(settings)
    # 2. generate was called on pipeline wrapper
    mock_pipeline_inst.generate.assert_called_once_with(params, "gen_123", None)
    # 3. Storage was called to save the output image
    storage.save_image.assert_called_once()
