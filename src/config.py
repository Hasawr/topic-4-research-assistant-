import os
from typing import Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Engine Configuration (Swapped defaults to Gemini)
    llm_provider: Literal["anthropic", "openai", "gemini"] = Field(default="gemini")
    llm_model: str = Field(default="gemini-2.5-flash")
    
    # Provider Secret Keys (Optional depending on provider chosen)
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

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "anthropic" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER is 'anthropic'")
        return v

    # Added strict validation check for the new Gemini workflow
    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "gemini" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("GEMINI_API_KEY is required when LLM_PROVIDER is 'gemini'")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()


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
    cache_ttl_seconds: int = Field(default=86400, description="Default TTL is 24 hours (86400s)")
    cache_dir: str = Field(default="./.cache_storage")

    # Observability
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_anthropic_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "anthropic" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("❌ Missing ANTHROPIC_API_KEY: Please add it to your .env file since you selected 'anthropic' as your provider.")
        return v

    @field_validator("gemini_api_key")
    @classmethod
    def validate_gemini_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "gemini" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("❌ Missing GEMINI_API_KEY: Please add it to your .env file since you selected 'gemini' as your provider.")
        return v
        
    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: str | None, info) -> str | None:
        if info.data.get("llm_provider") == "openai" and not v:
            if os.getenv("OFFLINE_MODE") != "true":
                raise ValueError("❌ Missing OPENAI_API_KEY: Please add it to your .env file since you selected 'openai' as your provider.")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Initialize settings
settings = Settings()

# Added a friendly printout to confirm what was loaded
print(f"🚀 Settings Loaded Successfully!")
print(f"🤖 LLM Provider : {settings.llm_provider.upper()} ({settings.llm_model})")
print(f"🔍 Web Search   : {settings.web_search_provider.capitalize()}")
print(f"💾 Cache Engine : {settings.cache_backend.capitalize()}")
print(f"📊 Log Level    : {settings.log_level}")
print("-" * 40)
