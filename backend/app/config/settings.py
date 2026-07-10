"""Application configuration using Pydantic Settings.

Centralized configuration management with environment variable support,
validation, and sensible defaults optimized for RTX 4060 8GB VRAM.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_project_root() -> Path:
    """Get the project root directory (parent of backend/)."""
    return Path(__file__).resolve().parent.parent.parent.parent


class AppSettings(BaseSettings):
    """Core application settings."""

    model_config = SettingsConfigDict(env_prefix="APP_")

    name: str = "Image Agent"
    version: str = "0.1.0"
    env: Literal["development", "production", "testing"] = "development"
    debug: bool = True
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"

    @property
    def is_development(self) -> bool:
        return self.env == "development"

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_testing(self) -> bool:
        return self.env == "testing"


class ServerSettings(BaseSettings):
    """HTTP server settings."""

    model_config = SettingsConfigDict(env_prefix="SERVER_")

    host: str = "127.0.0.1"
    port: int = 8000
    workers: int = 1
    reload: bool = False


class PathSettings(BaseSettings):
    """File system path settings.

    All paths default to locations relative to the project root.
    Can be overridden via environment variables for custom setups.
    """

    model_config = SettingsConfigDict(env_prefix="")

    models_dir: Path | None = Field(default=None)
    outputs_dir: Path | None = Field(default=None)
    database_path: Path | None = Field(default=None)
    logs_dir: Path | None = Field(default=None)
    plugins_dir: Path | None = Field(default=None)
    thumbnails_dir: Path | None = Field(default=None)

    def model_post_init(self, __context: object) -> None:
        """Set default paths relative to project root if not provided."""
        root = _get_project_root()

        if self.models_dir is None:
            self.models_dir = root / "models"
        if self.outputs_dir is None:
            self.outputs_dir = root / "outputs"
        if self.database_path is None:
            self.database_path = root / "data" / "image_agent.db"
        if self.logs_dir is None:
            self.logs_dir = root / "logs"
        if self.plugins_dir is None:
            self.plugins_dir = root / "plugins"
        if self.thumbnails_dir is None:
            self.thumbnails_dir = root / "outputs" / "thumbnails"

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        directories = [
            self.models_dir,
            self.models_dir / "checkpoints",
            self.models_dir / "loras",
            self.models_dir / "controlnet",
            self.models_dir / "upscalers",
            self.models_dir / "vae",
            self.models_dir / "embeddings",
            self.outputs_dir,
            self.outputs_dir / "txt2img",
            self.outputs_dir / "img2img",
            self.outputs_dir / "inpaint",
            self.outputs_dir / "upscale",
            self.thumbnails_dir,
            self.logs_dir,
            self.plugins_dir,
            self.plugins_dir / "installed",
            self.database_path.parent,
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


class GPUSettings(BaseSettings):
    """GPU and VRAM optimization settings.

    Defaults optimized for NVIDIA RTX 4060 Laptop 8GB VRAM.
    """

    model_config = SettingsConfigDict(env_prefix="GPU_")

    device: Literal["auto", "cuda", "cpu"] = "auto"
    dtype: Literal["float16", "float32", "bfloat16"] = "float16"
    xformers: bool = True
    attention_slicing: bool = False
    vae_slicing: bool = True
    vae_tiling: bool = False
    cpu_offload: bool = False
    sequential_cpu_offload: bool = False
    max_vram_usage_mb: int = 7680  # 7.5GB of 8GB, leave 512MB for system
    torch_compile: bool = False

    @property
    def torch_dtype(self) -> str:
        """Get the torch dtype string for pipeline configuration."""
        return {
            "float16": "torch.float16",
            "float32": "torch.float32",
            "bfloat16": "torch.bfloat16",
        }[self.dtype]


class GenerationDefaults(BaseSettings):
    """Default values for image generation parameters."""

    model_config = SettingsConfigDict(env_prefix="DEFAULT_")

    steps: int = Field(default=20, ge=1, le=150)
    cfg_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    width: int = Field(default=512, ge=64, le=2048)
    height: int = Field(default=512, ge=64, le=2048)
    sampler: str = "euler_a"
    clip_skip: int = Field(default=1, ge=1, le=12)
    batch_size: int = Field(default=1, ge=1, le=16)

    @field_validator("width", "height")
    @classmethod
    def must_be_multiple_of_8(cls, v: int) -> int:
        """Width and height must be multiples of 8 for stable diffusion."""
        if v % 8 != 0:
            msg = f"Must be a multiple of 8, got {v}"
            raise ValueError(msg)
        return v


class Settings(BaseSettings):
    """Unified application settings.

    Combines all setting groups into a single access point.
    Usage:
        settings = Settings()
        print(settings.app.name)
        print(settings.gpu.device)
    """

    app: AppSettings = Field(default_factory=AppSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    paths: PathSettings = Field(default_factory=PathSettings)
    gpu: GPUSettings = Field(default_factory=GPUSettings)
    generation: GenerationDefaults = Field(default_factory=GenerationDefaults)


# ─── Singleton instance ───
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get the global settings singleton.

    Returns:
        The application settings instance.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings singleton. Used in testing."""
    global _settings
    _settings = None
