from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class SearchSettings(BaseSettings):
    app_name: str = "A.N.N. Search Service"
    host: str = "0.0.0.0"
    port: int = 8005
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(default="", description="Postgres connection URL")
    article_service_url: str = Field(default="http://localhost:8002", description="Article service for indexing")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> SearchSettings:
    return SearchSettings()
