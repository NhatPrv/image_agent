"""Generation type enumeration.

Defines all supported image generation modes.
"""

from __future__ import annotations

from enum import StrEnum


class GenerationType(StrEnum):
    """Types of image generation supported by Image Agent."""

    TEXT_TO_IMAGE = "txt2img"
    IMAGE_TO_IMAGE = "img2img"
    INPAINT = "inpaint"
    OUTPAINT = "outpaint"
    CONTROLNET = "controlnet"
    UPSCALE = "upscale"
    FACE_RESTORE = "face_restore"
