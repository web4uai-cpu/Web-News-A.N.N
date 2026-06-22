from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class RAGSettings(BaseSettings):
    openai_api_key: str = Field(default="", alias="LLM_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    embedding_model: str = Field(default="text-embedding-3-small")
    embedding_dimensions: int = Field(default=1536)

    database_url: str = Field(default="")
    chunk_size: int = Field(default=500)
    chunk_overlap: int = Field(default=50)
    top_k: int = Field(default=5)
    similarity_threshold: float = Field(default=0.7)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> RAGSettings:
    return RAGSettings()
