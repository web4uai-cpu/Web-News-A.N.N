"""
A.N.N. Pydantic Schemas
All data models used across the application.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ── Enums ────────────────────────────────────────────────

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


class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    SPANISH = "es"
    FRENCH = "fr"
    MANDARIN = "zh"
    ARABIC = "ar"


# ── Input Models ─────────────────────────────────────────

class ArticleInput(BaseModel):
    """Raw article input for processing."""
    source_url: str = Field(..., description="Original source URL")
    raw_text: str = Field(..., min_length=50, description="Full article text")
    source_name: str = Field(default="unknown", description="Name of the news source")
    category: NewsCategory = Field(default=NewsCategory.GENERAL)


class IngestRequest(BaseModel):
    """Request to ingest news from a specific source."""
    category: NewsCategory = Field(default=NewsCategory.GENERAL)
    query: Optional[str] = Field(default=None, description="Search query for targeted ingestion")
    max_articles: int = Field(default=5, ge=1, le=20)


class FinancialIngestRequest(BaseModel):
    """Request to ingest financial/stock news."""
    symbols: list[str] = Field(default=["AAPL", "GOOGL", "MSFT"], description="Stock ticker symbols")
    max_articles: int = Field(default=5, ge=1, le=20)


class AudioGenerationRequest(BaseModel):
    """Request to generate TTS audio for a script."""
    script_id: str
    language: Language = Language.ENGLISH


class VideoGenerationRequest(BaseModel):
    """Request to generate avatar video."""
    script_id: str
    language: Language = Language.ENGLISH


# ── Output Models ────────────────────────────────────────

class ExtractedFacts(BaseModel):
    """Output from the Fact Extractor Agent."""
    source_url: str
    facts: str
    fact_count: int = 0
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class BroadcastScript(BaseModel):
    """A complete broadcast script with translations."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    headline: str
    english_script: str
    hindi_script: str = ""
    translations: dict[str, str] = Field(default_factory=dict)
    category: NewsCategory
    source_url: str = ""
    word_count_en: int = 0
    word_count_hi: int = 0
    estimated_duration_seconds: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def model_post_init(self, __context) -> None:
        """Calculate derived fields after initialization."""
        if self.english_script and not self.word_count_en:
            self.word_count_en = len(self.english_script.split())
        if self.hindi_script and not self.word_count_hi:
            self.word_count_hi = len(self.hindi_script.split())
        if self.word_count_en and not self.estimated_duration_seconds:
            # Average anchor reads ~150 words per minute
            self.estimated_duration_seconds = int((self.word_count_en / 150) * 60)


class AudioResult(BaseModel):
    """Result from TTS audio generation."""
    script_id: str
    language: Language
    audio_url: str = ""
    duration_seconds: float = 0.0
    status: str = "pending"


class VideoResult(BaseModel):
    """Result from avatar video generation."""
    script_id: str
    language: Language
    video_url: str = ""
    status: str = "pending"
    heygen_video_id: str = ""


# ── Pipeline Models ──────────────────────────────────────

class PipelineJob(BaseModel):
    """Tracks a full pipeline run."""
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
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    active_jobs: int = 0
