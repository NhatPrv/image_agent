"""Storage interface.

Defines the contract for storing output images and thumbnails.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PIL import Image


class IStorage(ABC):
    """Abstract interface for file persistence and organization."""

    @abstractmethod
    async def save_image(
        self,
        image: Image.Image,
        directory_name: str,
        filename_prefix: str = "img",
        save_format: str = "png",
    ) -> str:
        """Save a generated image to disk.

        Args:
            image: PIL Image object.
            directory_name: Subfolder name (e.g. "txt2img", "img2img").
            filename_prefix: Prefix for the generated filename.
            save_format: Target format ("png", "jpg", "jpeg", "webp").

        Returns:
            The absolute file path of the saved image.

        Raises:
            StorageError: If saving fails or output format is unsupported.
        """

    @abstractmethod
    async def save_thumbnail(self, image_path: str) -> str:
        """Generate and save a lightweight thumbnail for a saved image.

        Args:
            image_path: Path to the original full-size image.

        Returns:
            The absolute path of the generated thumbnail.

        Raises:
            StorageError: If thumbnail generation fails.
        """

    @abstractmethod
    async def delete_image(self, file_path: str) -> None:
        """Delete an image and its corresponding thumbnail from disk.

        Args:
            file_path: Path to the original image.

        Raises:
            StorageError: If deletion fails.
        """

    @abstractmethod
    async def exists(self, file_path: str) -> bool:
        """Check if a file exists on disk.

        Args:
            file_path: Absolute file path.

        Returns:
            True if file exists, False otherwise.
        """

    @abstractmethod
    def get_thumbnail_path(self, image_path: str) -> str:
        """Get the absolute thumbnail path for a given image path.

        Args:
            image_path: Path to the original full-size image.

        Returns:
            The absolute path of the corresponding thumbnail.
        """
