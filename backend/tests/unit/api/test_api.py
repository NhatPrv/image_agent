"""Unit tests for the REST API endpoints.

Mocks the services layer and database repositories to test router integration.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.entities.model_info import ModelInfo
from app.core.enums.model_type import ModelArchitecture, ModelComponentType, ModelFileFormat
from app.di.container import (
    get_model_service,
    get_settings_dep,
    get_system_service,
    get_download_service,
    get_generation_service,
)
from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient bound to the FastAPI instance."""
    return TestClient(app)


# ─── System/Health Check Test ───


def test_health_check_endpoint(client: TestClient):
    """Verify that system health endpoint returns status ok."""
    response = client.get("/api/v1/system/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Image Agent Backend is running."}


# ─── Models Endpoints Tests ───


def test_list_models_endpoint(client: TestClient):
    """Verify listing models endpoint calls ModelService and parses correctly."""
    mock_model = ModelInfo(
        id="model_123",
        name="SD1.5 Dreamshaper",
        filename="dreamshaper.safetensors",
        path="C:/models/dreamshaper.safetensors",
        component_type=ModelComponentType.CHECKPOINT,
        architecture=ModelArchitecture.SD_1_5,
        file_format=ModelFileFormat.SAFETENSORS,
        size_bytes=2147483648,
        hash_sha256="abc123hash",
        metadata={},
    )

    mock_service = MagicMock()
    mock_service.get_all_models = AsyncMock(return_value=[mock_model])

    # Override ModelService dependency
    app.dependency_overrides[get_model_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/models")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "model_123"
        assert data[0]["name"] == "SD1.5 Dreamshaper"
        assert data[0]["architecture"] == "sd_1_5"
    finally:
        # Clean overrides
        app.dependency_overrides.clear()


# ─── Settings Endpoints Tests ───


def test_get_settings_endpoint(client: TestClient):
    """Verify that settings get endpoint returns values mapped from Pydantic config."""
    mock_settings = MagicMock()
    mock_settings.app.name = "Test Image Agent"
    mock_settings.app.version = "1.0.0"
    mock_settings.app.debug = True

    mock_settings.server.host = "127.0.0.1"
    mock_settings.server.port = 8000
    mock_settings.server.cors_origins = ["*"]

    mock_settings.paths.models_dir = "models"
    mock_settings.paths.outputs_dir = "outputs"
    mock_settings.paths.logs_dir = "logs"

    mock_settings.gpu.device = "cuda"
    mock_settings.gpu.dtype = "float16"
    mock_settings.gpu.xformers = True
    mock_settings.gpu.attention_slicing = False
    mock_settings.gpu.vae_slicing = True
    mock_settings.gpu.vae_tiling = False
    mock_settings.gpu.cpu_offload = False
    mock_settings.gpu.sequential_cpu_offload = False
    mock_settings.gpu.torch_compile = False
    mock_settings.gpu.max_vram_usage_mb = 6000.0

    app.dependency_overrides[get_settings_dep] = lambda: mock_settings

    try:
        response = client.get("/api/v1/settings")
        assert response.status_code == 200

        data = response.json()
        assert data["app"]["name"] == "Test Image Agent"
        assert data["gpu"]["device"] == "cuda"
        assert data["gpu"]["xformers"] is True
    finally:
        app.dependency_overrides.clear()


# ─── System Monitor Info Tests ───


def test_system_info_endpoint(client: TestClient):
    """Verify platform stats endpoints returns CPU, RAM and GPU mock properties."""
    mock_stats = {
        "platform": "Windows",
        "platform_version": "11",
        "python_version": "3.11",
        "cpu": {"usage_percent": 12.5, "cores": 8},
        "ram": {"used_mb": 4096, "total_mb": 16384, "usage_percent": 25.0},
        "disk": {"used_gb": 120.0, "total_gb": 512.0, "usage_percent": 23.4},
        "gpu": {
            "cuda_available": True,
            "device_name": "NVIDIA GeForce RTX 4060",
            "vram_used_mb": 2048.0,
            "vram_total_mb": 8192.0,
            "vram_usage_percent": 25.0,
        },
    }

    mock_service = MagicMock()
    mock_service.get_system_stats.return_value = mock_stats

    app.dependency_overrides[get_system_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200

        data = response.json()
        assert data["platform"] == "Windows"
        assert data["cpu"]["cores"] == 8
        assert data["gpu"]["device_name"] == "NVIDIA GeForce RTX 4060"
    finally:
        app.dependency_overrides.clear()


# ─── Download Endpoints Tests ───


def test_create_download_endpoint(client: TestClient):
    """Verify that posting to download route invokes DownloadService.start_download."""
    mock_task = {
        "task_id": "download_task_123",
        "url": "http://example.com/model.safetensors",
        "filename": "model.safetensors",
        "component_type": "checkpoint",
        "status": "pending",
    }
    mock_service = MagicMock()
    mock_service.start_download = AsyncMock(return_value=mock_task)

    app.dependency_overrides[get_download_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/downloads",
            json={
                "url": "http://example.com/model.safetensors",
                "filename": "model.safetensors",
                "component_type": "checkpoint",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["task_id"] == "download_task_123"
        assert data["status"] == "pending"
    finally:
        app.dependency_overrides.clear()


def test_list_downloads_endpoint(client: TestClient):
    """Verify that list downloads route retrieves active downloads from service."""
    mock_tasks = [
        {
            "task_id": "download_task_123",
            "url": "http://example.com/model.safetensors",
            "filename": "model.safetensors",
            "component_type": "checkpoint",
            "status": "downloading",
        }
    ]
    mock_service = MagicMock()
    mock_service.get_all_tasks.return_value = mock_tasks

    app.dependency_overrides[get_download_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/downloads")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["task_id"] == "download_task_123"
    finally:
        app.dependency_overrides.clear()


def test_cancel_download_endpoint(client: TestClient):
    """Verify cancellation route requests cancel on DownloadService."""
    mock_service = MagicMock()
    mock_service.cancel_download = AsyncMock(return_value=True)

    app.dependency_overrides[get_download_service] = lambda: mock_service

    try:
        response = client.post("/api/v1/downloads/download_task_123/cancel")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["task_id"] == "download_task_123"
    finally:
        app.dependency_overrides.clear()


def test_delete_generation_endpoint(client: TestClient):
    """Verify DELETE endpoint calls delete_generation on GenerationService."""
    mock_service = MagicMock()
    mock_service.delete_generation = AsyncMock()

    app.dependency_overrides[get_generation_service] = lambda: mock_service

    try:
        response = client.delete("/api/v1/generations/generation_123")
        assert response.status_code == 204
        mock_service.delete_generation.assert_called_once_with("generation_123")
    finally:
        app.dependency_overrides.clear()
