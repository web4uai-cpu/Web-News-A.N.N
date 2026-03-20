"""
A.N.N. HeyGen Video Generation Service
Generates AI avatar videos from audio scripts for broadcast.
"""

import httpx
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

from models.schemas import VideoResult, Language
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("heygen_video")


class HeyGenVideoGenerator:
    """
    Integrates with HeyGen API for AI avatar video generation.
    Creates realistic talking-head videos for news broadcasts.
    
    Note: In production, this will be replaced by a local 
    Wav2Lip/SadTalker cluster for cost efficiency.
    """

    BASE_URL = "https://api.heygen.com/v2"

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.heygen_api_key
        self.avatar_map = {
            Language.ENGLISH: self.settings.heygen_avatar_en,
            Language.HINDI: self.settings.heygen_avatar_hi,
        }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=120),
    )
    async def generate_video(
        self,
        script_id: str,
        script_text: str,
        language: Language = Language.ENGLISH,
        audio_url: str | None = None,
    ) -> VideoResult:
        """
        Generate an AI avatar video for a broadcast script.
        
        Args:
            script_id: Unique script identifier.
            script_text: The broadcast script text.
            language: Language for avatar and voice selection.
            audio_url: Optional pre-generated audio file URL.
            
        Returns:
            VideoResult with HeyGen video ID and status.
        """
        if not self.api_key:
            log.warning("heygen_key_missing")
            return VideoResult(
                script_id=script_id,
                language=language,
                status="skipped",
            )

        await rate_limiter.acquire("heygen")

        avatar_id = self.avatar_map.get(language, self.settings.heygen_avatar_en)
        if not avatar_id:
            log.warning("avatar_id_missing", language=language.value)
            return VideoResult(
                script_id=script_id,
                language=language,
                status="no_avatar_configured",
            )

        # Clean script for video generation
        clean_text = script_text.replace("[PAUSE]", "... ")

        log.info(
            "generating_video",
            script_id=script_id,
            language=language.value,
            text_length=len(clean_text),
        )

        # Create video generation request
        video_input = {
            "character": {
                "type": "avatar",
                "avatar_id": avatar_id,
                "avatar_style": "normal",
            },
            "voice": {
                "type": "text",
                "input_text": clean_text,
            },
        }

        # If we have pre-generated audio from ElevenLabs, use it
        if audio_url:
            video_input["voice"] = {
                "type": "audio",
                "audio_url": audio_url,
            }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/video/generate",
                headers={
                    "X-Api-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "video_inputs": [video_input],
                    "dimension": {"width": 1080, "height": 1920},
                    "aspect_ratio": "9:16",
                    "test": False,
                },
            )

            response.raise_for_status()
            data = response.json()

        heygen_video_id = data.get("data", {}).get("video_id", "")

        log.info(
            "video_generation_started",
            script_id=script_id,
            heygen_video_id=heygen_video_id,
        )

        return VideoResult(
            script_id=script_id,
            language=language,
            status="processing",
            heygen_video_id=heygen_video_id,
        )

    async def check_video_status(self, video_id: str) -> dict:
        """
        Check the status of a video generation job.
        
        Returns:
            Dict with status and download URL when ready.
        """
        if not self.api_key:
            return {"status": "skipped"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/video_status.get",
                headers={"X-Api-Key": self.api_key},
                params={"video_id": video_id},
            )
            response.raise_for_status()
            data = response.json()

        status = data.get("data", {}).get("status", "unknown")
        video_url = data.get("data", {}).get("video_url", "")

        return {
            "status": status,
            "video_url": video_url,
            "video_id": video_id,
        }

    async def wait_for_video(
        self,
        video_id: str,
        poll_interval: int = 15,
        timeout: int = 600,
    ) -> dict:
        """
        Poll for video completion with timeout.
        
        Args:
            video_id: HeyGen video ID.
            poll_interval: Seconds between status checks.
            timeout: Maximum wait time in seconds.
            
        Returns:
            Final status dict with video URL.
        """
        elapsed = 0
        while elapsed < timeout:
            result = await self.check_video_status(video_id)
            status = result.get("status", "")

            if status == "completed":
                log.info("video_completed", video_id=video_id, video_url=result.get("video_url"))
                return result
            elif status in ("failed", "error"):
                log.error("video_failed", video_id=video_id)
                return result

            log.debug("video_polling", video_id=video_id, status=status, elapsed=elapsed)
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        log.warning("video_timeout", video_id=video_id, timeout=timeout)
        return {"status": "timeout", "video_id": video_id}
