"""Model loader interface.

Defines the contract for scanning and loading model metadata from disk.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from app.core.entities.model_info import ModelInfo


class IModelLoader(ABC):
    """Abstract interface for scanning, parsing, and verifying model files."""

    @abstractmethod
    async def scan_models(self, directory: Path) -> list[ModelInfo]:
        """Scan a directory recursively for supported model files and extract metadata.

        Args:
            directory: Directory to scan.

        Returns:
            A list of detected ModelInfo entities.
        """

    @abstractmethod
    async def get_model_info(self, file_path: Path) -> ModelInfo:
        """Parse a single model file and retrieve its metadata.

        Args:
            file_path: Path to the model file.

        Returns:
            ModelInfo containing detected file format, architecture, and size.

        Raises:
            ModelLoadError: If parsing or metadata extraction fails.
        """

    @abstractmethod
    async def calculate_hash(self, file_path: Path) -> str:
        """Calculate the SHA-256 hash of a model file for integrity checks.

        Args:
            file_path: Path to the file.

        Returns:
            The hex digest of the SHA-256 hash.
        """
