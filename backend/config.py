"""
A.N.N. Configuration Module
Centralizes all environment variables and application settings.
Uses pydantic-settings for validation and type safety.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from .env file."""

    # ── App ──────────────────────────────────────────────
    app_name: str = "A.N.N. - AI News Network"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # ── LLM Brain ───────────────────────────────────────
    llm_api_key: str = Field(default="", description="OpenAI / Gemini API Key")
    llm_model: str = Field(default="gpt-4o", description="LLM model identifier")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for LLM API (OpenAI-compatible)",
    )

    # ── News Ingestion ──────────────────────────────────
    news_api_key: str = Field(default="", description="NewsAPI.org API Key")
    alpha_vantage_key: str = Field(default="", description="Alpha Vantage API Key")

    # ── Media Production ────────────────────────────────
    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API Key")
    elevenlabs_voice_en: str = Field(default="", description="English voice clone ID")
    elevenlabs_voice_hi: str = Field(default="", description="Hindi voice clone ID")

    heygen_api_key: str = Field(default="", description="HeyGen API Key")
    heygen_avatar_en: str = Field(default="", description="English avatar ID")
    heygen_avatar_hi: str = Field(default="", description="Hindi avatar ID")

    # ── Rate Limits (requests per minute) ───────────────
    llm_rpm: int = Field(default=10, description="LLM API requests per minute")
    news_api_rpm: int = Field(default=30, description="NewsAPI requests per minute")
    elevenlabs_rpm: int = Field(default=10, description="ElevenLabs requests per minute")
    heygen_rpm: int = Field(default=5, description="HeyGen requests per minute")

    # ── Social Media ────────────────────────────────────
    twitter_bearer_token: str = Field(default="", description="Twitter/X Bearer Token")
    facebook_page_token: str = Field(default="", description="Facebook Page Access Token")
    facebook_page_id: str = Field(default="", description="Facebook Page ID")
    instagram_access_token: str = Field(default="", description="Instagram Graph API Token")
    instagram_account_id: str = Field(default="", description="Instagram Business Account ID")
    social_auto_post: bool = Field(default=False, description="Auto-post to social on script creation")

    # ── Public URL ──────────────────────────────────────
    public_url: str = Field(default="http://localhost:8000", description="Public-facing URL")

    # ── Enterprise Cloud DB ─────────────────────────────
    supabase_url: str = Field(default="", description="Supabase API URL")
    supabase_key: str = Field(default="", description="Supabase API Key")
    database_url: str = Field(default="", description="Direct Postgres Connection URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
