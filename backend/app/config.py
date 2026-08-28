from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Daily Content Automation"
    app_env: str = "local"
    database_url: str = "sqlite+aiosqlite:///./data/content.db"

    admin_token: str = "change-me"
    cron_secret: str = "change-me-cron"

    llm_provider: str = "gemini"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    tavily_api_key: str = ""

    anthropic_base_url: str = ""
    anthropic_auth_token: str = ""
    anthropic_model: str = "claude-sonnet-5"

    daily_run_hour: int = 11
    daily_run_minute: int = 0
    timezone: str = "Asia/Kolkata"

    linkedin_enabled: bool = False
    linkedin_access_token: str = ""
    linkedin_author_urn: str = ""
    linkedin_version: str = "202606"

    medium_enabled: bool = False

    publish_enabled: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
