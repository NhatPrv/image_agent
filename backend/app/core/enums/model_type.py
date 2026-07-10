"""Model architecture and type enumerations.

Defines supported model architectures and file formats.
"""

from __future__ import annotations

from enum import StrEnum


class ModelArchitecture(StrEnum):
    """Supported diffusion model architectures."""

    SD_1_5 = "sd_1_5"
    SD_2_1 = "sd_2_1"
    SDXL = "sdxl"
    SDXL_TURBO = "sdxl_turbo"
    SD3 = "sd3"
    FLUX = "flux"
    PONY = "pony"
    ILLUSTRIOUS = "illustrious"
    UNKNOWN = "unknown"


class ModelFileFormat(StrEnum):
    """Supported model file formats."""

    SAFETENSORS = "safetensors"
    CHECKPOINT = "ckpt"
    BIN = "bin"
    ONNX = "onnx"
    GGUF = "gguf"
    DIFFUSERS = "diffusers"  # HuggingFace diffusers format (directory)


class ModelComponentType(StrEnum):
    """Types of model components."""

    CHECKPOINT = "checkpoint"
    LORA = "lora"
    CONTROLNET = "controlnet"
    VAE = "vae"
    UPSCALER = "upscaler"
    EMBEDDING = "embedding"
    HYPERNETWORK = "hypernetwork"
