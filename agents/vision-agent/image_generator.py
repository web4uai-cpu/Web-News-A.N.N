"""
A.N.N. Image Generation Agent
Generates article thumbnails, infographics, and social media cards using AI image models.
"""

import os
import time
from pathlib import Path
from uuid import uuid4

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("image_generator")

OUTPUT_DIR = Path(__file__).parent.parent.parent / "backend" / "output" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

THUMBNAIL_PROMPT_TEMPLATE = """Create a photorealistic, editorial-quality news thumbnail image.
Topic: {headline}
Category: {category}
Style: Clean, modern, high contrast. No text overlays. No watermarks.
Mood: Professional broadcast news aesthetic.
Composition: 16:9 landscape, rule-of-thirds, shallow depth of field."""

INFOGRAPHIC_PROMPT_TEMPLATE = """Create a clean data visualization infographic.
Topic: {headline}
Key data points: {data_points}
Style: Minimal, dark theme (#0a0a1a background), cyan/indigo accent colors.
Layout: Vertical, mobile-friendly. Use icons and charts, not walls of text."""

SOCIAL_CARD_SIZES = {
    "twitter": {"width": 1200, "height": 675},
    "facebook": {"width": 1200, "height": 630},
    "instagram_square": {"width": 1080, "height": 1080},
    "instagram_story": {"width": 1080, "height": 1920},
    "youtube_thumbnail": {"width": 1280, "height": 720},
}


class ImageGenerationResult:
    def __init__(self, script_id: str = "", image_type: str = ""):
        self.id = str(uuid4())
        self.script_id = script_id
        self.image_type = image_type
        self.image_url = ""
        self.local_path = ""
        self.prompt_used = ""
        self.model = ""
        self.width = 0
        self.height = 0
        self.generation_time_s = 0.0
        self.status = "pending"
        self.error = ""


class ImageGeneratorAgent:
    def __init__(self):
        self.settings = get_settings()

    async def generate_thumbnail(
        self, script_id: str, headline: str, category: str
    ) -> ImageGenerationResult:
        result = ImageGenerationResult(script_id=script_id, image_type="thumbnail")
        prompt = THUMBNAIL_PROMPT_TEMPLATE.format(headline=headline, category=category)
        return await self._generate(result, prompt, width=1792, height=1024)

    async def generate_infographic(
        self, script_id: str, headline: str, data_points: list[str]
    ) -> ImageGenerationResult:
        result = ImageGenerationResult(script_id=script_id, image_type="infographic")
        prompt = INFOGRAPHIC_PROMPT_TEMPLATE.format(
            headline=headline, data_points="\n".join(f"- {d}" for d in data_points)
        )
        return await self._generate(result, prompt, width=1024, height=1792)

    async def generate_social_cards(
        self, script_id: str, headline: str, category: str, platforms: list[str] | None = None
    ) -> dict[str, ImageGenerationResult]:
        targets = platforms or ["twitter", "facebook", "instagram_square"]
        results = {}
        for platform in targets:
            size = SOCIAL_CARD_SIZES.get(platform)
            if not size:
                continue
            result = ImageGenerationResult(script_id=script_id, image_type=f"social_{platform}")
            prompt = f"News social media card for {platform}. Headline: {headline}. Category: {category}. Clean, bold, professional. No text."
            results[platform] = await self._generate(
                result, prompt, width=size["width"], height=size["height"]
            )
        return results

    async def _generate(
        self, result: ImageGenerationResult, prompt: str, width: int = 1024, height: int = 1024
    ) -> ImageGenerationResult:
        t0 = time.time()
        result.prompt_used = prompt
        result.width = width
        result.height = height

        if not self.settings.llm_api_key:
            result.status = "skipped"
            result.error = "no_api_key"
            return result

        await rate_limiter.acquire("llm")

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/images/generations",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": "gpt-image-1",
                        "prompt": prompt,
                        "n": 1,
                        "size": f"{width}x{height}",
                        "quality": "high",
                    },
                )
                response.raise_for_status()
                data = response.json()

            image_url = data["data"][0].get("url", "")
            result.image_url = image_url
            result.model = "gpt-image-1"

            if image_url:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    img_resp = await client.get(image_url)
                    img_resp.raise_for_status()
                    filename = f"{result.script_id}_{result.image_type}_{result.id[:8]}.png"
                    filepath = OUTPUT_DIR / filename
                    with open(filepath, "wb") as f:
                        f.write(img_resp.content)
                    result.local_path = str(filepath)

            result.status = "completed"
            result.generation_time_s = round(time.time() - t0, 2)
            log.info(
                "image_generated",
                script_id=result.script_id,
                image_type=result.image_type,
                time_s=result.generation_time_s,
            )

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            result.generation_time_s = round(time.time() - t0, 2)
            log.error("image_generation_failed", error=str(e), script_id=result.script_id)

        return result
