"""Agent API Endpoint.

Provides AI agent capabilities such as parsing natural conversational prompts into
structured positive/negative prompts for image generation.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.prompt_agent_service import PromptAgentService

router = APIRouter()
prompt_agent_service = PromptAgentService()


class PromptParseRequest(BaseModel):
    """Request payload for natural language prompt parsing."""
    prompt: str = Field(..., description="Natural language prompt in Vietnamese or English")
    mode: str = Field(default="txt2img", description="Generation mode: txt2img, img2img, inpaint, upscale")


class PromptParseResponse(BaseModel):
    """Response payload with structured positive and negative prompts."""
    raw_input: str
    positive_prompt: str
    negative_prompt: str
    detected_language: str
    extracted_keywords: list[str]


@router.post("/parse-prompt", response_model=PromptParseResponse)
async def parse_prompt(request: PromptParseRequest) -> PromptParseResponse:
    """Parse a natural language prompt into positive and negative prompts."""
    result = prompt_agent_service.parse_prompt(request.prompt, mode=request.mode)
    return PromptParseResponse(
        raw_input=result.raw_input,
        positive_prompt=result.positive_prompt,
        negative_prompt=result.negative_prompt,
        detected_language=result.detected_language,
        extracted_keywords=result.extracted_keywords,
    )
