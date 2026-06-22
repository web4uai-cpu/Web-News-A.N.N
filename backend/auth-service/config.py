from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class AuthSettings(BaseSettings):
    app_name: str = "A.N.N. Auth Service"
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    log_level: str = "INFO"

    # Supabase
    supabase_url: str = Field(default="", description="Supabase project URL")
    supabase_key: str = Field(default="", description="Supabase anon key")
    supabase_jwt_secret: str = Field(default="", description="Supabase JWT secret for server-side verification")

    # Database
    database_url: str = Field(default="", description="Postgres connection URL")

    # Stripe
    stripe_secret_key: str = Field(default="", description="Stripe secret key")
    stripe_webhook_secret: str = Field(default="", description="Stripe webhook signing secret")

    # Admin
    admin_secret: str = Field(default="superadmin123", description="Admin token for protected routes")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> AuthSettings:
    return AuthSettings()
