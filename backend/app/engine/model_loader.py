"""Model Loader implementation.

Scans directories for models, parses metadata headers of safetensors,
identifies model architectures (SD 1.5, SDXL, etc.), and calculates file hashes.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import struct
import uuid
from typing import TYPE_CHECKING

from app.core.entities.model_info import ModelInfo
from app.core.enums.model_type import (
    ModelArchitecture,
    ModelComponentType,
    ModelFileFormat,
)
from app.core.exceptions.base import ImageFileNotFoundError, ModelLoadError
from app.core.interfaces.model_loader import IModelLoader

if TYPE_CHECKING:
    from pathlib import Path

    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class SafetensorsHeaderParser:
    """Helper to parse the JSON header block from a safetensors file.

    Zero-copy approach: only reads the header prefix bytes from disk.
    """

    @classmethod
    def read_header(cls, file_path: Path) -> dict:
        """Read the JSON header metadata from a safetensors file.

        The safetensors format starts with an 8-byte little-endian unsigned integer
        indicating the length of the JSON header, followed by the JSON string itself.
        """
        try:
            with file_path.open("rb") as f:
                # 1. Read first 8 bytes for header size
                header_size_bytes = f.read(8)
                if len(header_size_bytes) < 8:
                    msg = "Invalid file header: less than 8 bytes."
                    raise ValueError(msg)

                header_size = struct.unpack("<Q", header_size_bytes)[0]

                # 2. Read the header bytes
                header_json_bytes = f.read(header_size)
                if len(header_json_bytes) < header_size:
                    msg = "Truncated file: header section is shorter than expected."
                    raise ValueError(msg)

                return json.loads(header_json_bytes.decode("utf-8"))
        except Exception as e:
            logger.error(
                "Failed to parse safetensors header for %s: %s",
                file_path.name,
                str(e),
            )
            return {}


class ModelLoader(IModelLoader):
    """Local model scanner and loader."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the model loader.

        Args:
            settings: Application configurations.
        """
        self._settings = settings

    async def scan_models(self, directory: Path) -> list[ModelInfo]:
        """Recursively scan a directory for supported model formats."""
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            return []

        logger.info("Scanning directory for model checkpoints: %s", directory)
        supported_extensions = {".safetensors", ".ckpt"}
        models: list[ModelInfo] = []

        loop = asyncio.get_running_loop()

        # Read directory listing in a thread pool to avoid blocking I/O
        def _list_files():
            return [
                p
                for p in directory.rglob("*")
                if p.is_file() and p.suffix.lower() in supported_extensions
            ]

        try:
            file_list = await loop.run_in_executor(None, _list_files)
        except Exception as e:
            logger.error("Failed listing files in directory %s: %s", directory, str(e))
            return []

        for file_path in file_list:
            try:
                model_info = await self.get_model_info(file_path)
                models.append(model_info)
            except Exception as e:
                logger.warning("Skipping invalid model file %s: %s", file_path.name, str(e))

        logger.info("Successfully scanned and identified %d models.", len(models))
        return models

    async def get_model_info(self, file_path: Path) -> ModelInfo:
        """Retrieve model metadata by checking headers asynchronously."""
        if not file_path.exists():
            msg = f"Model file not found: {file_path}"
            raise ImageFileNotFoundError(msg, path=str(file_path))

        loop = asyncio.get_running_loop()

        # Read file size in thread pool
        size_bytes = await loop.run_in_executor(None, lambda: file_path.stat().st_size)

        ext = file_path.suffix.lower()
        is_safetensors = ext == ".safetensors"
        file_format = ModelFileFormat.SAFETENSORS if is_safetensors else ModelFileFormat.CHECKPOINT

        # Estimate type and architecture by reading headers
        component_type = ModelComponentType.CHECKPOINT
        architecture = ModelArchitecture.UNKNOWN
        metadata = {}

        if file_format == ModelFileFormat.SAFETENSORS:
            # Safetensors allow fast key list extraction
            header = await loop.run_in_executor(
                None, lambda: SafetensorsHeaderParser.read_header(file_path)
            )

            # Identify base architecture and component type from header keys
            architecture = self._detect_architecture(header)
            component_type = self._detect_component_type(header)

            # Extract optional custom metadata embedded in safetensors
            if "__metadata__" in header:
                metadata = header["__metadata__"]

        # Fill display properties
        name = file_path.stem
        filename = file_path.name

        # Calculate ID from filename (we compute SHA-256 for actual registration)
        model_id = uuid.uuid5(uuid.NAMESPACE_DNS, str(file_path.resolve())).hex

        return ModelInfo(
            id=model_id,
            name=name,
            filename=filename,
            path=str(file_path.resolve()),
            component_type=component_type,
            architecture=architecture,
            file_format=file_format,
            size_bytes=size_bytes,
            hash_sha256="",  # Hashing is expensive; call calculate_hash separately when register
            metadata=metadata,
        )

    async def calculate_hash(self, file_path: Path) -> str:
        """Calculate the SHA-256 hash of the model.

        To prevent blocking, the hash is calculated block-by-block in the executor.
        """
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise ImageFileNotFoundError(msg, path=str(file_path))

        loop = asyncio.get_running_loop()

        def _calculate():
            logger.info("Starting SHA-256 hash calculation for %s...", file_path.name)
            sha256_hash = hashlib.sha256()
            # Read in 8MB chunks
            chunk_size = 8 * 1024 * 1024
            with file_path.open("rb") as f:
                for byte_block in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(byte_block)
            hash_str = sha256_hash.hexdigest()
            logger.info("Completed hash calculation for %s: %s", file_path.name, hash_str)
            return hash_str

        try:
            return await loop.run_in_executor(None, _calculate)
        except Exception as e:
            logger.error("Failed calculating SHA-256 hash for %s: %s", file_path.name, str(e))
            msg = f"Hash calculation failed: {e}"
            raise ModelLoadError(msg, model_path=str(file_path)) from e

    def _detect_architecture(self, header: dict) -> ModelArchitecture:
        """Detect model architecture (SD 1.5, SDXL, etc.) based on safetensors keys."""
        if not header:
            return ModelArchitecture.UNKNOWN

        # 1. SDXL checking
        # SDXL uses custom label embedding layers and dual text encoder architectures
        has_sdxl = any(
            "conditioner.embedders.1" in k or "model.diffusion_model.label_emb" in k
            for k in header
        )
        if has_sdxl:
            return ModelArchitecture.SDXL

        # 2. SD 1.5 checking
        # SD 1.5 has input blocks and attention structures matching the unet
        if any("model.diffusion_model.input_blocks.0.0.weight" in k for k in header):
            return ModelArchitecture.SD_1_5

        # 3. SD 2.1 checking
        # SD 2.1 has custom input dims, unet keys look similar to SD 1.5.
        # Default to SD 1.5 if standard unet input blocks exist without SDXL.

        # 4. Flux/SD3 checking
        if any("double_blocks" in k or "single_blocks" in k for k in header):
            return ModelArchitecture.FLUX

        if any("joint_blocks" in k for k in header):
            return ModelArchitecture.SD3

        return ModelArchitecture.UNKNOWN

    def _detect_component_type(self, header: dict) -> ModelComponentType:
        """Identify if a file is a Checkpoint, LoRA, VAE, or ControlNet."""
        if not header:
            return ModelComponentType.CHECKPOINT

        # LoRA detection: contains keys like lora_te_text_model_encoder...
        # Standard LoRAs keys contain "lora_up" or "lora_down"
        if any("lora_up" in k or "lora_down" in k or "lora_cpu" in k for k in header):
            return ModelComponentType.LORA

        # ControlNet detection: unet key structure contains "control_model"
        if any("control_model" in k or "input_hint_block" in k for k in header):
            return ModelComponentType.CONTROLNET

        # VAE detection: contains encoder/decoder structures only
        if any(
            "encoder.down.0" in k and "decoder.up.0" in k and "model.diffusion_model" not in k
            for k in header
        ):
            return ModelComponentType.VAE

        return ModelComponentType.CHECKPOINT
