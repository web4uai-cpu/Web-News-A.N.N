from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class OrchestratorSettings(BaseSettings):
    llm_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o")
    llm_base_url: str = Field(default="https://api.openai.com/v1")
    llm_rpm: int = Field(default=10)

    redis_url: str = Field(default="redis://localhost:6379/0")

    article_service_url: str = Field(default="http://localhost:8002")
    video_service_url: str = Field(default="http://localhost:8003")
    search_service_url: str = Field(default="http://localhost:8005")
    notification_service_url: str = Field(default="http://localhost:8006")

    max_critic_retries: int = Field(default=1)
    relevance_threshold: float = Field(default=3.0)
    dedup_similarity_threshold: float = Field(default=0.85)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> OrchestratorSettings:
    return OrchestratorSettings()
