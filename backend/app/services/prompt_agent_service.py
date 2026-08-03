"""Prompt Agent Service.

Natural language processing facade that parses human conversational input (Vietnamese/English)
into optimized positive and negative prompts for Stable Diffusion and SDXL models.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Common Vietnamese-to-English translation mapping for image editing & generation
VIETNAMESE_DICTIONARY: dict[str, str] = {
    "hiệu ứng đóng băng": "frosted ice crystallization effect, frozen ice texture",
    "đóng băng": "frosted ice texture, frozen ice effect",
    "băng giá": "frosty ice texture",
    "quả bóng nước": "crystal water sphere droplet",
    "quả bóng": "crystal sphere",
    "giọt nước": "crystal water droplet",
    "quả cầu": "glass sphere",
    "quả cầu pha lê": "transparent crystal glass sphere",
    "lá cây": "green leaf",
    "mắt": "eyes",
    "đôi mắt": "eyes",
    "mắt đỏ": "glowing red eyes",
    "mắt xanh": "vibrant blue eyes",
    "mèo": "kitten",
    "màu đỏ": "red",
    "màu xanh": "blue",
    "màu vàng": "golden yellow",
    "màu trắng": "pure white",
    "sửa": "modify",
    "đổi": "change to",
    "thành": "into",
    "biến thành": "transformed into",
    "trong suốt": "crystal clear transparent",
    "rêu": "green moss background",
    "chụp vĩ mô": "macro photography",
    "sắc nét": "sharp focus highly detailed",
}

# Mode-specific prompt booster configurations
MODE_BOOSTERS: dict[str, dict[str, str]] = {
    "inpaint": {
        "positive": "high quality, isolated target object details, sharp focus",
        "negative": "background change, color bleed, surrounding alterations, blurry, low quality, noise, out of focus, deformed",
    },
    "upscale": {
        "positive": "masterpiece, photorealistic, 8k resolution, sharp focus, micro details, noise-free",
        "negative": "blurry, low quality, noise, pixelated, compression artifacts, distorted",
    },
    "img2img": {
        "positive": "masterpiece, photorealistic, high quality, sharp focus, aesthetic texture",
        "negative": "blurry, low quality, noise, out of focus, deformed, ugly",
    },
    "txt2img": {
        "positive": "masterpiece, photorealistic, 8k resolution, highly detailed, sharp focus, professional photography",
        "negative": "blurry, low quality, noise, out of focus, deformed, ugly, bad anatomy, distorted",
    },
}


@dataclass
class ParsedPromptResult:
    """Structure representing parsed and enhanced prompt output."""
    raw_input: str
    positive_prompt: str
    negative_prompt: str
    detected_language: str
    extracted_keywords: list[str]


class PromptAgentService:
    """Agent service that parses natural conversational prompts into AI generation prompts."""

    def parse_prompt(self, user_input: str, mode: str = "txt2img") -> ParsedPromptResult:
        """Parse natural language user input into structured positive and negative prompts.

        Args:
            user_input: Natural conversational text (Vietnamese or English).
            mode: Generation mode ('txt2img', 'img2img', 'inpaint', 'upscale').

        Returns:
            ParsedPromptResult containing positive and negative prompts.
        """
        booster = MODE_BOOSTERS.get(mode.lower(), MODE_BOOSTERS["txt2img"])

        if not user_input or (hasattr(user_input, "strip") and not user_input.strip()):
            return ParsedPromptResult(
                raw_input="",
                positive_prompt=booster["positive"],
                negative_prompt=booster["negative"],
                detected_language="en",
                extracted_keywords=[],
            )

        text = user_input.strip()
        is_vietnamese = bool(re.search(r"[àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", text, re.IGNORECASE))
        detected_lang = "vi" if is_vietnamese else "en"

        translated_parts: list[str] = []

        if is_vietnamese:
            lower_text = text.lower()
            # Replace dictionary phrases
            for vi_phrase, en_phrase in VIETNAMESE_DICTIONARY.items():
                if vi_phrase in lower_text:
                    translated_parts.append(en_phrase)
                    lower_text = lower_text.replace(vi_phrase, "")

            # Cleanup remaining words
            cleaned_remaining = re.sub(r"[^\w\s]", "", lower_text).strip()
            if cleaned_remaining:
                translated_parts.append(cleaned_remaining)
        else:
            translated_parts.append(text)

        extracted = [p for p in translated_parts if p]
        body_prompt = ", ".join(extracted) if extracted else text

        positive_prompt = f"{body_prompt}, {booster['positive']}"
        negative_prompt = booster["negative"]

        logger.info(
            "Parsed natural prompt | Mode: '%s' | Input: '%s' | Positive: '%s'",
            mode,
            user_input,
            positive_prompt,
        )

        return ParsedPromptResult(
            raw_input=user_input,
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            detected_language=detected_lang,
            extracted_keywords=extracted,
        )
