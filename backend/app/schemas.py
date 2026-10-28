"""Validated API request and response shapes."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RuleType = Literal[
    "forbidden_term",
    "preferred_term",
    "tone",
    "approved_fact",
    "claim_constraint",
]
DecisionState = Literal["open", "resolved", "dismissed", "accepted_exception"]
Severity = Literal["low", "medium", "high"]


class GuidelineRuleInput(BaseModel):
    rule_key: str = Field(min_length=3, max_length=40)
    rule_type: RuleType
    title: str = Field(min_length=2, max_length=140)
    content: str = Field(min_length=1, max_length=2_000)
    replacement: str | None = Field(default=None, max_length=200)


class GuidelineRuleRead(GuidelineRuleInput):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class BrandCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str = Field(default="", max_length=2_000)
    guidelines: list[GuidelineRuleInput] = Field(default_factory=list, max_length=100)


class BrandUpdate(BrandCreate):
    pass


class BrandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    guidelines: list[GuidelineRuleRead]


class ReviewCreate(BaseModel):
    brand_id: str
    text: str = Field(min_length=1, max_length=20_000)
    prior_review_id: str | None = None


class FindingDecisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    state: DecisionState
    note: str
    updated_at: datetime


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    severity: Severity
    category: str
    label: str
    explanation: str
    suggestion: str
    excerpt: str
    rule_keys: list[str]
    created_at: datetime
    decision: FindingDecisionRead | None = None


class ReviewRead(BaseModel):
    id: str
    brand_id: str
    submission_id: str
    submission_text: str
    revision_number: int
    ai_status: str
    ai_error: str | None
    created_at: datetime
    findings: list[FindingRead]


class ReviewHistoryItem(BaseModel):
    id: str
    revision_number: int
    created_at: datetime
    ai_status: str
    finding_count: int
    excerpt: str


class FindingDecisionUpdate(BaseModel):
    state: DecisionState
    note: str = Field(default="", max_length=2_000)


class HealthRead(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
    ai_configured: bool
