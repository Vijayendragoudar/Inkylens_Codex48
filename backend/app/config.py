
"""Server-side configuration for Inkylens AI providers."""

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
    except (ValueError, TypeError):
        return default
    return parsed if parsed > 0 else default


def _default_database_url() -> str:
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/inkylens.db"
    return "sqlite:///./inkylens.db"


@dataclass(frozen=True)
class Settings:
    # Original fields remain first for positional compatibility.
    database_url: str
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = 20.0

    # Multi-provider settings.
    ai_provider: str = "openai"
    ai_api_key: str | None = None
    ai_base_url: str | None = None
    ai_model: str = "gpt-4o-mini"

    def __post_init__(self) -> None:
        # Fall back to legacy OpenAI settings when new fields aren't supplied.
        if self.ai_api_key is None and self.openai_api_key:
            object.__setattr__(self, "ai_api_key", self.openai_api_key)

        if self.ai_provider == "openai":
            if self.ai_base_url is None:
                object.__setattr__(
                    self, "ai_base_url", "https://api.openai.com/v1"
                )
            if self.ai_model == "gpt-4o-mini" and self.openai_model:
                object.__setattr__(self, "ai_model", self.openai_model)

    @property
    def ai_enabled(self) -> bool:
        return bool(self.ai_api_key)


def load_settings() -> Settings:
    provider = os.getenv("INKYLENS_AI_PROVIDER", "groq").strip().lower()

    openai_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    groq_key = os.getenv("GROQ_API_KEY", "").strip() or None
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or None

    provider_keys = {
        "openai": openai_key,
        "groq": groq_key,
        "gemini": gemini_key,
    }

    provider_urls = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    }

    default_models = {
        "openai": os.getenv("INKYLENS_OPENAI_MODEL", "gpt-4o-mini").strip(),
        "groq": "openai/gpt-oss-20b",
        "gemini": "gemini-3.8-flash",
    }

    selected_model = (
        os.getenv("INKYLENS_AI_MODEL", "").strip()
        or default_models.get(provider, "")
    )

    return Settings(
        database_url=os.getenv(
            "INKYLENS_DATABASE_URL", _default_database_url()
        ),
        openai_api_key=openai_key,
        openai_model=os.getenv(
            "INKYLENS_OPENAI_MODEL", "gpt-4o-mini"
        ).strip(),
        ai_timeout_seconds=_positive_float(
            os.getenv("INKYLENS_AI_TIMEOUT_SECONDS"), 20.0
        ),
        ai_provider=provider,
        ai_api_key=provider_keys.get(provider),
        ai_base_url=provider_urls.get(provider),
        ai_model=selected_model,
    )


settings = load_settings()
