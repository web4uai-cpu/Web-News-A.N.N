"""
Shared Pydantic models used across multiple microservices.
Canonical definitions — import from here to avoid drift.
"""

from __future__ import annotations
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class NewsCategory(str, Enum):
    GENERAL = "general"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    SCIENCE = "science"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    POLITICS = "politics"
    FINANCE = "finance"
    GEOPOLITICS = "geopolitics"


class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    MANDARIN = "zh"
    ARABIC = "ar"


class PipelineStatus(str, Enum):
    QUEUED = "queued"
    INGESTING = "ingesting"
    EXTRACTING_FACTS = "extracting_facts"
    WRITING_SCRIPT = "writing_script"
    TRANSLATING = "translating"
    GENERATING_AUDIO = "generating_audio"
    GENERATING_VIDEO = "generating_video"
    COMPLETED = "completed"
    FAILED = "failed"


class ArticleInput(BaseModel):
    source_url: str
    raw_text: str = Field(..., min_length=50)
    source_name: str = "unknown"
    category: NewsCategory = NewsCategory.GENERAL


class BroadcastScript(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    headline: str
    english_script: str
    hindi_script: str = ""
    translations: dict[str, str] = Field(default_factory=dict)
    category: NewsCategory = NewsCategory.GENERAL
    source_url: str = ""
    word_count_en: int = 0
    word_count_hi: int = 0
    estimated_duration_seconds: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context) -> None:
        if self.english_script and not self.word_count_en:
            self.word_count_en = len(self.english_script.split())
        if self.hindi_script and not self.word_count_hi:
            self.word_count_hi = len(self.hindi_script.split())
        if self.word_count_en and not self.estimated_duration_seconds:
            self.estimated_duration_seconds = int((self.word_count_en / 150) * 60)


class AudioResult(BaseModel):
    script_id: str
    language: Language
    audio_url: str = ""
    duration_seconds: float = 0.0
    status: str = "pending"


class VideoResult(BaseModel):
    script_id: str
    language: Language
    video_url: str = ""
    status: str = "pending"
    heygen_video_id: str = ""


class PipelineJob(BaseModel):
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: PipelineStatus = PipelineStatus.QUEUED
    scripts: list[BroadcastScript] = []
    audio_results: list[AudioResult] = []
    video_results: list[VideoResult] = []
    errors: list[str] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    progress_pct: int = 0


class HealthResponse(BaseModel):
    service: str
    status: str
    uptime_seconds: float
    checks: dict[str, str] = {}
