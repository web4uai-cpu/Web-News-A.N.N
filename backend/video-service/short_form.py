"""
A.N.N. Short-Form Video Generator
Creates vertical (9:16) short-form videos for Reels, Shorts, and TikTok.
"""

import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from utils.logger import get_logger
from utils.rate_limiter import rate_limiter
from config import get_settings

log = get_logger("short_form_video")

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "video" / "shorts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ShortFormConfig:
    max_duration_seconds: int = 60
    width: int = 1080
    height: int = 1920
    fps: int = 30
    font_size: int = 48
    font_color: str = "white"
    caption_bg_color: str = "black@0.6"
    caption_position: str = "center"


@dataclass
class ShortFormResult:
    script_id: str
    video_path: str = ""
    duration_seconds: float = 0.0
    platform_variants: dict = field(default_factory=dict)
    status: str = "pending"
    error: str = ""


class ShortFormVideoGenerator:
    def __init__(self, config: ShortFormConfig | None = None):
        self.config = config or ShortFormConfig()
        self.settings = get_settings()

    def truncate_script(self, script: str, max_seconds: int = 30) -> str:
        words_per_second = 2.5
        max_words = int(max_seconds * words_per_second)
        words = script.replace("[PAUSE]", "").split()
        if len(words) <= max_words:
            return script
        truncated = " ".join(words[:max_words])
        if not truncated.endswith((".", "!", "?")):
            truncated += "."
        return truncated

    def generate_captions_srt(self, script: str, output_path: str) -> str:
        srt_path = output_path.replace(".mp4", ".srt")
        words = script.replace("[PAUSE]", " ").split()
        words_per_chunk = 5
        seconds_per_chunk = 2.0
        lines = []

        for i in range(0, len(words), words_per_chunk):
            chunk = " ".join(words[i : i + words_per_chunk])
            idx = i // words_per_chunk + 1
            start = i // words_per_chunk * seconds_per_chunk
            end = start + seconds_per_chunk

            start_ts = f"{int(start // 3600):02}:{int((start % 3600) // 60):02}:{int(start % 60):02},{int((start % 1) * 1000):03}"
            end_ts = f"{int(end // 3600):02}:{int((end % 3600) // 60):02}:{int(end % 60):02},{int((end % 1) * 1000):03}"

            lines.append(f"{idx}\n{start_ts} --> {end_ts}\n{chunk}\n")

        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return srt_path

    async def generate(
        self,
        script_id: str,
        audio_path: str,
        script_text: str,
        background_image: str | None = None,
    ) -> ShortFormResult:
        try:
            truncated = self.truncate_script(script_text, self.config.max_duration_seconds)
            output_path = str(OUTPUT_DIR / f"{script_id}_short.mp4")
            srt_path = self.generate_captions_srt(truncated, output_path)

            filter_complex = (
                f"[0:a]showwaves=s={self.config.width}x{self.config.height}:mode=cline:colors=cyan[v];"
                f"[v]subtitles={srt_path}:force_style='FontSize={self.config.font_size},"
                f"PrimaryColour=&HFFFFFF,BackColour=&H80000000,BorderStyle=4,"
                f"Alignment=10,MarginV=200'[out]"
            )

            cmd = [
                "ffmpeg", "-y",
                "-i", audio_path,
                "-filter_complex", filter_complex,
                "-map", "[out]", "-map", "0:a",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac", "-b:a", "192k",
                "-r", str(self.config.fps),
                "-t", str(self.config.max_duration_seconds),
                output_path,
            ]

            log.info("generating_short_form", script_id=script_id, output=output_path)
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if proc.returncode != 0:
                log.error("ffmpeg_failed", stderr=proc.stderr[:500])
                return ShortFormResult(
                    script_id=script_id, status="failed", error=proc.stderr[:500]
                )

            duration = await self._get_duration(output_path)

            variants = await self._create_platform_variants(script_id, output_path)

            return ShortFormResult(
                script_id=script_id,
                video_path=output_path,
                duration_seconds=duration,
                platform_variants=variants,
                status="completed",
            )
        except Exception as e:
            log.error("short_form_failed", script_id=script_id, error=str(e))
            return ShortFormResult(script_id=script_id, status="failed", error=str(e))

    async def _get_duration(self, video_path: str) -> float:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return float(proc.stdout.strip()) if proc.returncode == 0 else 0.0

    async def _create_platform_variants(
        self, script_id: str, source_path: str
    ) -> dict[str, str]:
        variants = {}
        platforms = {
            "youtube_shorts": {"max_duration": 60},
            "instagram_reels": {"max_duration": 90},
            "tiktok": {"max_duration": 60},
        }

        for platform, config in platforms.items():
            variant_path = str(OUTPUT_DIR / f"{script_id}_{platform}.mp4")
            cmd = [
                "ffmpeg", "-y",
                "-i", source_path,
                "-t", str(config["max_duration"]),
                "-c", "copy",
                variant_path,
            ]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if proc.returncode == 0:
                variants[platform] = variant_path

        return variants
