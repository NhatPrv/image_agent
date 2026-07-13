"""API Schemas.

Pydantic DTO models for REST request and response validation.
"""

# NOTE: Do NOT add `from __future__ import annotations` here.
# Pydantic v2 TypeAdapter requires all annotations to be resolvable at
# runtime. The future-annotations import makes them lazy strings, which
# breaks TypeAdapter.rebuild() and causes PydanticUserError at request time.

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums.generation_type import GenerationType
from app.core.enums.model_type import ModelArchitecture, ModelComponentType, ModelFileFormat
from app.core.enums.scheduler_type import SchedulerType
from app.core.enums.status import GenerationStatus, QueueItemStatus, QueuePriority

# ─── Model Schemas ───


class ModelInfoResponse(BaseModel):
    """Details about a scanned or registered AI model."""

    id: str
    name: str
    filename: str
    path: str
    component_type: ModelComponentType
    architecture: ModelArchitecture
    file_format: ModelFileFormat
    size_bytes: int
    hash_sha256: str
    metadata: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)


class ModelLoadRequest(BaseModel):
    """Payload to request loading a model into GPU memory."""

    model_id: str


# ─── Generation Schemas ───


class GenerateRequest(BaseModel):
    """Payload to initiate a new image generation request."""

    prompt: str = Field(..., min_length=1, description="Text prompt guiding the image generation.")
    negative_prompt: str = Field(default="", description="Text prompt specifying what to avoid.")
    width: int = Field(default=512, ge=128, le=2048)
    height: int = Field(default=512, ge=128, le=2048)
    steps: int = Field(default=20, ge=1, le=150)
    cfg_scale: float = Field(default=7.5, ge=1.0, le=30.0)
    seed: int = Field(default=-1, description="-1 represents random seed initialization.")
    sampler: SchedulerType = Field(default=SchedulerType.EULER_A)
    model_id: str = Field(..., description="ID of the model to execute inference against.")

    # Img2Img / Inpaint specific
    type: GenerationType = Field(default=GenerationType.TEXT_TO_IMAGE)
    input_image_path: str | None = Field(default=None)
    mask_image_path: str | None = Field(default=None)
    denoise_strength: float = Field(default=0.75, ge=0.0, le=1.0)

    # Scheduler priority
    priority: QueuePriority = Field(default=QueuePriority.NORMAL)


class ImageRecordResponse(BaseModel):
    """Details of a generated image file."""

    id: str
    generation_id: str
    path: str
    thumbnail_path: str
    width: int
    height: int
    format: str
    size_bytes: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerationResponse(BaseModel):
    """High-level details of a generation record."""

    id: str
    status: GenerationStatus
    created_at: datetime
    completed_at: datetime | None
    duration_ms: int | None
    error_message: str | None

    # Nested schemas
    params: dict[str, Any]
    images: list[ImageRecordResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ─── Queue Schemas ───


class QueueItemResponse(BaseModel):
    """Active priority queue node state."""

    id: str
    generation_id: str
    priority: QueuePriority
    status: QueueItemStatus
    position: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── System Monitor Schemas ───


class CpuStats(BaseModel):
    usage_percent: float
    cores: int


class RamStats(BaseModel):
    used_mb: int
    total_mb: int
    usage_percent: float


class DiskStats(BaseModel):
    used_gb: float
    total_gb: float
    usage_percent: float


class GpuStats(BaseModel):
    cuda_available: bool
    device_name: str
    vram_used_mb: float
    vram_total_mb: float
    vram_usage_percent: float


class SystemStatsResponse(BaseModel):
    """Response containing general system monitor details."""

    platform: str
    platform_version: str
    python_version: str
    cpu: CpuStats
    ram: RamStats
    disk: DiskStats
    gpu: GpuStats


# ─── Settings Schemas ───


class AppSettingsSchema(BaseModel):
    name: str
    version: str
    debug: bool


class ServerSettingsSchema(BaseModel):
    host: str
    port: int
    cors_origins: list[str]


class PathSettingsSchema(BaseModel):
    models_dir: str
    outputs_dir: str
    logs_dir: str


class GpuSettingsSchema(BaseModel):
    device: str
    dtype: str
    xformers: bool
    attention_slicing: bool
    vae_slicing: bool
    vae_tiling: bool
    cpu_offload: bool
    sequential_cpu_offload: bool
    torch_compile: bool
    max_vram_usage_mb: float


class SettingsSchema(BaseModel):
    """Unified application configurations schema."""

    app: AppSettingsSchema
    server: ServerSettingsSchema
    paths: PathSettingsSchema
    gpu: GpuSettingsSchema
