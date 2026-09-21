"""Application configuration via Pydantic Settings.

All settings are loaded from environment variables or .env file.
Grouped into logical sub-models for clarity.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Root application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────
    app_env: AppEnv = AppEnv.DEVELOPMENT
    app_name: str = "Personal AI Astrologer"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # ── Security / Auth ──────────────────────────
    secret_key: str = "CHANGE-ME-generate-a-64-char-random-string"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── Database ─────────────────────────────────
    database_url: str = "postgresql+asyncpg://astrologer:astrologer@localhost:5432/astrologer"
    database_echo: bool = False
    database_pool_size: int = 10

    # ── Redis ────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    redis_cache_ttl: int = 3600

    # ── Celery ───────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # ── AI Provider ──────────────────────────────
    ai_provider: str = "gemini"
    ai_model: str = "gemini-2.0-flash"
    gemini_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # ── Astrology ────────────────────────────────
    ephemeris_path: str = ""
    default_house_system: str = "placidus"
    default_ayanamsa: str = "lahiri"

    # ── Geocoding ────────────────────────────────
    geocoding_provider: str = "nominatim"
    geocoding_api_key: str = ""
    nominatim_user_agent: str = "personal-ai-astrologer/0.1.0"

    # ── Voice ────────────────────────────────────
    stt_provider: str = ""
    stt_api_key: str = ""
    tts_provider: str = ""
    tts_api_key: str = ""

    # ── Storage ──────────────────────────────────
    storage_provider: str = "local"
    storage_local_path: str = "./storage"
    storage_bucket: str = ""

    # ── Notifications ────────────────────────────
    notification_provider: str = ""

    # ── Rate Limiting ────────────────────────────
    rate_limit_auth: str = "20/minute"
    rate_limit_chat: str = "30/minute"
    rate_limit_chart: str = "10/minute"
    rate_limit_voice: str = "10/minute"
    rate_limit_report: str = "5/minute"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnv.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.app_env == AppEnv.TESTING


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
