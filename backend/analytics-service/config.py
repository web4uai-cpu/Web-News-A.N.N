from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class AnalyticsSettings(BaseSettings):
    app_name: str = "A.N.N. Analytics Service"
    host: str = "0.0.0.0"
    port: int = 8004
    debug: bool = False
    log_level: str = "INFO"

    database_url: str = Field(default="", description="Postgres connection URL")
    redis_url: str = Field(default="redis://localhost:6379/0")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> AnalyticsSettings:
    return AnalyticsSettings()
