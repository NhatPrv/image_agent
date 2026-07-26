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
from PIL import Image as PILImage

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
        """Step 1: General Super-Resolution scaling using Lanczos4 interpolation with bilateral noise reduction."""
        # High quality scaling using OpenCV INTER_LANCZOS4
        upscaled = cv2.resize(img_np, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        # Apply gentle bilateral filter to remove pixelation noise while preserving sharp boundaries
        denoised = cv2.bilateralFilter(upscaled, d=5, sigmaColor=20, sigmaSpace=20)
        return denoised

    def _step2_detail_and_face_restoration(self, img_np: np.ndarray) -> np.ndarray:
        """Step 2: Detail & Feature Enhancement via LAB Unsharp Masking."""
        # Convert to LAB color space to apply sharpening on Lightness channel only (prevents color distortion)
        lab = cv2.cvtColor(img_np, cv2.COLOR_RGB2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        # Unsharp mask on L channel
        gaussian = cv2.GaussianBlur(l_channel, (0, 0), 3.0)
        unsharp = cv2.addWeighted(l_channel, 1.35, gaussian, -0.35, 0)

        merged_lab = cv2.merge((unsharp, a_channel, b_channel))
        enhanced_rgb = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)
        return enhanced_rgb

    def _step3_color_and_clarity_adjustment(self, img_np: np.ndarray) -> np.ndarray:
        """Step 3: CLAHE Contrast Adjustment & Final Clarity Polish."""
        # Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) on Y channel in YCrCb
        ycrcb = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)
        y, cr, cb = cv2.split(ycrcb)

        clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
        cl = clahe.apply(y)

        final_ycrcb = cv2.merge((cl, cr, cb))
        final_rgb = cv2.cvtColor(final_ycrcb, cv2.COLOR_YCrCb2RGB)
        return final_rgb

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
