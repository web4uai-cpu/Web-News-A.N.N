"""
Pydantic schemas for Article Service request/response models.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class ArticleInput(BaseModel):
    source_url: str
    raw_text: str = Field(..., min_length=50)
    source_name: str = "unknown"
    category: str = "general"


class ScriptResponse(BaseModel):
    id: str
    headline: str
    english_script: str
    hindi_script: str = ""
    translations: dict[str, str] = {}
    category: str
    source_url: str = ""
    word_count_en: int = 0
    word_count_hi: int = 0
    estimated_duration_seconds: int = 0
    created_at: datetime

    class Config:
        from_attributes = True


class ScriptCreate(BaseModel):
    headline: str
    english_script: str
    hindi_script: str = ""
    translations: dict[str, str] = {}
    category: str = "general"
    source_url: str = ""
