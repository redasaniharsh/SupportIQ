"""Application settings loaded from environment variables / .env file.

No secret ever gets a real default value here — required secrets must be
supplied via the environment (or backend/.env, which is git-ignored).
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor .env to the backend/ directory (this file lives at backend/app/core/config.py,
# so backend/ is two parents up) so settings load the same values regardless of the
# shell's current working directory when a script is invoked (repo root vs backend/
# vs backend/scripts/ all resolve to the same backend/.env).
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # --- MongoDB ---
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="ai_service_desk", alias="MONGODB_DATABASE")

    # --- Pinecone ---
    pinecone_api_key: str = Field(default="", alias="PINECONE_API_KEY")
    pinecone_index_name: str = Field(default="ai-service-desk", alias="PINECONE_INDEX_NAME")
    pinecone_cloud: str = Field(default="aws", alias="PINECONE_CLOUD")
    pinecone_region: str = Field(default="us-east-1", alias="PINECONE_REGION")

    # --- LLM (Groq, OpenAI-compatible) ---
    llm_provider: str = Field(default="groq", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.groq.com/openai/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="llama-3.3-70b-versatile", alias="LLM_MODEL")

    # --- App / CORS ---
    frontend_url: str = Field(default="http://localhost:5173", alias="FRONTEND_URL")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")

    # --- Similarity thresholds ---
    similarity_duplicate_threshold: float = Field(default=0.90, alias="SIMILARITY_DUPLICATE_THRESHOLD")
    similarity_related_threshold: float = Field(default=0.75, alias="SIMILARITY_RELATED_THRESHOLD")

    # --- AI provider switch: "groq" (real) or "mock" (tests / offline dev) ---
    ai_provider: str = Field(default="groq", alias="AI_PROVIDER")

    # --- Embeddings ---
    embedding_model: str = Field(default="llama-text-embed-v2", alias="EMBEDDING_MODEL")

    # --- Misc ---
    environment: str = Field(default="development", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        extra="ignore",
        populate_by_name=True,
    )

    @property
    def is_mock_ai(self) -> bool:
        return self.ai_provider.lower() == "mock" or self.llm_provider.lower() == "mock"

    @property
    def is_groq(self) -> bool:
        return self.llm_provider.lower() == "groq" or "groq.com" in self.llm_base_url


@lru_cache
def get_settings() -> Settings:
    return Settings()
