"""Application configuration and settings management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env from project root
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Pydantic settings model with environment variable binding."""

    model_config = SettingsConfigDict(
        env_file=str(env_path),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM Configuration
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    model_name: str = Field(default="gpt-4o-mini", alias="MODEL_NAME")
    temperature: float = Field(default=0.3, alias="TEMPERATURE")
    max_tokens: int = Field(default=1024, alias="MAX_TOKENS")

    # Database
    database_url: str = Field(default="sqlite:///data/aquamax.db", alias="DATABASE_URL")

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )
    log_format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        alias="LOG_FORMAT",
    )

    # Server
    api_port: int = Field(default=8000, alias="API_PORT")
    ui_port: int = Field(default=8501, alias="UI_PORT")

    # Feature flags
    enable_tool_confirmation: bool = Field(default=False, alias="ENABLE_TOOL_CONFIRMATION")
    enable_human_handoff: bool = Field(default=True, alias="ENABLE_HUMAN_HANDOFF")

    # Derived paths
    @property
    def project_root(self) -> Path:
        return Path(__file__).resolve().parents[3]

    @property
    def data_dir(self) -> Path:
        path = self.project_root / "data"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def db_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.replace("sqlite:///", ""))
        return self.data_dir / "aquamax.db"

    def validate(self) -> None:
        """Validate critical settings at runtime."""
        if not self.openai_api_key or self.openai_api_key == "sk-your-api-key-here":
            raise ValueError(
                "OPENAI_API_KEY is not set. Please configure it in your .env file."
            )


# Singleton settings instance
settings = Settings()
