"""Server-side, schema-validated optional AI review adapter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Iterable, Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from .config import Settings, settings
from .rules import CandidateFinding, RuleLike


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

    findings: list[AIOutputFinding] = Field(default_factory=list, max_length=20)


@dataclass(frozen=True)
class AIAnalysisResult:
    status: str
    findings: list[CandidateFinding]
    error: str | None = None


OUTPUT_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "category": {"type": "string", "enum": ["tone", "messaging", "claim"]},
                    "label": {"type": "string"},
                    "explanation": {"type": "string"},
                    "suggestion": {"type": "string"},
                    "excerpt": {"type": "string"},
                    "rule_keys": {"type": "array", "items": {"type": "string"}},
                },
                "required": [
                    "severity",
                    "category",
                    "label",
                    "explanation",
                    "suggestion",
                    "excerpt",
                    "rule_keys",
                ],
            },
        }
    },
    "required": ["findings"],
}


def _system_prompt() -> str:
    return (
        "You are Inkylens, an assistant that helps a human review text against supplied "
        "organisation guidelines. Return JSON only according to the schema. Do not invent "
        "brand policy, facts, sources, or rule keys. Only cite a rule key supplied in the "
        "guidelines. A factual or promotional statement that is not supported by an approved "
        "fact must be labelled exactly 'unsupported/unverified'; do not call it false. "
        "Offer constructive, editable suggestions. Omit findings when the supplied guidance "
        "does not support them. This output assists human review and is not a compliance decision."
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
        "Review the following content using only these supplied guidelines. Focus on tone, "
        "messaging, and unsupported claims that deterministic checks may not catch.\n\n"
        f"GUIDELINES:\n{json.dumps(guideline_payload, ensure_ascii=False)}\n\n"
        f"CONTENT:\n{text}"
    )


def _response_text(payload: dict[str, object]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct

    output = payload.get("output")
    if not isinstance(output, list):
        raise ValueError("AI response did not include output text.")
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if isinstance(part, dict) and part.get("type") == "output_text":
                text = part.get("text")
                if isinstance(text, str) and text.strip():
                    return text
    raise ValueError("AI response did not include structured output text.")


def analyze_with_ai(
    text: str,
    rules: Iterable[RuleLike],
    *,
    config: Settings | None = None,
    client: httpx.Client | None = None,
) -> AIAnalysisResult:
    """Attempt AI analysis without ever hiding an unavailable or invalid result."""
    active_config = config or settings
    rule_list = list(rules)
    if not active_config.ai_enabled:
        return AIAnalysisResult(
            status="unavailable",
            findings=[],
            error="AI analysis is not configured. Deterministic checks are still available.",
        )

    payload = {
        "model": active_config.openai_model,
        "input": [
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": _user_prompt(text, rule_list)},
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "inkylens_review",
                "strict": True,
                "schema": OUTPUT_SCHEMA,
            }
        },
    }
    headers = {
        "Authorization": f"Bearer {active_config.openai_api_key}",
        "Content-Type": "application/json",
    }

    owns_client = client is None
    request_client = client or httpx.Client(timeout=active_config.ai_timeout_seconds)
    try:
        response = request_client.post(
            "https://api.openai.com/v1/responses", headers=headers, json=payload
        )
        response.raise_for_status()
        output = AIOutput.model_validate_json(_response_text(response.json()))
        known_rule_keys = {rule.rule_key for rule in rule_list}
        findings: list[CandidateFinding] = []
        for finding in output.findings:
            if not set(finding.rule_keys).issubset(known_rule_keys):
                continue
            label = (
                "unsupported/unverified"
                if finding.category == "claim" and not finding.rule_keys
                else finding.label
            )
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
        return AIAnalysisResult(status="completed", findings=findings)
    except httpx.TimeoutException:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error="AI analysis timed out. Please retry; deterministic findings are still available.",
        )
    except httpx.HTTPStatusError as error:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error=(
                f"AI analysis is temporarily unavailable (provider status {error.response.status_code}). "
                "Please retry; deterministic findings are still available."
            ),
        )
    except (ValidationError, ValueError, TypeError, json.JSONDecodeError):
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error="AI returned an invalid result. Please retry; deterministic findings are still available.",
        )
    except httpx.HTTPError:
        return AIAnalysisResult(
            status="failed",
            findings=[],
            error="AI analysis could not be reached. Please retry; deterministic findings are still available.",
        )
    finally:
        if owns_client:
            request_client.close()
