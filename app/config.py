"""Configuration settings for DocuMind AI application."""
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    app_env: str = "development"
    log_level: str = "INFO"

    # Persistent Storage
    chroma_persist_directory: str = "./data/chroma"
    chroma_collection_name: str = "documind_collection"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 25

    # Embedding settings
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # Chunking settings
    chunk_size: int = 500
    chunk_overlap: int = 100

    # Retrieval settings
    top_k: int = 5

    # LLM Settings
    llm_provider: str = "openai"  # "openai", "groq", "ollama", "mock"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def ensure_directories(self) -> None:
        """Ensure necessary runtime directories exist."""
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    settings = Settings()
    settings.ensure_directories()
    return settings
