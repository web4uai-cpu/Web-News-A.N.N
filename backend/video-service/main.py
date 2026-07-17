"""
A.N.N. Video Service
Handles TTS audio generation (ElevenLabs) and avatar video generation (HeyGen).
"""

import time
from contextlib import asynccontextmanager

import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from config import get_settings
import rate_limiter
import tts
import avatar

settings = get_settings()
START_TIME = time.time()


class AudioRequest(BaseModel):
    script_id: str
    text: str
    language: str = "en"


class VideoRequest(BaseModel):
    script_id: str
    script_text: str
    language: str = "en"
    audio_url: str | None = None


class VideoStatusRequest(BaseModel):
    video_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    rate_limiter.register("elevenlabs", settings.elevenlabs_rpm)
    rate_limiter.register("heygen", settings.heygen_rpm)
    yield


app = FastAPI(
    title="A.N.N. Video Service",
    description="TTS audio and AI avatar video generation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"service": "video-service", "status": "healthy", "uptime_seconds": round(time.time() - START_TIME, 1)}


@app.post("/api/v1/media/generate_audio")
async def generate_audio(req: AudioRequest):
    try:
        result = await tts.generate_audio(req.script_id, req.text, req.language)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/media/generate_video")
async def generate_video(req: VideoRequest):
    try:
        result = await avatar.generate_video(req.script_id, req.script_text, req.language, req.audio_url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/media/video_status/{video_id}")
async def video_status(video_id: str):
    try:
        result = await avatar.check_status(video_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
