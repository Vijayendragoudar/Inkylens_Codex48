"""Clearly fictional, safe demo data for the judge workflow."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Brand, GuidelineRule


DEMO_BRAND_NAME = "Cinder & Coast — fictional sample brand"
DEMO_COPY = (
    "Our REVOLUTIONARY coffee plan gives every customer GUARANTEED energy. "
    "Join today for the best cup in the city."
)


def seed_demo_brand(db: Session) -> Brand:
    """Create the demo brand once and return the existing record thereafter."""
    existing = db.scalar(select(Brand).where(Brand.name == DEMO_BRAND_NAME))
    if existing is not None:
        return existing

    brand = Brand(
        name=DEMO_BRAND_NAME,
        description=(
            "A fictional coffee brand used only for the Inkylens demo. "
            "Its rules are sample guidance, not real organisation policy."
        ),
        guidelines=[
            GuidelineRule(
                rule_key="TERM-001",
                rule_type="forbidden_term",
                title="Avoid unsupported hype",
                content="revolutionary",
                replacement="Use a specific, supportable benefit instead.",
            ),
            GuidelineRule(
                rule_key="TERM-002",
                rule_type="preferred_term",
                title="Use guest instead of customer",
                content="customer",
                replacement="guest",
            ),
            GuidelineRule(
                rule_key="TONE-001",
                rule_type="tone",
                title="Warm, calm, and plain spoken",
                content="Use warm, calm, plain language. Avoid hype, urgency, and shouting.",
            ),
            GuidelineRule(
                rule_key="FACT-001",
                rule_type="approved_fact",
                title="Subscription offering",
                content="The sample brand offers coffee subscriptions in three sizes.",
            ),
            GuidelineRule(
                rule_key="CLAIM-001",
                rule_type="claim_constraint",
                title="Do not promise guaranteed outcomes",
                content="guaranteed",
            ),
        ],
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand
