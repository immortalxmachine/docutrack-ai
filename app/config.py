"""
Central configuration.

All tunables live in one place and are read from environment variables (or a
local `.env` file) via pydantic-settings. This keeps secrets out of the code
and makes the LLM provider switchable without touching any logic.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed, validated application settings.

    pydantic-settings loads each field from the matching environment variable
    (case-insensitive). Defaults below mean the app boots even with no `.env`,
    which is what lets the test suite run against the "mock" provider.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM provider ---
    llm_provider: str = "gemini"          # "gemini" | "ollama" | "mock"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # --- Embeddings ---
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # --- Retrieval tuning ---
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 4
    min_confidence: float = 0.30          # below this, /ask answers "I don't know"

    # --- Database ---
    database_url: str = "sqlite:///./data/docutrack.db"

    # --- Paths ---
    docs_dir: str = "data/docs"
    index_dir: str = "data/index"

    # --- UI -> API ---
    api_base_url: str = "http://localhost:8000"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so every module shares one object and the `.env` file is parsed
    exactly once per process.
    """
    return Settings()
