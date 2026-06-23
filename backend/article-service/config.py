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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> ArticleSettings:
    return ArticleSettings()
