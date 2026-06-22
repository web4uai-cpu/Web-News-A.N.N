"""
HeyGen avatar video generation.
"""

import asyncio
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from config import get_settings
import rate_limiter

HEYGEN_URL = "https://api.heygen.com/v2"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=5, max=120))
async def generate_video(script_id: str, script_text: str, language: str = "en", audio_url: str | None = None) -> dict:
    settings = get_settings()

    if not settings.heygen_api_key:
        return {"script_id": script_id, "language": language, "status": "skipped", "video_url": "", "heygen_video_id": ""}

    await rate_limiter.acquire("heygen")

    avatar_id = settings.heygen_avatar_en if language == "en" else settings.heygen_avatar_hi
    if not avatar_id:
        return {"script_id": script_id, "language": language, "status": "no_avatar_configured", "video_url": "", "heygen_video_id": ""}

    clean_text = script_text.replace("[PAUSE]", "... ")

    video_input = {
        "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
        "voice": {"type": "text", "input_text": clean_text},
    }
    if audio_url:
        video_input["voice"] = {"type": "audio", "audio_url": audio_url}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{HEYGEN_URL}/video/generate",
            headers={"X-Api-Key": settings.heygen_api_key, "Content-Type": "application/json"},
            json={"video_inputs": [video_input], "dimension": {"width": 1080, "height": 1920}, "aspect_ratio": "9:16", "test": False},
        )
        response.raise_for_status()
        data = response.json()

    heygen_id = data.get("data", {}).get("video_id", "")
    return {"script_id": script_id, "language": language, "status": "processing", "video_url": "", "heygen_video_id": heygen_id}


async def check_status(video_id: str) -> dict:
    settings = get_settings()
    if not settings.heygen_api_key:
        return {"status": "skipped"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            f"{HEYGEN_URL}/video_status.get",
            headers={"X-Api-Key": settings.heygen_api_key},
            params={"video_id": video_id},
        )
        response.raise_for_status()
        data = response.json()

    return {
        "status": data.get("data", {}).get("status", "unknown"),
        "video_url": data.get("data", {}).get("video_url", ""),
        "video_id": video_id,
    }


async def wait_for_completion(video_id: str, poll_interval: int = 15, timeout: int = 600) -> dict:
    elapsed = 0
    while elapsed < timeout:
        result = await check_status(video_id)
        if result["status"] in ("completed", "failed", "error"):
            return result
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval
    return {"status": "timeout", "video_id": video_id}
