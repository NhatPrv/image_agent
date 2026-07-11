"""WebSocket Endpoint.

Provides real-time generation progress updates and hardware monitor statistics
broadcasting.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.di.container import get_event_bus, get_system_service

if TYPE_CHECKING:
    from app.core.interfaces.event_bus import IEventBus
    from app.services.system_service import SystemService

router = APIRouter(tags=["WebSocket"])
logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts JSON packets."""

    def __init__(self) -> None:
        """Initialize connection list and broadcast lock."""
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept connection and register websocket client."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.debug("WebSocket client connected. Total clients: %d", len(self.active_connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        """Unregister websocket client."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.debug(
            "WebSocket client disconnected. Total clients: %d", len(self.active_connections)
        )

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast a JSON message packet to all connected clients."""
        async with self._lock:
            if not self.active_connections:
                return

            # Capture a copy to safely iterate while sending
            clients = list(self.active_connections)

        for websocket in clients:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.debug(
                    "Failed broadcasting to websocket client: %s. Cleaning client.", str(e)
                )
                await self.disconnect(websocket)


# Global connection manager instance
manager = ConnectionManager()
_stats_monitor_task: asyncio.Task | None = None
_bridge_registered = False


# ─── Event Bus WebSocket Bridge ───


async def websocket_event_bridge(event_type: str, data: dict[str, Any]) -> None:
    """Forward internal events from EventBus directly to WebSocket clients."""
    packet = {
        "event": event_type,
        "timestamp": data.get("completed_at")
        or data.get("started_at")
        or data.get("loaded_at")
        or "",
        "data": data,
    }
    await manager.broadcast(packet)


def register_event_bridge(event_bus: IEventBus) -> None:
    """Register the event bridge handler for all generation and model events."""
    global _bridge_registered
    if _bridge_registered:
        return

    event_types = [
        "generation.queued",
        "generation.started",
        "generation.progress",
        "generation.completed",
        "generation.failed",
        "model.loading",
        "model.loaded",
        "model.error",
        "model.unloaded",
        "download.started",
        "download.progress",
        "download.completed",
        "download.failed",
    ]

    for et in event_types:
        # Wrap handler to bind the current event type parameter
        def make_handler(evt_type=et):
            async def handler(data: dict[str, Any]):
                await websocket_event_bridge(evt_type, data)

            return handler

        event_bus.subscribe(et, make_handler())

    _bridge_registered = True
    logger.info("WebSocket Event Bus bridge registered successfully.")


# ─── Periodic System Stats Broadcast Loop ───


async def start_system_monitor_loop(system_service: SystemService) -> None:
    """Background task loop broadcasting system/VRAM stats to clients."""
    global _stats_monitor_task
    if _stats_monitor_task is not None:
        return

    async def _loop():
        while True:
            try:
                if manager.active_connections:
                    stats = system_service.get_system_stats()
                    packet = {
                        "event": "system.monitor",
                        "data": stats,
                    }
                    await manager.broadcast(packet)
                # Broadcast stats every 3 seconds
                await asyncio.sleep(3.0)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in system monitoring WebSocket loop: %s", str(e))
                await asyncio.sleep(5.0)

    _stats_monitor_task = asyncio.create_task(_loop())
    logger.info("System stats monitor loop started.")


def stop_system_monitor_loop() -> None:
    """Request shutdown of the background stats monitor loop."""
    global _stats_monitor_task
    if _stats_monitor_task is not None:
        _stats_monitor_task.cancel()
        _stats_monitor_task = None
        logger.info("System stats monitor loop stopped.")


# ─── WebSocket Endpoint Route ───


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    event_bus: IEventBus = Depends(get_event_bus),
    system_service: SystemService = Depends(get_system_service),
) -> None:
    """FastAPI WebSocket endpoint for real-time progress and hardware telemetry."""
    # Ensure bridge handlers and monitoring loop are initialized
    register_event_bridge(event_bus)
    await start_system_monitor_loop(system_service)

    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection alive, listen for client messages (ignored for now)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.debug("WebSocket error: %s", str(e))
        await manager.disconnect(websocket)
