"""
ElevenLabs TTS — text-to-speech audio generation.
"""

import os
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from config import get_settings
import rate_limiter

ELEVENLABS_URL = "https://api.elevenlabs.io/v1"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=60))
async def generate_audio(script_id: str, text: str, language: str = "en") -> dict:
    settings = get_settings()

    if not settings.elevenlabs_api_key:
        return {"script_id": script_id, "language": language, "status": "skipped", "audio_url": ""}

    await rate_limiter.acquire("elevenlabs")

    voice_id = settings.elevenlabs_voice_en if language == "en" else settings.elevenlabs_voice_hi
    if not voice_id:
        return {"script_id": script_id, "language": language, "status": "no_voice_configured", "audio_url": ""}

    clean_text = text.replace("[PAUSE]", "... ")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{ELEVENLABS_URL}/text-to-speech/{voice_id}",
            headers={"xi-api-key": settings.elevenlabs_api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            json={
                "text": clean_text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {"stability": 0.6, "similarity_boost": 0.85, "style": 0.4, "use_speaker_boost": True},
            },
        )
        response.raise_for_status()

        audio_dir = os.path.join(settings.output_dir, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        filename = f"{script_id}_{language}.mp3"
        filepath = os.path.join(audio_dir, filename)
        with open(filepath, "wb") as f:
            f.write(response.content)

    return {
        "script_id": script_id,
        "language": language,
        "audio_url": filepath,
        "duration_seconds": 0.0,
        "status": "completed",
    }
