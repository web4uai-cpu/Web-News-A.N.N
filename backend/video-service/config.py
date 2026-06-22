from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class VideoSettings(BaseSettings):
    app_name: str = "A.N.N. Video Service"
    host: str = "0.0.0.0"
    port: int = 8003
    debug: bool = False
    log_level: str = "INFO"

    elevenlabs_api_key: str = Field(default="", description="ElevenLabs API Key")
    elevenlabs_voice_en: str = Field(default="", description="English voice clone ID")
    elevenlabs_voice_hi: str = Field(default="", description="Hindi voice clone ID")
    elevenlabs_rpm: int = Field(default=10, description="ElevenLabs requests per minute")

    heygen_api_key: str = Field(default="", description="HeyGen API Key")
    heygen_avatar_en: str = Field(default="", description="English avatar ID")
    heygen_avatar_hi: str = Field(default="", description="Hindi avatar ID")
    heygen_rpm: int = Field(default=5, description="HeyGen requests per minute")

    redis_url: str | None = Field(default=None, description="Redis URL for Celery broker")
    output_dir: str = Field(default="./output", description="Media output directory")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> VideoSettings:
    return VideoSettings()
