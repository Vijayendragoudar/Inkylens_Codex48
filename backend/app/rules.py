"""Deterministic, independently testable brand-guideline checks."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, Protocol


class RuleLike(Protocol):
    rule_key: str
    rule_type: str
    title: str
    content: str
    replacement: str | None


@dataclass(frozen=True)
class CandidateFinding:
    source: str
    severity: str
    category: str
    label: str
    explanation: str
    suggestion: str
    excerpt: str
    rule_keys: list[str]


def _phrase_match(text: str, phrase: str) -> re.Match[str] | None:
    """Match a configured phrase without matching inside a larger word."""
    phrase = phrase.strip()
    if not phrase:
        return None
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text, flags=re.IGNORECASE)


def _excerpt(text: str, start: int, end: int, context: int = 48) -> str:
    prefix = "…" if start > context else ""
    suffix = "…" if end < len(text) - context else ""
    return f"{prefix}{text[max(0, start - context):min(len(text), end + context)].strip()}{suffix}"


def _term_finding(text: str, rule: RuleLike) -> CandidateFinding | None:
    match = _phrase_match(text, rule.content)
    if not match:
        return None

    is_claim = rule.rule_type == "claim_constraint"
    if is_claim:
        return CandidateFinding(
            source="deterministic",
            severity="high",
            category="claim",
            label="unsupported/unverified",
            explanation=(
                f"This uses “{match.group(0)}”, which matches the claim restriction "
                f"{rule.rule_key}: {rule.title}. The claim needs human verification."
            ),
            suggestion="Remove, qualify, or support this claim with an approved fact.",
            excerpt=_excerpt(text, match.start(), match.end()),
            rule_keys=[rule.rule_key],
        )

    if rule.rule_type == "preferred_term":
        preferred = rule.replacement or "the approved terminology"
        return CandidateFinding(
            source="deterministic",
            severity="medium",
            category="terminology",
            label="preferred terminology",
            explanation=(
                f"This uses “{match.group(0)}”. Rule {rule.rule_key}: {rule.title} "
                f"asks for “{preferred}” instead."
            ),
            suggestion=f"Replace “{match.group(0)}” with “{preferred}”.",
            excerpt=_excerpt(text, match.start(), match.end()),
            rule_keys=[rule.rule_key],
        )

    replacement = rule.replacement or "remove or rewrite the phrase"
    return CandidateFinding(
        source="deterministic",
        severity="high",
        category="terminology",
        label="forbidden terminology",
        explanation=(
            f"This uses “{match.group(0)}”, which conflicts with rule "
            f"{rule.rule_key}: {rule.title}."
        ),
        suggestion=f"{replacement[:1].upper()}{replacement[1:]}",
        excerpt=_excerpt(text, match.start(), match.end()),
        rule_keys=[rule.rule_key],
    )


def _all_caps_finding(text: str) -> CandidateFinding | None:
    words = re.findall(r"\b[A-Z]{5,}\b", text)
    if not words:
        return None
    sample = words[0]
    match = re.search(re.escape(sample), text)
    assert match is not None
    return CandidateFinding(
        source="deterministic",
        severity="low",
        category="accessibility",
        label="readability check",
        explanation=(
            f"“{sample}” is written in all caps. Extended all-caps text can be harder to read "
            "and may sound like shouting."
        ),
        suggestion="Use sentence case unless the term is an approved acronym.",
        excerpt=_excerpt(text, match.start(), match.end()),
        rule_keys=[],
    )


def run_deterministic_checks(text: str, rules: Iterable[RuleLike]) -> list[CandidateFinding]:
    """Return reproducible findings without using any external service."""
    findings: list[CandidateFinding] = []
    for rule in rules:
        if rule.rule_type not in {"forbidden_term", "preferred_term", "claim_constraint"}:
            continue
        finding = _term_finding(text, rule)
        if finding is not None:
            findings.append(finding)

    accessibility = _all_caps_finding(text)
    if accessibility is not None:
        findings.append(accessibility)

    return findings
