from pathlib import Path
import os
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / ".env"

print("DEBUG config.py:", Path(__file__).resolve())
print("DEBUG project root:", PROJECT_ROOT)
print("DEBUG .env path:", ENV_PATH)
print("DEBUG .env exists:", ENV_PATH.exists())


class Settings(BaseSettings):
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
    cache_ttl_seconds: int = Field(default=86400)
    cache_dir: str = Field(default="./.cache_storage")

    # Extra settings from your .env
    per_source_timeout_seconds: int = Field(default=10)
    max_sources_per_query: int = Field(default=3)

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "anthropic" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'")
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "gemini" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "openai" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER is 'openai'")
        return v

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()

print("Settings Loaded Successfully!")
print(f"LLM Provider : {settings.llm_provider.upper()} ({settings.llm_model})")
print(f"Gemini Key   : {'Loaded' if settings.gemini_api_key else 'Missing'}")
print(f"Tavily Key   : {'Loaded' if settings.tavily_api_key else 'Missing'}")
print(f"Web Search   : {settings.web_search_provider}")
print(f"Cache Engine : {settings.cache_backend}")
print(f"Log Level    : {settings.log_level}")
print("-" * 40)