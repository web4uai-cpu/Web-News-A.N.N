from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class NotificationSettings(BaseSettings):
    app_name: str = "A.N.N. Notification Service"
    host: str = "0.0.0.0"
    port: int = 8006
    debug: bool = False
    log_level: str = "INFO"

    twitter_bearer_token: str = Field(default="")
    facebook_page_token: str = Field(default="")
    facebook_page_id: str = Field(default="")
    instagram_access_token: str = Field(default="")
    instagram_account_id: str = Field(default="")

    redis_url: str = Field(default="redis://localhost:6379/0")
    public_url: str = Field(default="http://localhost:8000")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> NotificationSettings:
    return NotificationSettings()
