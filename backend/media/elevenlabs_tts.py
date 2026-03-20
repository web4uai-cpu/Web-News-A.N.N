"""
A.N.N. ElevenLabs TTS Service
Generates high-fidelity text-to-speech audio for broadcast scripts.
"""

import httpx
import os
from tenacity import retry, stop_after_attempt, wait_exponential

from models.schemas import AudioResult, Language
from utils.rate_limiter import rate_limiter
from utils.logger import get_logger
from config import get_settings

log = get_logger("elevenlabs_tts")


class ElevenLabsTTS:
    """
    Integrates with ElevenLabs API for broadcast-quality TTS.
    Supports dual-language output with cloned voices.
    """

    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.elevenlabs_api_key
        self.voice_map = {
            Language.ENGLISH: self.settings.elevenlabs_voice_en,
            Language.HINDI: self.settings.elevenlabs_voice_hi,
        }
        # Create output directory
        self.output_dir = os.path.join(os.path.dirname(__file__), "..", "output", "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=3, max=60),
    )
    async def generate_audio(
        self,
        script_id: str,
        text: str,
        language: Language = Language.ENGLISH,
    ) -> AudioResult:
        """
        Generate TTS audio from a broadcast script.
        
        Args:
            script_id: Unique identifier for the script.
            text: The script text to synthesize.
            language: Target language for voice selection.
            
        Returns:
            AudioResult with file path and metadata.
        """
        if not self.api_key:
            log.warning("elevenlabs_key_missing")
            return AudioResult(
                script_id=script_id,
                language=language,
                status="skipped",
                audio_url="",
            )

        await rate_limiter.acquire("elevenlabs")

        voice_id = self.voice_map.get(language, self.settings.elevenlabs_voice_en)
        if not voice_id:
            log.warning("voice_id_missing", language=language.value)
            return AudioResult(
                script_id=script_id,
                language=language,
                status="no_voice_configured",
            )

        # Clean script for TTS (remove [PAUSE] markers, replace with SSML-like breaks)
        clean_text = text.replace("[PAUSE]", "... ")

        log.info(
            "generating_audio",
            script_id=script_id,
            language=language.value,
            text_length=len(clean_text),
        )

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{self.BASE_URL}/text-to-speech/{voice_id}",
                headers={
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
                json={
                    "text": clean_text,
                    "model_id": "eleven_multilingual_v2",
                    "voice_settings": {
                        "stability": 0.6,
                        "similarity_boost": 0.85,
                        "style": 0.4,
                        "use_speaker_boost": True,
                    },
                },
            )

            response.raise_for_status()

            # Save audio file
            filename = f"{script_id}_{language.value}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, "wb") as f:
                f.write(response.content)

            log.info(
                "audio_generated",
                script_id=script_id,
                language=language.value,
                file_size_kb=round(len(response.content) / 1024, 1),
                filepath=filepath,
            )

            return AudioResult(
                script_id=script_id,
                language=language,
                audio_url=filepath,
                status="completed",
            )

    async def list_voices(self) -> list[dict]:
        """List available voices (useful for setup/debugging)."""
        if not self.api_key:
            return []

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{self.BASE_URL}/voices",
                headers={"xi-api-key": self.api_key},
            )
            response.raise_for_status()
            data = response.json()

        return [
            {
                "voice_id": v["voice_id"],
                "name": v["name"],
                "category": v.get("category", "unknown"),
            }
            for v in data.get("voices", [])
        ]
