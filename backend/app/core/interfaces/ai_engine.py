"""AI Engine interface.

Defines the contract for the core image generation AI engine.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from app.core.entities.generation import GenerationParams, GenerationProgress
    from app.core.entities.model_info import ModelInfo


class IAIEngine(ABC):
    """Abstract interface for the AI Generation Engine."""

    @abstractmethod
    async def generate(
        self,
        params: GenerationParams,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[str]:
        """Generate images based on the provided parameters.

        Args:
            params: Parameters for the generation request (prompt, steps, etc.).
            progress_callback: Optional async or sync callable for real-time progress updates.

        Returns:
            A list of paths to the generated output images.

        Raises:
            EngineError: If an error occurs during inference.
            ModelNotLoadedError: If no active model is loaded.
        """

    @abstractmethod
    async def load_model(self, model: ModelInfo) -> None:
        """Load an AI model into GPU memory.

        Args:
            model: Model information entity to be loaded.

        Raises:
            ModelLoadError: If loading fails.
            VRAMInsufficientError: If target device does not have enough VRAM.
        """

    @abstractmethod
    async def unload_model(self) -> None:
        """Unload the currently loaded model and free GPU/VRAM resources."""

    @abstractmethod
    def get_loaded_model(self) -> ModelInfo | None:
        """Get information about the currently loaded model.

        Returns:
            ModelInfo if a model is loaded, otherwise None.
        """

    @abstractmethod
    def is_model_loaded(self) -> bool:
        """Check if any model is currently loaded.

        Returns:
            True if a model is loaded, False otherwise.
        """
