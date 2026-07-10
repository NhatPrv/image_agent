"""Default constants and limits for Image Agent.

Centralized constants used across the application. Never hardcode
values in services or routes — reference these constants instead.
"""

from __future__ import annotations

# ═══════════════════════════════════════════
# Generation Limits
# ═══════════════════════════════════════════

MIN_IMAGE_SIZE = 64
MAX_IMAGE_SIZE = 2048
IMAGE_SIZE_STEP = 8  # Must be multiple of 8

MIN_STEPS = 1
MAX_STEPS = 150

MIN_CFG_SCALE = 1.0
MAX_CFG_SCALE = 30.0

MIN_CLIP_SKIP = 1
MAX_CLIP_SKIP = 12

MAX_PROMPT_LENGTH = 2000
MAX_NEGATIVE_PROMPT_LENGTH = 2000

MAX_BATCH_SIZE = 16
MAX_SEED = 2**32 - 1

# ═══════════════════════════════════════════
# Queue Limits
# ═══════════════════════════════════════════

MAX_QUEUE_SIZE = 100
DEFAULT_QUEUE_PRIORITY = "normal"

# ═══════════════════════════════════════════
# File & Storage
# ═══════════════════════════════════════════

SUPPORTED_IMAGE_FORMATS = {"png", "jpg", "jpeg", "webp"}
DEFAULT_OUTPUT_FORMAT = "png"
THUMBNAIL_SIZE = (256, 256)
THUMBNAIL_FORMAT = "webp"
THUMBNAIL_QUALITY = 85

SUPPORTED_MODEL_EXTENSIONS = {".safetensors", ".ckpt", ".bin", ".pt", ".pth"}
SUPPORTED_LORA_EXTENSIONS = {".safetensors", ".pt", ".bin"}

# ═══════════════════════════════════════════
# VRAM Management (RTX 4060 8GB Target)
# ═══════════════════════════════════════════

DEFAULT_MAX_VRAM_MB = 7680  # 7.5GB — leave 512MB for system
VRAM_WARNING_THRESHOLD = 0.85  # Warn at 85% usage
VRAM_CRITICAL_THRESHOLD = 0.95  # Critical at 95% usage

# Estimated VRAM usage per model architecture (MB)
ESTIMATED_VRAM_USAGE = {
    "sd_1_5": 2000,
    "sd_2_1": 2500,
    "sdxl": 6500,
    "sdxl_turbo": 6500,
    "flux": 12000,
    "sd3": 8000,
}

# ═══════════════════════════════════════════
# API
# ═══════════════════════════════════════════

API_V1_PREFIX = "/api/v1"
WS_PREFIX = "/ws"

# ═══════════════════════════════════════════
# Pagination
# ═══════════════════════════════════════════

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ═══════════════════════════════════════════
# Performance
# ═══════════════════════════════════════════

MONITOR_INTERVAL_SECONDS = 1.0  # System monitor update interval
PROGRESS_CALLBACK_INTERVAL = 1  # Send progress every N steps
