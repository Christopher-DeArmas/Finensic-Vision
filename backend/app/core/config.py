"""Application configuration loaded from environment variables.

All tunables and secrets are read here via ``pydantic-settings`` so that no
value is hard-coded elsewhere in the codebase.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- General ---
    app_name: str = "Sentinel AML"
    environment: str = Field(default="development")

    # --- Database ---
    database_url: str = Field(default="sqlite:///./sentinel.db")

    # --- OpenAI ---
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")

    # --- Streaming simulator ---
    stream_min_tps: int = Field(default=2)
    stream_max_tps: int = Field(default=5)

    # --- Risk / alerting ---
    # Score at/above which an alert is raised (High band and up).
    alert_threshold: int = Field(default=40)

    # --- Synthetic data ---
    seed: int = Field(default=42)

    # --- CORS ---
    cors_origins: str = Field(default="http://localhost:5173,http://localhost:3000")

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS origins as a clean list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def ai_enabled(self) -> bool:
        """Whether live OpenAI calls are configured."""
        return bool(self.openai_api_key.strip())


@lru_cache
def get_settings() -> Settings:
    """Return a cached ``Settings`` instance."""
    return Settings()


settings = get_settings()
