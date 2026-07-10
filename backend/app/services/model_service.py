"""Model Service.

Orchestrates model directory scanning, registration persistence,
and active model loading states.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.exceptions.base import ModelLoadError

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.core.entities.model_info import ModelInfo
    from app.core.interfaces.ai_engine import IAIEngine
    from app.core.interfaces.model_loader import IModelLoader
    from app.core.interfaces.repositories import IModelRepository

logger = logging.getLogger(__name__)


class ModelService:
    """Service handling model metadata scanning and GPU load operations."""

    def __init__(
        self,
        settings: Settings,
        model_repo: IModelRepository,
        model_loader: IModelLoader,
        ai_engine: IAIEngine,
    ) -> None:
        """Initialize the Model Service."""
        self._settings = settings
        self._repo = model_repo
        self._loader = model_loader
        self._engine = ai_engine

    async def get_all_models(self) -> list[ModelInfo]:
        """Fetch all registered models from database."""
        return await self._repo.get_all()

    async def get_active_model(self) -> ModelInfo | None:
        """Get the currently loaded active model info."""
        return self._engine.get_loaded_model()

    async def scan_and_register_models(self) -> list[ModelInfo]:
        """Scan the configured model directories, calculate new hashes, and persist."""
        models_dir = Path(self._settings.paths.models_dir)
        scanned_models = await self._loader.scan_models(models_dir)

        registered_models: list[ModelInfo] = []

        for model in scanned_models:
            # Check if model path already exists in database
            existing = await self._repo.get_by_path(model.path)
            if existing:
                registered_models.append(existing)
                continue

            # Calculate SHA-256 hash for new models (expensive operation)
            logger.info("New model found: %s. Initiating hash registration.", model.filename)
            try:
                model_hash = await self._loader.calculate_hash(Path(model.path))
                model.hash_sha256 = model_hash
            except Exception as e:
                logger.warning("Could not calculate hash for %s: %s", model.filename, str(e))
                model.hash_sha256 = ""

            # Save to repository
            await self._repo.save(model)
            registered_models.append(model)

        # Return full updated list
        return await self._repo.get_all()

    async def load_model(self, model_id: str) -> None:
        """Load a specific model from database by ID into PyTorch memory."""
        model = await self._repo.get_by_id(model_id)
        if not model:
            msg = f"Model with ID '{model_id}' not found in registry."
            raise ModelLoadError(msg, model_path="")

        logger.info("Routing request to load model: %s", model.name)
        await self._engine.load_model(model)

    async def unload_model(self) -> None:
        """Unload the active model and release GPU VRAM."""
        await self._engine.unload_model()
