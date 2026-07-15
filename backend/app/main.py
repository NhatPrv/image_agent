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
from app.api.v1.endpoints.websocket import router as ws_router
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

    # 2. Start background Queue Worker
    from app.di.container import (
        get_ai_engine,
        get_event_bus,
        get_queue_manager,
        get_queue_worker,
        get_storage,
    )

    bus = get_event_bus()
    storage = get_storage(settings)
    queue_mgr = get_queue_manager(settings)
    engine = get_ai_engine(settings, bus, storage)
    worker = get_queue_worker(queue_mgr, engine)
    worker.start()

    # 3. On first startup, scan models and auto-load the first available model.
    # This uses a short-lived DB session context to register scanned models
    # and then instruct the engine to load the first model discovered.
    from app.core.entities.generation import GenerationParams
    from app.core.enums.scheduler_type import SchedulerType
    from app.core.enums.status import QueuePriority
    from app.di.container import get_services_context

    try:
        async with get_services_context() as (gen_service, model_service):
            # Sync outputs folder to database so existing local images appear in gallery
            try:
                await gen_service.sync_output_folder_to_db()
            except Exception as e:
                logger.warning("Failed to sync outputs folder to database: %s", str(e))

            models = await model_service.scan_and_register_models()
            if models:
                first = models[0]
                logger.info("Auto-loading first discovered model: %s", first.name)
                try:
                    await model_service.load_model(first.id)
                except Exception as e:
                    logger.warning("Auto-load of model failed: %s", str(e))

                # Enqueue a lightweight startup generation to validate pipeline end-to-end.
                try:
                    params = GenerationParams(
                        prompt="Startup test image",
                        negative_prompt="",
                        width=256,
                        height=256,
                        steps=10,
                        cfg_scale=7.5,
                        seed=-1,
                        sampler=SchedulerType.EULER_A,
                        model_id=first.id,
                    )
                    await gen_service.create_generation(params, QueuePriority.NORMAL)
                    logger.info(
                        "Startup test generation enqueued (generation will run in background)."
                    )
                except Exception as e:
                    logger.warning("Failed to enqueue startup test generation: %s", str(e))
    except Exception as e:
        logger.warning("Model auto-scan/load during startup failed: %s", str(e))

    yield

    # 3. Shutdown connection cleanups
    logger.info("Shutting down %s...", settings.app.name)

    # Stop QueueWorker loop
    try:
        await worker.stop()
    except Exception as e:
        logger.error("Failed to stop queue worker: %s", str(e))

    # Stop WebSocket monitor stats loop
    try:
        from app.api.v1.endpoints.websocket import stop_system_monitor_loop

        stop_system_monitor_loop()
    except Exception:
        pass

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

# Mount WebSocket at root /ws (no prefix) so the frontend can connect to
# ws://127.0.0.1:8000/ws directly without needing the /api/v1 prefix.
# CORSMiddleware does not apply to WebSocket — we handle origins via
# uvicorn's ws_ping_interval=None which disables the strict origin check.
app.include_router(ws_router)

# Mount outputs as static files so generated images/thumbnails can be viewed
# e.g., http://localhost:8000/outputs/txt2img/img_xxxx.png
app.mount(
    "/outputs",
    StaticFiles(directory=str(settings.paths.outputs_dir.resolve())),
    name="outputs",
)

logger.info("Application initialized. Debug mode: %s", settings.app.debug)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=False,  # reload not supported when running as __main__
        log_level="debug" if settings.app.debug else "info",
        ws_ping_interval=None,
        ws_max_size=16 * 1024 * 1024,  # 16 MB
    )
