"""
A.N.N. Video Understanding Agent
Analyzes video content using multi-modal LLMs: extracts key frames, transcribes,
identifies events, and generates summaries from video sources.
"""

import subprocess
import tempfile
import base64
import time
from pathlib import Path
from uuid import uuid4

import httpx

from config import get_settings
from utils.logger import get_logger
from utils.rate_limiter import rate_limiter

log = get_logger("video_understanding")


class VideoAnalysisResult:
    def __init__(self, video_id: str = ""):
        self.id = str(uuid4())
        self.video_id = video_id
        self.transcript = ""
        self.summary = ""
        self.key_events: list[dict] = []
        self.entities: list[dict] = []
        self.sentiment = ""
        self.topics: list[str] = []
        self.frame_descriptions: list[dict] = []
        self.duration_seconds = 0.0
        self.analysis_time_s = 0.0
        self.status = "pending"
        self.error = ""


class VideoUnderstandingAgent:
    def __init__(self):
        self.settings = get_settings()

    async def extract_keyframes(
        self, video_path: str, interval_seconds: int = 10, max_frames: int = 20
    ) -> list[str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_pattern = str(Path(tmpdir) / "frame_%04d.jpg")
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vf", f"fps=1/{interval_seconds},scale=768:-1",
                "-frames:v", str(max_frames),
                "-q:v", "2",
                output_pattern,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if proc.returncode != 0:
                log.error("keyframe_extraction_failed", stderr=proc.stderr[:300])
                return []

            frames = sorted(Path(tmpdir).glob("frame_*.jpg"))
            encoded = []
            for frame in frames:
                with open(frame, "rb") as f:
                    encoded.append(base64.b64encode(f.read()).decode("utf-8"))
            return encoded

    async def transcribe_audio(self, video_path: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            audio_path = tmp.name

        try:
            cmd = [
                "ffmpeg", "-i", video_path,
                "-vn", "-acodec", "libmp3lame", "-q:a", "4",
                "-y", audio_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode != 0:
                return ""

            await rate_limiter.acquire("llm")

            with open(audio_path, "rb") as f:
                audio_data = f.read()

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/audio/transcriptions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
                    data={"model": "whisper-1", "language": "en"},
                )
                response.raise_for_status()
                return response.json().get("text", "")

        except Exception as e:
            log.error("transcription_failed", error=str(e))
            return ""
        finally:
            Path(audio_path).unlink(missing_ok=True)

    async def analyze_frames(self, frames_b64: list[str], context: str = "") -> list[dict]:
        if not frames_b64:
            return []

        await rate_limiter.acquire("llm")

        content_parts = [
            {"type": "text", "text": (
                "Analyze these video keyframes from a news broadcast. For each frame, describe:\n"
                "1. What is shown (scene, people, graphics)\n"
                "2. Any text/chyrons visible\n"
                "3. Emotional tone\n"
                f"\nContext: {context}\n"
                "Return a JSON array of {\"frame\": int, \"description\": str, \"text_visible\": str, \"tone\": str}."
            )}
        ]

        for i, frame in enumerate(frames_b64[:10]):
            content_parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{frame}", "detail": "low"},
            })

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.settings.llm_base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                    json={
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": content_parts}],
                        "temperature": 0.1,
                        "max_tokens": 2000,
                    },
                )
                response.raise_for_status()
                return [{"raw": response.json()["choices"][0]["message"]["content"]}]
        except Exception as e:
            log.error("frame_analysis_failed", error=str(e))
            return []

    async def analyze_video(self, video_path: str, context: str = "") -> VideoAnalysisResult:
        t0 = time.time()
        result = VideoAnalysisResult()
        result.status = "analyzing"

        try:
            probe_cmd = [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ]
            probe = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=15)
            result.duration_seconds = float(probe.stdout.strip()) if probe.returncode == 0 else 0.0

            interval = max(5, int(result.duration_seconds / 15))
            frames = await self.extract_keyframes(video_path, interval_seconds=interval)

            transcript = await self.transcribe_audio(video_path)
            result.transcript = transcript

            frame_descriptions = await self.analyze_frames(frames, context=context)
            result.frame_descriptions = frame_descriptions

            if transcript:
                summary = await self._generate_summary(transcript, frame_descriptions, context)
                result.summary = summary.get("summary", "")
                result.key_events = summary.get("key_events", [])
                result.entities = summary.get("entities", [])
                result.sentiment = summary.get("sentiment", "neutral")
                result.topics = summary.get("topics", [])

            result.status = "completed"

        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            log.error("video_analysis_failed", error=str(e))

        result.analysis_time_s = round(time.time() - t0, 2)
        log.info("video_analyzed", duration=result.duration_seconds, time_s=result.analysis_time_s)
        return result

    async def _generate_summary(
        self, transcript: str, frame_descriptions: list[dict], context: str
    ) -> dict:
        await rate_limiter.acquire("llm")

        frame_text = "\n".join(
            f"Frame {i+1}: {fd.get('raw', fd.get('description', ''))}"
            for i, fd in enumerate(frame_descriptions[:10])
        )

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.settings.llm_base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
                json={
                    "model": self.settings.llm_model,
                    "messages": [
                        {"role": "system", "content": (
                            "Analyze this video content and produce a structured summary. "
                            "Return JSON: {\"summary\": str (200 words), \"key_events\": [{\"timestamp\": str, \"event\": str}], "
                            "\"entities\": [{\"name\": str, \"type\": str}], \"sentiment\": str, \"topics\": [str]}"
                        )},
                        {"role": "user", "content": (
                            f"Context: {context}\n\nTranscript:\n{transcript[:3000]}\n\n"
                            f"Visual descriptions:\n{frame_text}"
                        )},
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1500,
                    "response_format": {"type": "json_object"},
                },
            )
            response.raise_for_status()

        import json
        try:
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except (json.JSONDecodeError, KeyError):
            return {"summary": "", "key_events": [], "entities": [], "sentiment": "neutral", "topics": []}
