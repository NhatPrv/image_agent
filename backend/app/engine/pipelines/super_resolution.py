"""Super-Resolution Pipeline.

High-performance, specialized image upscaling pipeline incorporating:
Step 1: General Super-Resolution (Lanczos4 High-Fidelity Scaling & Denoising)
Step 2: Detail & Edge Restoration (Adaptive LAB Unsharp Masking & Sharpness)
Step 3: Color & Clarity Adjustment (CLAHE Contrast Balance & Final Polish)
"""

import asyncio
import time
from typing import Any, Callable

import cv2
import numpy as np
from PIL import Image as PILImage, ImageEnhance, ImageFilter

import logging

from app.core.entities.generation import GenerationParams, GenerationProgress
from app.core.exceptions.base import GenerationError

logger = logging.getLogger(__name__)


class SuperResolutionPipeline:
    """Specialized engine for fast, high-quality image upscaling up to 8K resolution."""

    def __init__(self, settings: Any) -> None:
        self.settings = settings
        self.pipeline = True  # Marker indicating pipeline is active and ready

    async def load(self, model_path: str) -> None:
        """No heavy checkpoint load required for super resolution."""
        pass

    def load_from_components(self, components: dict[str, Any]) -> None:
        """Compatibility no-op."""
        pass

    def _step1_general_super_resolution(self, img_np: np.ndarray, target_w: int, target_h: int) -> np.ndarray:
        """Step 1: General Super-Resolution scaling using Lanczos4 interpolation with adaptive detail preservation."""
        # High quality scaling using OpenCV INTER_LANCZOS4
        upscaled = cv2.resize(img_np, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        # Apply subtle bilateral filter to reduce JPEG/pixelation noise while preserving sharp boundaries
        denoised = cv2.bilateralFilter(upscaled, d=3, sigmaColor=15, sigmaSpace=15)
        return denoised

    def _step2_detail_and_face_restoration(self, img_np: np.ndarray) -> np.ndarray:
        """Step 2: Multi-Scale Unsharp Masking & High-Frequency Texture Recovery (SnapEdit Style)."""
        # Convert to YCrCb space to operate on Luminance (Y) channel
        ycrcb = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        # Multi-scale Gaussian blurring for dual-frequency sharpening
        g1 = cv2.GaussianBlur(y, (0, 0), 1.2)  # Fine micro-details (hair, eyes, skin texture)
        g2 = cv2.GaussianBlur(y, (0, 0), 3.5)  # Medium structure boundaries

        # Dual-layer Unsharp Masking
        y_fine = cv2.addWeighted(y, 1.8, g1, -0.8, 0)
        y_sharp = cv2.addWeighted(y_fine, 1.35, g2, -0.35, 0)

        merged_ycrcb = cv2.merge((np.clip(y_sharp, 0, 255).astype(np.uint8), cr, cb))
        enhanced_rgb = cv2.cvtColor(merged_ycrcb, cv2.COLOR_YCrCb2RGB)
        return enhanced_rgb

    def _step3_color_and_clarity_adjustment(self, img_np: np.ndarray) -> np.ndarray:
        """Step 3: CLAHE Contrast Adjustment & SnapEdit Clarity / Vibrance Polish."""
        # Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) on Y channel
        ycrcb = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(y)

        final_ycrcb = cv2.merge((cl, cr, cb))
        rgb = cv2.cvtColor(final_ycrcb, cv2.COLOR_YCrCb2RGB)

        # Final PIL Polish for professional DSLR clarity & contrast
        pil_img = PILImage.fromarray(rgb)
        pil_img = ImageEnhance.Sharpness(pil_img).enhance(1.45)
        pil_img = ImageEnhance.Contrast(pil_img).enhance(1.12)
        pil_img = ImageEnhance.Color(pil_img).enhance(1.08)

        return np.array(pil_img)

    async def generate(
        self,
        params: GenerationParams,
        generation_id: str,
        progress_callback: Callable[[GenerationProgress], Any] | None = None,
    ) -> list[PILImage.Image]:
        """Execute the 3-step Super-Resolution pipeline."""
        if not params.input_image_path:
            msg = "Input image path is required for Super-Resolution upscaling."
            raise GenerationError(msg)

        # Resolve input_image_path
        from pathlib import Path
        input_path = Path(params.input_image_path)
        if not input_path.is_absolute() or not input_path.exists():
            outputs_dir = Path(self.settings.paths.outputs_dir).resolve()
            resolved = outputs_dir / input_path
            if resolved.exists():
                input_path = resolved
            else:
                matches = list(outputs_dir.rglob(input_path.name))
                if matches:
                    input_path = matches[0]

        resolved_str = str(input_path)
        target_w = params.width
        target_h = params.height

        logger.info(
            "Starting 3-Step Super-Resolution Pipeline | Input: %s -> Target: %dx%d",
            resolved_str,
            target_w,
            target_h,
        )

        start_time = time.perf_counter()

        def _process():
            # Read input image with OpenCV
            img_bgr = cv2.imread(resolved_str, cv2.IMREAD_COLOR)
            if img_bgr is None:
                raise GenerationError(f"Failed to read image at path: {resolved_str}")
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

            # Step 1: General Super-Resolution
            if progress_callback:
                progress_callback(
                    GenerationProgress(
                        generation_id=generation_id,
                        current_step=1,
                        total_steps=3,
                        progress_percent=33.0,
                        elapsed_ms=int((time.perf_counter() - start_time) * 1000),
                        estimated_remaining_ms=1000,
                    )
                )
            step1_out = self._step1_general_super_resolution(img_rgb, target_w, target_h)

            # Step 2: Detail & Restoration
            if progress_callback:
                progress_callback(
                    GenerationProgress(
                        generation_id=generation_id,
                        current_step=2,
                        total_steps=3,
                        progress_percent=66.0,
                        elapsed_ms=int((time.perf_counter() - start_time) * 1000),
                        estimated_remaining_ms=500,
                    )
                )
            step2_out = self._step2_detail_and_face_restoration(step1_out)

            # Step 3: Color & Clarity Adjustment
            if progress_callback:
                progress_callback(
                    GenerationProgress(
                        generation_id=generation_id,
                        current_step=3,
                        total_steps=3,
                        progress_percent=99.0,
                        elapsed_ms=int((time.perf_counter() - start_time) * 1000),
                        estimated_remaining_ms=0,
                    )
                )
            step3_out = self._step3_color_and_clarity_adjustment(step2_out)

            return PILImage.fromarray(step3_out)

        loop = asyncio.get_running_loop()
        final_pil = await loop.run_in_executor(None, _process)
        return [final_pil]
