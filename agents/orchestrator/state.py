"""
Pipeline state schema — passed between all agent nodes in the DAG.
"""

from __future__ import annotations
from typing import Annotated
from pydantic import BaseModel, Field
from operator import add


class PipelineState(BaseModel):
    """Immutable state object flowing through the LangGraph pipeline."""

    # Input
    raw_text: str = ""
    source_url: str = ""
    source_name: str = "unknown"
    category: str = "general"

    # Discovery
    is_duplicate: bool = False
    relevance_score: float = 0.0

    # Fact Extraction
    facts: str = ""
    fact_count: int = 0

    # Legal
    legal_approved: bool = True
    legal_risks: list[str] = Field(default_factory=list)

    # Script
    english_script: str = ""
    draft_count: int = 0

    # Critic
    critic_approved: bool = False
    critic_feedback: str = ""

    # Headline
    headline: str = ""

    # SEO
    meta_title: str = ""
    meta_description: str = ""
    keywords: list[str] = Field(default_factory=list)
    schema_json: dict = Field(default_factory=dict)

    # Translation
    hindi_script: str = ""
    translations: dict[str, str] = Field(default_factory=dict)

    # Media
    audio_url: str = ""
    video_url: str = ""
    heygen_video_id: str = ""

    # Output
    script_id: str = ""
    word_count_en: int = 0
    estimated_duration_seconds: int = 0

    # Pipeline metadata
    errors: list[str] = Field(default_factory=list)
    agent_timings: dict[str, float] = Field(default_factory=dict)
