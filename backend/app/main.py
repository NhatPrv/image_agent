"""Main application entry point.

Initializes configuration, logging, database connections, mounts endpoints,
and registers global middleware error handling filters.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.middleware.error_handler import setup_error_handlers
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.v1 import router as api_v1_router
from app.config.logging_config import setup_logging
from app.config.settings import get_settings
from app.infrastructure.database.connection import db_manager

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

# ─── Global setups and configurations ───
settings = get_settings()
settings.paths.ensure_directories()
setup_logging(log_level=settings.app.log_level, logs_dir=settings.paths.logs_dir)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Manages application startup and shutdown lifecycle events."""
    logger.info("Starting up %s (version %s)...", settings.app.name, settings.app.version)

    # 1. Database connection initialization
    db_manager.init(str(settings.paths.database_path.resolve()))
    await db_manager.create_all_tables()

    yield

    # 3. Shutdown connection cleanups
    logger.info("Shutting down %s...", settings.app.name)
    await db_manager.close()


app = FastAPI(
    title=settings.app.name,
    version=settings.app.version,
    description="Local AI Image Generation Platform API",
    lifespan=lifespan,
    docs_url="/docs" if settings.app.debug else None,
    redoc_url="/redoc" if settings.app.debug else None,
)

# ─── Middleware ───
app.add_middleware(RequestLoggingMiddleware)

# Enable CORS for localhost frontend (Electron Renderer)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to native origin later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global custom error handlers
setup_error_handlers(app)

# ─── Mount routes ───
app.include_router(api_v1_router, prefix="/api/v1")

# Mount outputs as static files so generated images/thumbnails can be viewed
# e.g., http://localhost:8000/outputs/txt2img/img_xxxx.png
app.mount(
    "/outputs",
    StaticFiles(directory=str(settings.paths.outputs_dir.resolve())),
    name="outputs",
)

logger.info("Application initialized. Debug mode: %s", settings.app.debug)
