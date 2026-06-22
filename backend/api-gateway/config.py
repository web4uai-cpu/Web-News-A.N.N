from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class GatewaySettings(BaseSettings):
    app_name: str = "A.N.N. API Gateway"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # Downstream services
    auth_service_url: str = Field(default="http://localhost:8001", description="Auth service base URL")
    article_service_url: str = Field(default="http://localhost:8002", description="Article service base URL")
    video_service_url: str = Field(default="http://localhost:8003", description="Video service base URL")
    analytics_service_url: str = Field(default="http://localhost:8004", description="Analytics service base URL")
    search_service_url: str = Field(default="http://localhost:8005", description="Search service base URL")
    notification_service_url: str = Field(default="http://localhost:8006", description="Notification service base URL")

    # Legacy monolith (used during migration — routes not yet extracted go here)
    monolith_url: str = Field(default="http://localhost:8080", description="Legacy monolith backend URL")

    # Rate limiting
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL for rate limiting")
    rate_limit_anonymous_rpm: int = Field(default=60, description="Anonymous requests per minute per IP")
    rate_limit_authenticated_rpm: int = Field(default=600, description="Authenticated requests per minute per key")

    # CORS
    cors_origins: str = Field(default="*", description="Comma-separated allowed origins")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> GatewaySettings:
    return GatewaySettings()
