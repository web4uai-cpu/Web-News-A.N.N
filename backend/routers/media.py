"""Media generation endpoints (TTS + avatar video) — cost-sensitive, auth-gated."""

from fastapi import APIRouter, Depends, HTTPException

from core import runtime
from core.security import require_pipeline_access
from models.schemas import AudioGenerationRequest, Language, VideoGenerationRequest
from utils.logger import get_logger

router = APIRouter()
log = get_logger("media_router")


@router.post("/api/v1/media/generate_audio", tags=["Media"])
async def generate_audio(request: AudioGenerationRequest, _auth: dict = Depends(require_pipeline_access)):
    """Generate TTS audio for a script."""
    script = runtime.script_store.get(request.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    text = script.english_script if request.language == Language.ENGLISH else script.hindi_script

    try:
        result = await runtime.tts_service.generate_audio(
            script_id=request.script_id,
            text=text,
            language=request.language,
        )
        return result
    except Exception as e:
        log.error("audio_gen_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/v1/media/generate_video", tags=["Media"])
async def generate_video(request: VideoGenerationRequest, _auth: dict = Depends(require_pipeline_access)):
    """Generate AI avatar video for a script."""
    script = runtime.script_store.get(request.script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found.")

    text = script.english_script if request.language == Language.ENGLISH else script.hindi_script

    try:
        result = await runtime.video_service.generate_video(
            script_id=request.script_id,
            script_text=text,
            language=request.language,
        )
        return result
    except Exception as e:
        log.error("video_gen_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
