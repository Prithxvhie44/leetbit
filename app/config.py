from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = Field(default=None)
    leetcode_username: str | None = Field(default=None)
    leetcode_session: str | None = Field(default=None)
    github_token: str | None = Field(default=None)
    github_repo: str | None = Field(default=None)
    github_oauth_client_id: str | None = Field(default=None)
    github_oauth_scope: str = Field(default="repo")
    github_base_branch: str = Field(default="main")
    github_base_path: Path = Field(default=Path("Leetbit-Revisions"))
    linkedin_config: str | None = Field(default=None)
    poll_interval: int = Field(default=300, ge=30)
    database_url: str = Field(default="sqlite:///./leetbit.db")
    log_level: str = Field(default="INFO")
    openai_model: str = Field(default="gpt-4.1-mini")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
