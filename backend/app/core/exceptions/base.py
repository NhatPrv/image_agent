"""Exception hierarchy for Image Agent.

All custom exceptions inherit from ImageAgentError, providing
structured error handling with error codes and contextual details.

Hierarchy:
    ImageAgentError
    ├── ImageAgentValidationError
    ├── EngineError
    │   ├── ModelLoadError
    │   ├── ModelNotLoadedError
    │   ├── GenerationError
    │   ├── VRAMInsufficientError
    │   └── CUDAError
    ├── StorageError
    │   ├── ImageFileNotFoundError
    │   └── DiskFullError
    ├── ImageAgentDatabaseError
    ├── QueueError
    │   ├── QueueFullError
    │   └── QueueItemNotFoundError
    ├── PluginError
    │   ├── PluginLoadError
    │   └── PluginExecutionError
    └── DownloadError
"""

from __future__ import annotations

from typing import Any


class ImageAgentError(Exception):
    """Base exception for all Image Agent errors.

    Attributes:
        message: Human-readable error description.
        error_code: Machine-readable error code (e.g., "VRAM_INSUFFICIENT").
        details: Additional context as key-value pairs.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        *,
        error_code: str = "UNKNOWN_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to a structured dictionary for API responses."""
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "details": self.details,
            }
        }


# ═══════════════════════════════════════════
# Validation Errors
# ═══════════════════════════════════════════


class ImageAgentValidationError(ImageAgentError):
    """Input validation failed."""

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        field: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={"field": field, **(details or {})},
        )


# ═══════════════════════════════════════════
# Engine Errors
# ═══════════════════════════════════════════


class EngineError(ImageAgentError):
    """Base class for AI engine errors."""

    def __init__(
        self,
        message: str = "AI engine error",
        *,
        error_code: str = "ENGINE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class ModelLoadError(EngineError):
    """Failed to load a model file."""

    def __init__(
        self,
        message: str = "Failed to load model",
        *,
        model_path: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="MODEL_LOAD_ERROR",
            details={"model_path": model_path, **(details or {})},
        )


class ModelNotLoadedError(EngineError):
    """No model is currently loaded."""

    def __init__(self, message: str = "No model is currently loaded") -> None:
        super().__init__(message, error_code="MODEL_NOT_LOADED")


class GenerationError(EngineError):
    """Image generation failed."""

    def __init__(
        self,
        message: str = "Image generation failed",
        *,
        generation_id: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="GENERATION_ERROR",
            details={"generation_id": generation_id, **(details or {})},
        )


class GenerationNotFoundError(GenerationError):
    """Generation request record not found."""

    def __init__(
        self,
        message: str = "Generation request not found",
        *,
        generation_id: str = "",
    ) -> None:
        super().__init__(
            message,
            error_code="GENERATION_NOT_FOUND",
            generation_id=generation_id,
        )


class VRAMInsufficientError(EngineError):
    """Not enough GPU VRAM for the requested operation."""

    def __init__(
        self,
        message: str = "Insufficient VRAM",
        *,
        required_mb: int = 0,
        available_mb: int = 0,
    ) -> None:
        super().__init__(
            message,
            error_code="VRAM_INSUFFICIENT",
            details={
                "required_mb": required_mb,
                "available_mb": available_mb,
                "suggestion": "Try using a smaller model, reducing image size, "
                "or enabling CPU offloading in settings.",
            },
        )


class CUDAError(EngineError):
    """CUDA-related error (driver, runtime, etc.)."""

    def __init__(
        self,
        message: str = "CUDA error occurred",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code="CUDA_ERROR", details=details)


# ═══════════════════════════════════════════
# Storage Errors
# ═══════════════════════════════════════════


class StorageError(ImageAgentError):
    """Base class for file storage errors."""

    def __init__(
        self,
        message: str = "Storage error",
        *,
        error_code: str = "STORAGE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class ImageFileNotFoundError(StorageError):
    """Requested file does not exist."""

    def __init__(self, message: str = "File not found", *, path: str = "") -> None:
        super().__init__(
            message,
            error_code="FILE_NOT_FOUND",
            details={"path": path},
        )


class DiskFullError(StorageError):
    """Not enough disk space for the operation."""

    def __init__(self, message: str = "Insufficient disk space") -> None:
        super().__init__(message, error_code="DISK_FULL")


# ═══════════════════════════════════════════
# Database Errors
# ═══════════════════════════════════════════


class ImageAgentDatabaseError(ImageAgentError):
    """Database operation failed."""

    def __init__(
        self,
        message: str = "Database error",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code="DATABASE_ERROR", details=details)


# ═══════════════════════════════════════════
# Queue Errors
# ═══════════════════════════════════════════


class QueueError(ImageAgentError):
    """Base class for queue errors."""

    def __init__(
        self,
        message: str = "Queue error",
        *,
        error_code: str = "QUEUE_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, error_code=error_code, details=details)


class QueueFullError(QueueError):
    """Queue has reached maximum capacity."""

    def __init__(self, message: str = "Queue is full", *, max_size: int = 0) -> None:
        super().__init__(
            message,
            error_code="QUEUE_FULL",
            details={"max_size": max_size},
        )


class QueueItemNotFoundError(QueueError):
    """Queue item with given ID not found."""

    def __init__(self, message: str = "Queue item not found", *, item_id: str = "") -> None:
        super().__init__(
            message,
            error_code="QUEUE_ITEM_NOT_FOUND",
            details={"item_id": item_id},
        )


# ═══════════════════════════════════════════
# Plugin Errors
# ═══════════════════════════════════════════


class PluginError(ImageAgentError):
    """Base class for plugin errors."""

    def __init__(
        self,
        message: str = "Plugin error",
        *,
        error_code: str = "PLUGIN_ERROR",
        plugin_name: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code=error_code,
            details={"plugin_name": plugin_name, **(details or {})},
        )


class PluginLoadError(PluginError):
    """Failed to load a plugin."""

    def __init__(self, message: str = "Failed to load plugin", *, plugin_name: str = "") -> None:
        super().__init__(message, error_code="PLUGIN_LOAD_ERROR", plugin_name=plugin_name)


class PluginExecutionError(PluginError):
    """Plugin encountered an error during execution."""

    def __init__(self, message: str = "Plugin execution failed", *, plugin_name: str = "") -> None:
        super().__init__(message, error_code="PLUGIN_EXECUTION_ERROR", plugin_name=plugin_name)


# ═══════════════════════════════════════════
# Download Errors
# ═══════════════════════════════════════════


class DownloadError(ImageAgentError):
    """Download operation failed."""

    def __init__(
        self,
        message: str = "Download failed",
        *,
        url: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message,
            error_code="DOWNLOAD_ERROR",
            details={"url": url, **(details or {})},
        )
