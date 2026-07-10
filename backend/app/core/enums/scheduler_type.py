"""Scheduler / sampler type enumeration.

Defines all supported noise schedulers for diffusion inference.
"""

from __future__ import annotations

from enum import StrEnum


class SchedulerType(StrEnum):
    """Supported noise schedulers (samplers) for diffusion models.

    Each scheduler implements a different denoising strategy with
    trade-offs between speed, quality, and determinism.
    """

    # ─── Euler family ───
    EULER = "euler"
    EULER_A = "euler_a"  # Euler Ancestral (stochastic)

    # ─── DPM++ family ───
    DPM_PP_2M = "dpm_pp_2m"
    DPM_PP_2M_KARRAS = "dpm_pp_2m_karras"
    DPM_PP_2M_SDE = "dpm_pp_2m_sde"
    DPM_PP_2M_SDE_KARRAS = "dpm_pp_2m_sde_karras"
    DPM_PP_SDE = "dpm_pp_sde"
    DPM_PP_SDE_KARRAS = "dpm_pp_sde_karras"

    # ─── Classic ───
    DDIM = "ddim"
    DDPM = "ddpm"
    PNDM = "pndm"
    LMS = "lms"
    HEUN = "heun"

    # ─── UniPC ───
    UNIPC = "unipc"

    # ─── LCM (few-step) ───
    LCM = "lcm"

    @classmethod
    def get_default(cls) -> SchedulerType:
        """Get the recommended default scheduler."""
        return cls.EULER_A

    @classmethod
    def get_fast_schedulers(cls) -> list[SchedulerType]:
        """Get schedulers optimized for speed (fewer steps needed)."""
        return [cls.EULER_A, cls.DPM_PP_2M_KARRAS, cls.LCM, cls.UNIPC]

    @classmethod
    def get_quality_schedulers(cls) -> list[SchedulerType]:
        """Get schedulers optimized for quality (more steps recommended)."""
        return [cls.DPM_PP_2M_SDE_KARRAS, cls.DPM_PP_SDE_KARRAS, cls.DDIM]
