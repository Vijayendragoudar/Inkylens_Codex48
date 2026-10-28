"""Server-side, schema-validated AI review adapter for Inkylens."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import Settings, settings
from .rules import CandidateFinding, RuleLike


PROVIDER_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "groq": "https://api.groq.com/openai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
}

DEFAULT_MODELS = {
    "openai": "gpt-4o-mini",
    "groq": "openai/gpt-oss-20b",
    "gemini": "gemini-3.8-flash",
}


class AIOutputFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: Literal["low", "medium", "high"]
    category: Literal["tone", "messaging", "claim"]
    label: str = Field(min_length=1, max_length=80)
    explanation: str = Field(min_length=1, max_length=1_000)
    suggestion: str = Field(min_length=1, max_length=1_000)
    excerpt: str = Field(min_length=1, max_length=1_000)
    rule_keys: list[str] = Field(default_factory=list, max_length=10)


class AIOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    findings: list[AIOutputFinding] = Field(
        default_factory=list,
        max_length=20,
    )


@dataclass(frozen=True)
class AIAnalysisResult:
    status: str
    findings: list[CandidateFinding]
    error: str | None = None


def _system_prompt() -> str:
    return (
        "You are Inkylens, an AI assistant helping a human review content "
        "against supplied brand guidelines. Return JSON only, without "
        "Markdown or surrounding commentary, matching this structure: "
        '{"findings":[{"severity":"low|medium|high",'
        '"category":"tone|messaging|claim","label":"short label",'
        '"explanation":"why this needs review",'
        '"suggestion":"a constructive rewrite",'
        '"excerpt":"exact text from the submitted content",'
        '"rule_keys":["actual supplied rule keys"]}]}. '
        "Use an empty findings array when no supported issue is found. "
        "Do not invent brand policies, approved facts, sources, or rule keys. "
        "Only reference rule keys present in the supplied guidelines. "
        "Check tone, messaging, and unsupported promotional or factual claims. "
        "A claim that lacks support must be described as "
        "'unsupported/unverified', not declared false. "
        "Suggestions are advisory and must not override human judgement."
    )


def _user_prompt(text: str, rules: Iterable[RuleLike]) -> str:
    guideline_payload = [
        {
            "rule_key": rule.rule_key,
            "rule_type": rule.rule_type,
            "title": rule.title,
            "content": rule.content[:1_000],
            "replacement": rule.replacement,
        }
        for rule in rules
    ]

    return (
        "Review the supplied content using only these brand guidelines. "
        "Identify contextual problems that simple keyword checks might miss. "
        "For each finding, quote an exact excerpt from the content and cite "
        "only relevant rule keys. Do not invent missing evidence.\n\n"
        f"GUIDELINES:\n"
        f"{json.dumps(guideline_payload, ensure_ascii=False)}\n\n"
        f"CONTENT:\n{text}"
    )


def _extract_message_content(payload: dict) -> str:
    """Extract the assistant's text from a Chat Completions response."""
    choices = payload.get("choices")

    if not isinstance(choices, list) or not choices:
        raise ValueError("AI response did not contain any choices.")

    choice = choices[0]
    if not isinstance(choice, dict):
        raise ValueError("AI response contained an invalid choice.")

    message = choice.get("message")
    if not isinstance(message, dict):
        raise ValueError("AI response did not contain an assistant message.")

    content = message.get("content")

    if isinstance(content, str) and content.strip():
        return content

    # Some compatible APIs may represent message content as text blocks.
    if isinstance(content, list):
        parts = [
            part["text"]
            for part in content
            if isinstance(part, dict)
            and isinstance(part.get("text"), str)
        ]
        if parts:
            return "\n".join(parts)

    raise ValueError("AI response did not contain usable text.")


def _get_provider_settings(config: Settings):
    """Support new provider settings and legacy OpenAI-only settings."""
    provider = getattr(config, "ai_provider", "openai")
    provider = (provider or "openai").strip().lower()

    if provider not in PROVIDER_BASE_URLS:
        raise ValueError(
            "Unsupported AI provider. Choose openai, groq, or gemini."
        )

    if hasattr(config, "ai_api_key"):
        api_key = config.ai_api_key
    elif provider == "openai":
        api_key = getattr(config, "openai_api_key", None)
    else:
        api_key = None

    if hasattr(config, "ai_model"):
        model = config.ai_model
    elif provider == "openai":
        model = getattr(config, "openai_model", None)
    else:
        model = None

    model = (model or DEFAULT_MODELS[provider]).strip()

    base_url = getattr(config, "ai_base_url", None)
    base_url = (
        base_url.strip().rstrip("/")
        if isinstance(base_url, str) and base_url.strip()
        else PROVIDER_BASE_URLS[provider]
    )

    return provider, api_key, model, base_url


def analyze_with_ai(
    text: str,
    rules: Iterable[RuleLike],
    *,
    config: Settings | None = None,
    client: httpx.Client | None = None,
) -> AIAnalysisResult:
    """Run AI review while reporting unavailable or invalid results honestly."""
    active_config = config or settings
    rule_list = list(rules)

    try:
        provider, api_key, model, base_url = _get_provider_settings(
            active_config
        )
    except (AttributeError, TypeError, ValueError):
        return AIAnalysisResult(
            status="unavailable",
            findings=[],
            error="AI provider configuration is invalid.",
        )

    if not api_key or not api_key.strip():
        return AIAnalysisResult(
            status="unavailable",
            findings=[],
            error=(
                f"{provider.capitalize()} AI is not configured. "
                "Deterministic checks are still available."
            ),
        )

    if not model:
        return AIAnalysisResult(
            status="unavailable",
            findings=[],
            error="The selected AI model is not configured.",
        )

    # JSON object mode is used for broad provider compatibility.
    # Pydantic still validates every returned field on our server.
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _system_prompt(),
            },
            {
                "role": "user",
                "content": _user_prompt(text, rule_list),
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    owns_client = client is None
    request_client = client or httpx.Client(
        timeout=active_config.ai_timeout_seconds
    )

    try:
        response = request_client.post(
            f"{base_url}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

        response_payload = response.json()
        if not isinstance(response_payload, dict):
            raise ValueError("AI response was not a JSON object.")

        raw_content = _extract_message_content(response_payload)
        output = AIOutput.model_validate_json(raw_content)

        known_rule_keys = {rule.rule_key for rule in rule_list}
        findings: list[CandidateFinding] = []

        for finding in output.findings:
            # Never trust a model-generated rule reference that does not
            # exist in the supplied brand guidelines.
            if not set(finding.rule_keys).issubset(known_rule_keys):
                continue

            label = finding.label
            if finding.category == "claim" and not finding.rule_keys:
                label = "unsupported/unverified"

            findings.append(
                CandidateFinding(
                    source="ai_assisted",
                    severity=finding.severity,
                    category=finding.category,
                    label=label,
                    explanation=finding.explanation,
                    suggestion=finding.suggestion,
                    excerpt=finding.excerpt,
                    rule_keys=finding.rule_keys,
                )
            )

        return AIAnalysisResult(
            status="completed",
            findings=findings,
        )

    except httpx.TimeoutException:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error=(
                "AI analysis timed out. Please retry; "
                "deterministic findings are still available."
            ),
        )

    except httpx.HTTPStatusError as error:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error=(
                f"AI provider returned HTTP "
                f"{error.response.status_code}. Check the provider, model, "
                "key and API quota. Deterministic findings are still available."
            ),
        )

    except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error=(
                "AI returned an invalid result. Please retry; "
                "deterministic findings are still available."
            ),
        )

    except httpx.HTTPError:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error=(
                "AI provider could not be reached. Please retry; "
                "deterministic findings are still available."
            ),
        )

    finally:
        if owns_client:
            request_client.close()
