"""Scheduler Factory.

Maps domain SchedulerType enums to native Diffusers schedulers.
"""

from __future__ import annotations

import logging
from typing import Any

from diffusers import (
    DDIMScheduler,
    DDPMScheduler,
    DPMSolverMultistepScheduler,
    EulerAncestralDiscreteScheduler,
    EulerDiscreteScheduler,
    HeunDiscreteScheduler,
    LCMScheduler,
    LMSDiscreteScheduler,
    PNDMScheduler,
    UniPCMultistepScheduler,
)

from app.core.enums.scheduler_type import SchedulerType

logger = logging.getLogger(__name__)


class SchedulerFactory:
    """Factory class to create and configure Diffusers schedulers."""

    @classmethod
    def create(cls, scheduler_type: SchedulerType, config: dict[str, Any]) -> Any:
        """Create a scheduler instance from a pipeline configuration.

        Args:
            scheduler_type: The enum type representing the target sampler.
            config: The config dictionary copied from the pipeline (pipeline.scheduler.config).

        Returns:
            The instantiated and configured Diffusers scheduler.
        """
        # Ensure we don't modify the original pipeline config inplace directly
        config = dict(config)

        # ─── Scheduler Mappings ───
        if scheduler_type == SchedulerType.EULER:
            return EulerDiscreteScheduler.from_config(config)

        if scheduler_type == SchedulerType.EULER_A:
            return EulerAncestralDiscreteScheduler.from_config(config)

        if scheduler_type == SchedulerType.DPM_PP_2M:
            config["use_karras_sigmas"] = False
            config["algorithm_type"] = "dpmsolver++"
            return DPMSolverMultistepScheduler.from_config(config)

        if scheduler_type == SchedulerType.DPM_PP_2M_KARRAS:
            config["use_karras_sigmas"] = True
            config["algorithm_type"] = "dpmsolver++"
            return DPMSolverMultistepScheduler.from_config(config)

        if scheduler_type == SchedulerType.DPM_PP_2M_SDE:
            config["use_karras_sigmas"] = False
            config["algorithm_type"] = "sde-dpmsolver++"
            return DPMSolverMultistepScheduler.from_config(config)

        if scheduler_type == SchedulerType.DPM_PP_2M_SDE_KARRAS:
            config["use_karras_sigmas"] = True
            config["algorithm_type"] = "sde-dpmsolver++"
            return DPMSolverMultistepScheduler.from_config(config)

        if scheduler_type == SchedulerType.DDIM:
            return DDIMScheduler.from_config(config)

        if scheduler_type == SchedulerType.DDPM:
            return DDPMScheduler.from_config(config)

        if scheduler_type == SchedulerType.PNDM:
            return PNDMScheduler.from_config(config)

        if scheduler_type == SchedulerType.LMS:
            return LMSDiscreteScheduler.from_config(config)

        if scheduler_type == SchedulerType.HEUN:
            return HeunDiscreteScheduler.from_config(config)

        if scheduler_type == SchedulerType.UNIPC:
            return UniPCMultistepScheduler.from_config(config)

        if scheduler_type == SchedulerType.LCM:
            return LCMScheduler.from_config(config)

        # Fallback to Euler Ancestral if scheduler is not recognized
        logger.warning(
            "Unknown scheduler type '%s'. Falling back to Euler Ancestral.",
            scheduler_type,
        )
        return EulerAncestralDiscreteScheduler.from_config(config)
