"""Generation domain entity.

Represents a single image generation request with all its parameters.
This is a pure domain object — no framework dependencies.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums.generation_type import GenerationType
from app.core.enums.scheduler_type import SchedulerType
from app.core.enums.status import GenerationStatus


class GenerationParams(BaseModel):
    """Immutable parameters for an image generation request.

    These are the user-specified inputs that define what to generate.
    """

    model_config = ConfigDict(frozen=True)

    type: GenerationType = GenerationType.TEXT_TO_IMAGE
    prompt: str = Field(..., min_length=1, max_length=2000)
    negative_prompt: str = Field(default="", max_length=2000)
    width: int = Field(default=512, ge=64, le=8192)
    height: int = Field(default=512, ge=64, le=8192)
    steps: int = Field(default=20, ge=1, le=150)
    cfg_scale: float = Field(default=7.0, ge=1.0, le=30.0)
    seed: int = Field(default=-1, ge=-1)
    sampler: SchedulerType = SchedulerType.EULER_A
    clip_skip: int = Field(default=1, ge=1, le=12)
    batch_size: int = Field(default=1, ge=1, le=16)
    model_id: str = ""

    # Optional: Image-to-Image / Inpainting
    input_image_path: str | None = None
    mask_image_path: str | None = None
    denoise_strength: float = Field(default=0.75, ge=0.0, le=1.0)

    # Optional: LoRA
    loras: list[LoRAConfig] | None = None

    # Optional: ControlNet
    controlnet: ControlNetConfig | None = None

    # Extra parameters for future extensibility
    extra: dict[str, Any] = Field(default_factory=dict)


class LoRAConfig(BaseModel):
    """Configuration for a LoRA model."""

    model_config = ConfigDict(frozen=True)

    path: str
    weight: float = Field(default=1.0, ge=-2.0, le=2.0)
    name: str = ""


class ControlNetConfig(BaseModel):
    """Configuration for ControlNet."""

    model_config = ConfigDict(frozen=True)

    model_path: str
    input_image_path: str
    weight: float = Field(default=1.0, ge=0.0, le=2.0)
    guidance_start: float = Field(default=0.0, ge=0.0, le=1.0)
    guidance_end: float = Field(default=1.0, ge=0.0, le=1.0)
    preprocessor: str = "none"


class GenerationEntity(BaseModel):
    """Domain entity representing a complete generation lifecycle.

    Tracks a generation from creation through completion, including
    timing, status, and output information.
    """

    id: str
    params: GenerationParams
    status: GenerationStatus = GenerationStatus.PENDING

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int | None = None

    # Output
    output_images: list[str] = Field(default_factory=list)
    seed_used: int | None = None

    # Error tracking
    error_message: str | None = None

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(cls, params: GenerationParams) -> GenerationEntity:
        """Create a new generation entity from parameters."""
        import uuid

        return cls(
            id=uuid.uuid4().hex,
            params=params,
            status=GenerationStatus.PENDING,
            created_at=datetime.utcnow(),
        )


class GenerationProgress(BaseModel):
    """Real-time progress update during generation."""

    generation_id: str
    current_step: int
    total_steps: int
    progress_percent: float = Field(ge=0.0, le=100.0)
    preview_image_path: str | None = None
    elapsed_ms: int = 0
    estimated_remaining_ms: int = 0
