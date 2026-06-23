from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class ArticleSettings(BaseSettings):
    app_name: str = "A.N.N. Article Service"
    host: str = "0.0.0.0"
    port: int = 8002
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(default="", description="Postgres connection URL")
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase service key")
    public_url: str = Field(default="http://localhost:8000", description="Public-facing base URL")

    llm_api_key: str = Field(default="", description="OpenAI / Gemini API Key")
    llm_model: str = Field(default="gemini-2.0-flash", description="LLM model identifier")
    llm_base_url: str = Field(default="https://generativelanguage.googleapis.com/v1beta/openai", description="LLM API base URL")
    news_api_key: str = Field(default="", description="NewsAPI.org API Key")
    alpha_vantage_key: str = Field(default="", description="Alpha Vantage API Key")
    analytics_service_url: str = Field(default="http://localhost:8005", description="Analytics service URL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> ArticleSettings:
    return ArticleSettings()
