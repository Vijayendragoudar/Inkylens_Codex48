
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
    """Use a writable but non-durable database location on serverless demos."""
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/inkylens.db"
    return "sqlite:///./inkylens.db"


@dataclass(frozen=True)
class Settings:
    database_url: str

    # New multi-provider AI settings
    ai_provider: str
    ai_api_key: str | None
    ai_base_url: str | None
    ai_model: str

    # Retain legacy OpenAI settings while the AI adapter is migrated.
    openai_api_key: str | None
    openai_model: str

    ai_timeout_seconds: float

    @property
    def ai_enabled(self) -> bool:
        """True when the selected provider has a configured key."""
        return bool(self.ai_api_key)


def load_settings() -> Settings:
    provider = os.getenv(
        "INKYLENS_AI_PROVIDER", "groq"
    ).strip().lower()

    openai_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    groq_key = os.getenv("GROQ_API_KEY", "").strip() or None
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip() or None

    provider_keys = {
        "openai": openai_key,
        "groq": groq_key,
        "gemini": gemini_key,
    }

    provider_urls = {
        "openai": None,
        "groq": "https://api.groq.com/openai/v1",
        "gemini": (
            "https://generativelanguage.googleapis.com/v1beta/openai/"
        ),
    }

    default_models = {
        "openai": "gpt-4o-mini",
        "groq": "llama-3.3-70b-versatile",
        "gemini": "gemini-3.8-flash",
    }

    configured_model = os.getenv("INKYLENS_AI_MODEL", "").strip()

    # Preserve the former OpenAI model variable for backward compatibility.
    legacy_openai_model = os.getenv(
        "INKYLENS_OPENAI_MODEL", "gpt-4o-mini"
    ).strip()

    if configured_model:
        selected_model = configured_model
    elif provider == "openai":
        selected_model = legacy_openai_model
    else:
        selected_model = default_models.get(provider, "")

    return Settings(
        database_url=os.getenv(
            "INKYLENS_DATABASE_URL", _default_database_url()
        ),
        ai_provider=provider,
        ai_api_key=provider_keys.get(provider),
        ai_base_url=provider_urls.get(provider),
        ai_model=selected_model,
        openai_api_key=openai_key,
        openai_model=legacy_openai_model,
        ai_timeout_seconds=_positive_float(
            os.getenv("INKYLENS_AI_TIMEOUT_SECONDS"),
            default=20.0,
        ),
    )


settings = load_settings()
