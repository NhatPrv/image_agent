"""Local file storage implementation.

Saves generated images and generates thumbnails using Pillow.
File writes are offloaded to an async executor to prevent blocking.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import Image

from app.core.exceptions.base import ImageFileNotFoundError, StorageError
from app.core.interfaces.storage import IStorage

if TYPE_CHECKING:
    from app.config.settings import Settings

logger = logging.getLogger(__name__)


class LocalFileStorage(IStorage):
    """Local disk storage implementation using Pillow and OS filesystem."""

    def __init__(self, settings: Settings) -> None:
        """Initialize the storage manager.

        Args:
            settings: Unified application configuration.
        """
        self._settings = settings

    async def save_image(
        self,
        image: Image.Image,
        directory_name: str,
        filename_prefix: str = "img",
        save_format: str = "png",
    ) -> str:
        """Save a generated image to disk asynchronously.

        Args:
            image: PIL Image object.
            directory_name: Folder under output directory (e.g. "txt2img").
            filename_prefix: Prefix for filename.
            save_format: Image file extension / format.

        Returns:
            The absolute file path of the saved image.
        """
        # Ensure directories exist
        target_dir = self._settings.paths.outputs_dir / directory_name
        target_dir.mkdir(parents=True, exist_ok=True)

        # Generate a unique filename using UUID to avoid collisions
        unique_id = uuid.uuid4().hex[:8]
        filename = f"{filename_prefix}_{unique_id}.{save_format}"
        file_path = target_dir / filename

        loop = asyncio.get_running_loop()
        try:
            # Save the image using threadpool executor to avoid blocking the event loop
            await loop.run_in_executor(
                None,
                lambda: image.save(file_path, format=save_format.upper()),
            )
            logger.info("Saved image to disk: %s", file_path)
            return str(file_path.resolve())
        except Exception as e:
            logger.error("Failed to write image file: %s", str(e))
            msg = f"Failed to save image {filename}: {e}"
            raise StorageError(msg) from e

    async def save_thumbnail(self, image_path: str) -> str:
        """Generate and save a thumbnail (typically WebP) from a high-res image.

        Args:
            image_path: Path to the original full-size image.

        Returns:
            The absolute path of the generated thumbnail.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            msg = f"Cannot generate thumbnail, original image not found: {image_path}"
            raise ImageFileNotFoundError(msg, path=image_path)

        thumbnail_dir = self._settings.paths.thumbnails_dir
        thumbnail_dir.mkdir(parents=True, exist_ok=True)

        thumbnail_filename = f"{img_path.stem}_thumb.webp"
        thumbnail_path = thumbnail_dir / thumbnail_filename

        loop = asyncio.get_running_loop()
        try:

            def _generate_thumb():
                with Image.open(img_path) as img:
                    # Create thumbnail with anti-aliasing
                    img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                    img.save(thumbnail_path, format="WEBP", quality=85)

            await loop.run_in_executor(None, _generate_thumb)
            logger.info("Generated thumbnail: %s", thumbnail_path)
            return str(thumbnail_path.resolve())
        except Exception as e:
            logger.error("Failed to create thumbnail: %s", str(e))
            msg = f"Failed to generate thumbnail for {image_path}: {e}"
            raise StorageError(msg) from e

    async def delete_image(self, file_path: str) -> None:
        """Delete an image and its corresponding thumbnail from disk."""
        img_path = Path(file_path)
        loop = asyncio.get_running_loop()

        def _delete_files():
            # Delete original image
            if img_path.exists():
                img_path.unlink()
                logger.info("Deleted original image file: %s", file_path)

            # Search and delete associated thumbnail
            thumbnail_dir = self._settings.paths.thumbnails_dir
            thumbnail_filename = f"{img_path.stem}_thumb.webp"
            thumbnail_path = thumbnail_dir / thumbnail_filename
            if thumbnail_path.exists():
                thumbnail_path.unlink()
                logger.info("Deleted thumbnail file: %s", thumbnail_path)

        try:
            await loop.run_in_executor(None, _delete_files)
        except Exception as e:
            logger.error("Error during image cleanup: %s", str(e))
            msg = f"Failed to delete files for {file_path}: {e}"
            raise StorageError(msg) from e

    async def exists(self, file_path: str) -> bool:
        """Check if a file exists on disk asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, lambda: Path(file_path).exists())
