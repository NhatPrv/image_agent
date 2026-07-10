"""Settings Endpoints.

REST router for reading and dynamically modifying application configuration parameters.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.schemas import SettingsSchema
from app.di.container import get_settings_dep, get_settings_repository

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.core.interfaces.repositories import ISettingsRepository

router = APIRouter(prefix="/settings", tags=["Settings"])
logger = logging.getLogger(__name__)


@router.get("", response_model=SettingsSchema)
async def get_settings(
    settings: Settings = Depends(get_settings_dep),
) -> SettingsSchema:
    """Retrieve current runtime configuration settings."""
    # Convert Settings object properties to dictionary layout
    return SettingsSchema(
        app={
            "name": settings.app.name,
            "version": settings.app.version,
            "debug": settings.app.debug,
        },
        server={
            "host": settings.server.host,
            "port": settings.server.port,
            "cors_origins": settings.server.cors_origins,
        },
        paths={
            "models_dir": settings.paths.models_dir,
            "outputs_dir": settings.paths.outputs_dir,
            "logs_dir": settings.paths.logs_dir,
        },
        gpu={
            "device": settings.gpu.device,
            "dtype": settings.gpu.dtype,
            "xformers": settings.gpu.xformers,
            "attention_slicing": settings.gpu.attention_slicing,
            "vae_slicing": settings.gpu.vae_slicing,
            "vae_tiling": settings.gpu.vae_tiling,
            "cpu_offload": settings.gpu.cpu_offload,
            "sequential_cpu_offload": settings.gpu.sequential_cpu_offload,
            "torch_compile": settings.gpu.torch_compile,
            "max_vram_usage_mb": settings.gpu.max_vram_usage_mb,
        },
    )


@router.put("", response_model=SettingsSchema)
async def update_settings(
    payload: SettingsSchema,
    settings: Settings = Depends(get_settings_dep),
    repo: ISettingsRepository = Depends(get_settings_repository),
) -> SettingsSchema:
    """Update runtime settings and persist key-value pairs into SQLite database."""
    try:
        # 1. Update active runtime settings object fields
        settings.app.debug = payload.app.debug

        settings.paths.models_dir = payload.paths.models_dir
        settings.paths.outputs_dir = payload.paths.outputs_dir
        settings.paths.logs_dir = payload.paths.logs_dir

        settings.gpu.device = payload.gpu.device
        settings.gpu.dtype = payload.gpu.dtype
        settings.gpu.xformers = payload.gpu.xformers
        settings.gpu.attention_slicing = payload.gpu.attention_slicing
        settings.gpu.vae_slicing = payload.gpu.vae_slicing
        settings.gpu.vae_tiling = payload.gpu.vae_tiling
        settings.gpu.cpu_offload = payload.gpu.cpu_offload
        settings.gpu.sequential_cpu_offload = payload.gpu.sequential_cpu_offload
        settings.gpu.torch_compile = payload.gpu.torch_compile
        settings.gpu.max_vram_usage_mb = payload.gpu.max_vram_usage_mb

        # Ensure directories exist
        settings.paths.ensure_directories()

        # 2. Persist key-values to SQLite database settings table
        # We prefix keys for easy section grouping
        await repo.set("app.debug", str(payload.app.debug))
        await repo.set("paths.models_dir", payload.paths.models_dir)
        await repo.set("paths.outputs_dir", payload.paths.outputs_dir)
        await repo.set("paths.logs_dir", payload.paths.logs_dir)
        await repo.set("gpu.device", payload.gpu.device)
        await repo.set("gpu.dtype", payload.gpu.dtype)
        await repo.set("gpu.xformers", str(payload.gpu.xformers))
        await repo.set("gpu.attention_slicing", str(payload.gpu.attention_slicing))
        await repo.set("gpu.vae_slicing", str(payload.gpu.vae_slicing))
        await repo.set("gpu.vae_tiling", str(payload.gpu.vae_tiling))
        await repo.set("gpu.cpu_offload", str(payload.gpu.cpu_offload))
        await repo.set("gpu.sequential_cpu_offload", str(payload.gpu.sequential_cpu_offload))
        await repo.set("gpu.torch_compile", str(payload.gpu.torch_compile))
        await repo.set("gpu.max_vram_usage_mb", str(payload.gpu.max_vram_usage_mb))

        logger.info("Configuration updated and saved to SQLite settings registry.")
        return payload
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed updating settings: {e}",
        ) from e
