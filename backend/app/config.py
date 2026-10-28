"""Configuration loaded only from the server environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def _positive_float(value: str | None, default: float) -> float:
    try:
        parsed = float(value) if value is not None else default
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def _default_database_url() -> str:
    """Use a writable, explicitly non-durable SQLite location on serverless demos."""
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/inkylens.db"
    return "sqlite:///./inkylens.db"


@dataclass(frozen=True)
class Settings:
    database_url: str
    openai_api_key: str | None
    openai_model: str
    ai_timeout_seconds: float

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key)


def load_settings() -> Settings:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    return Settings(
        database_url=os.getenv("INKYLENS_DATABASE_URL", _default_database_url()),
        openai_api_key=api_key or None,
        openai_model=os.getenv("INKYLENS_OPENAI_MODEL", "gpt-4o-mini"),
        ai_timeout_seconds=_positive_float(
            os.getenv("INKYLENS_AI_TIMEOUT_SECONDS"), default=20.0
        ),
    )


settings = load_settings()
