"""
Configuration module for the Async Research Assistant.

This module uses Pydantic BaseSettings to manage environment variables,
validate API keys based on the selected LLM provider, and configure
caching and observability parameters.
"""

import os
import logging
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """
    Application settings managed via environment variables.
    Loads from a .env file and validates required dependencies.
    """

    # LLM Engine Configuration
    llm_provider: Literal["anthropic", "openai", "gemini"] = Field(default="gemini")
    llm_model: str = Field(default="gemini-2.5-flash")

    # Provider Secret Keys
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    gemini_api_key: str | None = None

    # Web Search Configuration
    web_search_provider: Literal["tavily", "serper", "duckduckgo"] = Field(default="duckduckgo")
    tavily_api_key: str | None = None
    serper_api_key: str | None = None

    # Cache Control Parameters
    cache_backend: Literal["memory", "filesystem"] = Field(default="memory")
    cache_ttl_seconds: int = Field(default=86400, description="Default TTL is 24 hours")
    cache_dir: str = Field(default="./.cache_storage")

    # Extra runtime settings
    per_source_timeout_seconds: int = Field(default=10)
    max_sources_per_query: int = Field(default=3)

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("llm_provider") == "anthropic" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError(
                    "Missing ANTHROPIC_API_KEY: Please add it to your .env file "
                    "since you selected 'anthropic' as your provider."
                )
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("llm_provider") == "gemini" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError(
                    "Missing GEMINI_API_KEY: Please add it to your .env file "
                    "since you selected 'gemini' as your provider."
                )
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None, info: ValidationInfo) -> str | None:
        if info.data.get("llm_provider") == "openai" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError(
                    "Missing OPENAI_API_KEY: Please add it to your .env file "
                    "since you selected 'openai' as your provider."
                )
        return v

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logger.info("Settings Loaded Successfully!")
    logger.info("LLM Provider : %s (%s)", settings.llm_provider.upper(), settings.llm_model)
    logger.info("Web Search   : %s", settings.web_search_provider)
    logger.info("Cache Engine : %s", settings.cache_backend)
    logger.info("Log Level    : %s", settings.log_level)