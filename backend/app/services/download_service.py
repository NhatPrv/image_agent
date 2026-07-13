"""Model Download Service.

Handles local background downloading of checkpoints, LoRAs, and VAES.
Streams chunks to avoid RAM bloating, calculates speed/ETA, and broadcasts
progress via the Event Bus.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import aiohttp

from app.infrastructure.events.event_types import (
    DownloadCompletedPayload,
    DownloadFailedPayload,
    DownloadProgressPayload,
    DownloadStartedPayload,
)

if TYPE_CHECKING:
    from app.config.settings import Settings
    from app.core.interfaces.event_bus import IEventBus
    from app.services.model_service import ModelService

logger = logging.getLogger(__name__)


class DownloadTask:
    """Represents a model download task running in the background."""

    def __init__(
        self,
        task_id: str,
        url: str,
        filename: str,
        component_type: str,
        file_path: Path,
    ) -> None:
        self.task_id = task_id
        self.url = url
        self.filename = filename
        self.component_type = component_type
        self.file_path = file_path
        self.bytes_downloaded = 0
        self.bytes_total = 0
        self.speed_mb = 0.0
        self.eta_seconds = 0.0
        self.status = "pending"  # pending, downloading, completed, failed, cancelled
        self.error_message: str | None = None
        self.start_time: float = 0.0

    def to_dict(self) -> dict:
        """Serialize task to dictionary representation."""
        return {
            "task_id": self.task_id,
            "url": self.url,
            "filename": self.filename,
            "component_type": self.component_type,
            "bytes_downloaded": self.bytes_downloaded,
            "bytes_total": self.bytes_total,
            "speed_mb": round(self.speed_mb, 2),
            "eta_seconds": round(self.eta_seconds, 1),
            "status": self.status,
            "error_message": self.error_message,
            "file_path": str(self.file_path),
        }


class DownloadService:
    """Orchestrates multi-threaded safe downloading of model assets."""

    def __init__(
        self,
        settings: Settings,
        event_bus: IEventBus,
        model_service: ModelService,
    ) -> None:
        """Initialize Download Service."""
        self._settings = settings
        self._event_bus = event_bus
        self._model_service = model_service
        self._tasks: dict[str, DownloadTask] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}

    def get_all_tasks(self) -> list[dict]:
        """Fetch status dictionary for all registered tasks."""
        return [task.to_dict() for task in self._tasks.values()]

    def get_task(self, task_id: str) -> dict | None:
        """Get status for a single task."""
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None

    async def start_download(self, url: str, filename: str, component_type: str) -> dict:
        """Spawns an asynchronous download task in the background."""
        task_id = str(uuid.uuid4())

        # Decide output subfolder based on component type
        models_base_dir = Path(self._settings.paths.models_dir)

        # Ensure directory structure exists
        models_base_dir.mkdir(parents=True, exist_ok=True)
        file_path = models_base_dir / filename

        task = DownloadTask(task_id, url, filename, component_type, file_path)
        self._tasks[task_id] = task

        # Spin off background execution task
        bg_task = asyncio.create_task(self._download_loop(task))
        self._running_tasks[task_id] = bg_task

        return task.to_dict()

    async def cancel_download(self, task_id: str) -> bool:
        """Cancel a running download task and delete partial temp download files."""
        bg_task = self._running_tasks.get(task_id)
        task = self._tasks.get(task_id)

        if not task:
            return False

        logger.info("Requesting cancellation for download task: %s", task_id)
        task.status = "cancelled"

        if bg_task and not bg_task.done():
            bg_task.cancel()

        # Clear running task registration
        if task_id in self._running_tasks:
            del self._running_tasks[task_id]

        # Async clean up partial download files
        temp_path = Path(f"{task.file_path}.download")
        try:
            if temp_path.exists():
                temp_path.unlink()
                logger.info("Cleaned up partial download file: %s", temp_path)
        except Exception as e:
            logger.warning("Could not clean up temp file %s: %s", temp_path, str(e))

        return True

    async def _download_loop(self, task: DownloadTask) -> None:
        """Core download routine with auto-retry and HTTP Range resume support.

        Handles HuggingFace CDN connection drops gracefully by resuming
        from the last received byte using 'Range: bytes=X-' headers.
        Retries up to MAX_RETRIES times with exponential backoff.
        """
        MAX_RETRIES = 10
        CHUNK_SIZE = 512 * 1024  # 512 KB

        task.status = "downloading"
        task.start_time = time.time()
        temp_path = Path(f"{task.file_path}.download")

        # Emit download started payload to event bus
        started_payload = DownloadStartedPayload(
            task_id=task.task_id,
            url=task.url,
            filename=task.filename,
            started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        await self._event_bus.publish("download.started", started_payload)

        attempt = 0
        last_emit_time = time.time()

        try:
            while attempt < MAX_RETRIES:
                attempt += 1

                # Resume: check how many bytes already written to temp file
                resume_from = temp_path.stat().st_size if temp_path.exists() else 0
                task.bytes_downloaded = resume_from

                headers = {}
                if resume_from > 0:
                    headers["Range"] = f"bytes={resume_from}-"
                    logger.info(
                        "Resuming download from byte %d (attempt %d/%d): %s",
                        resume_from,
                        attempt,
                        MAX_RETRIES,
                        task.filename,
                    )

                # sock_read=120: timeout if NO bytes received for 120s (stalled)
                # total=None: never timeout active streaming transfers
                timeout = aiohttp.ClientTimeout(total=None, connect=30, sock_read=120)

                try:
                    async with (
                        aiohttp.ClientSession(timeout=timeout) as session,
                        session.get(task.url, headers=headers) as response,
                    ):
                        # 200 = full content, 206 = partial content (resume OK)
                        if response.status not in (200, 206):
                            msg = f"HTTP Server returned status code {response.status}"
                            raise ValueError(msg)

                        # Update total only on first response (or 200 retry)
                        if task.bytes_total == 0 or response.status == 200:
                            task.bytes_total = int(response.headers.get("content-length", 0))
                            if response.status == 206:
                                # For Range responses, Content-Length is the remaining bytes
                                # Reconstruct total from Content-Range header if available
                                content_range = response.headers.get("content-range", "")
                                if "/" in content_range:
                                    try:
                                        task.bytes_total = int(content_range.split("/")[-1])
                                    except ValueError:
                                        pass

                        # Open in append mode when resuming, write mode for fresh start
                        file_mode = "ab" if resume_from > 0 else "wb"
                        async with aiofiles.open(temp_path, file_mode) as f:
                            async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                                # Check cancellation between chunks
                                if task.status == "cancelled":
                                    return

                                await f.write(chunk)
                                task.bytes_downloaded += len(chunk)

                                # Calculate speed & ETA metrics
                                current_time = time.time()
                                elapsed = current_time - task.start_time
                                if elapsed > 0:
                                    task.speed_mb = task.bytes_downloaded / (1024 * 1024 * elapsed)
                                    if task.bytes_total > task.bytes_downloaded:
                                        remaining = task.bytes_total - task.bytes_downloaded
                                        task.eta_seconds = remaining / (
                                            task.bytes_downloaded / elapsed
                                        )
                                    else:
                                        task.eta_seconds = 0.0

                                # Emit progress (throttled to once per second)
                                if current_time - last_emit_time >= 1.0:
                                    last_emit_time = current_time
                                    progress_percent = (
                                        (task.bytes_downloaded / task.bytes_total) * 100
                                        if task.bytes_total > 0
                                        else 0.0
                                    )
                                    progress_payload = DownloadProgressPayload(
                                        task_id=task.task_id,
                                        bytes_downloaded=task.bytes_downloaded,
                                        bytes_total=task.bytes_total,
                                        progress_percent=progress_percent,
                                        speed_mb=task.speed_mb,
                                        eta_seconds=task.eta_seconds,
                                    )
                                    await self._event_bus.publish(
                                        "download.progress", progress_payload
                                    )

                        # Stream completed successfully — break retry loop
                        break

                except (
                    TimeoutError,
                    aiohttp.ClientError,
                    aiohttp.ServerDisconnectedError,
                    aiohttp.ClientPayloadError,
                    ConnectionResetError,
                ) as conn_err:
                    if task.status == "cancelled":
                        return
                    if attempt >= MAX_RETRIES:
                        raise
                    # Exponential backoff: 2s, 4s, 8s ... capped at 60s
                    wait_secs = min(2**attempt, 60)
                    logger.warning(
                        "Connection error on attempt %d/%d for %s: %s. Retrying in %ds...",
                        attempt,
                        MAX_RETRIES,
                        task.filename,
                        conn_err,
                        wait_secs,
                    )
                    await asyncio.sleep(wait_secs)
                    continue

            # Check if cancelled before finishing
            if task.status == "cancelled":
                return

            # Rename temp file to final target destination
            if temp_path.exists():
                if task.file_path.exists():
                    task.file_path.unlink()
                temp_path.rename(task.file_path)

            task.status = "completed"
            logger.info("Successfully completed downloading: %s", task.filename)

            # Auto trigger scanner to register the model in database instantly!
            await self._model_service.scan_and_register_models()

            # Emit completed payload
            completed_payload = DownloadCompletedPayload(
                task_id=task.task_id,
                file_path=str(task.file_path),
                completed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            await self._event_bus.publish("download.completed", completed_payload)

        except asyncio.CancelledError:
            task.status = "cancelled"
            logger.info("Download task %s was cancelled by user.", task.task_id)

        except Exception as e:
            task.status = "failed"
            task.error_message = str(e)
            logger.error("Download failed for URL %s: %s", task.url, str(e))

            # Clean up temp file on permanent failure (not on cancel)
            if temp_path.exists():
                with contextlib.suppress(Exception):
                    temp_path.unlink()

            failed_payload = DownloadFailedPayload(
                task_id=task.task_id,
                error_message=str(e),
                failed_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            )
            await self._event_bus.publish("download.failed", failed_payload)

        finally:
            if task.task_id in self._running_tasks:
                del self._running_tasks[task.task_id]
