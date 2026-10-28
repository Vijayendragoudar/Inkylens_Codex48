"""FastAPI application for the Inkylens judge-ready MVP."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from .ai import analyze_with_ai
from .config import PROJECT_ROOT, settings
from .database import Base, SessionLocal, engine, get_db
from .models import Brand, Finding, FindingDecision, GuidelineRule, Review, Submission
from .rules import CandidateFinding, run_deterministic_checks
from .schemas import (
    BrandCreate,
    BrandRead,
    BrandUpdate,
    FindingDecisionRead,
    FindingDecisionUpdate,
    FindingRead,
    GuidelineRuleInput,
    GuidelineRuleRead,
    HealthRead,
    ReviewCreate,
    ReviewHistoryItem,
    ReviewRead,
)
from .seed import seed_demo_brand


def initialise_database() -> None:
    """Create the local schema and seeded demo before serving requests."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_demo_brand(db)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialise_database()
    yield


app = FastAPI(
    title="Inkylens API",
    version="0.1.0",
    description="Explainable, human-in-the-loop brand-governance review API.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH"],
    allow_headers=["Content-Type"],
)


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} was not found.")


def _get_brand(db: Session, brand_id: str) -> Brand:
    brand = db.scalar(
        select(Brand)
        .where(Brand.id == brand_id)
        .options(selectinload(Brand.guidelines))
    )
    if brand is None:
        raise _not_found("Brand")
    return brand


def _normalise_rules(rules: list[GuidelineRuleInput]) -> list[GuidelineRuleInput]:
    normalised: list[GuidelineRuleInput] = []
    seen_keys: set[str] = set()
    for rule in rules:
        key = rule.rule_key.strip().upper()
        if not key:
            raise HTTPException(status_code=422, detail="Each guideline needs a rule key.")
        if key in seen_keys:
            raise HTTPException(status_code=422, detail=f"Guideline key {key} is duplicated.")
        if not rule.title.strip() or not rule.content.strip():
            raise HTTPException(status_code=422, detail=f"Guideline {key} needs a title and content.")
        if rule.rule_type == "preferred_term" and not (rule.replacement or "").strip():
            raise HTTPException(
                status_code=422,
                detail=f"Preferred-term guideline {key} needs a preferred replacement.",
            )
        seen_keys.add(key)
        normalised.append(
            GuidelineRuleInput(
                rule_key=key,
                rule_type=rule.rule_type,
                title=rule.title.strip(),
                content=rule.content.strip(),
                replacement=rule.replacement.strip() if rule.replacement else None,
            )
        )
    return normalised


def _apply_brand_payload(brand: Brand, payload: BrandCreate | BrandUpdate) -> None:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Brand name cannot be blank.")
    brand.name = name
    brand.description = payload.description.strip()
    brand.guidelines.clear()
    for rule in _normalise_rules(payload.guidelines):
        brand.guidelines.append(
            GuidelineRule(
                rule_key=rule.rule_key,
                rule_type=rule.rule_type,
                title=rule.title,
                content=rule.content,
                replacement=rule.replacement,
            )
        )


def _brand_read(brand: Brand) -> BrandRead:
    return BrandRead(
        id=brand.id,
        name=brand.name,
        description=brand.description,
        created_at=brand.created_at,
        updated_at=brand.updated_at,
        guidelines=[GuidelineRuleRead.model_validate(rule) for rule in brand.guidelines],
    )


def _finding_read(finding: Finding) -> FindingRead:
    decision = (
        FindingDecisionRead.model_validate(finding.decision) if finding.decision is not None else None
    )
    return FindingRead(
        id=finding.id,
        source=finding.source,
        severity=finding.severity,
        category=finding.category,
        label=finding.label,
        explanation=finding.explanation,
        suggestion=finding.suggestion,
        excerpt=finding.excerpt,
        rule_keys=finding.rule_keys,
        created_at=finding.created_at,
        decision=decision,
    )


def _review_read(review: Review) -> ReviewRead:
    return ReviewRead(
        id=review.id,
        brand_id=review.brand_id,
        submission_id=review.submission_id,
        submission_text=review.submission.text,
        revision_number=review.submission.revision_number,
        ai_status=review.ai_status,
        ai_error=review.ai_error,
        created_at=review.created_at,
        findings=[_finding_read(finding) for finding in review.findings],
    )


def _get_review(db: Session, review_id: str) -> Review:
    review = db.scalar(
        select(Review)
        .where(Review.id == review_id)
        .options(
            selectinload(Review.submission),
            selectinload(Review.findings).selectinload(Finding.decision),
        )
    )
    if review is None:
        raise _not_found("Review")
    return review


@app.get("/api/health", response_model=HealthRead)
def health_check(db: Session = Depends(get_db)) -> HealthRead:
    db.execute(text("SELECT 1"))
    return HealthRead(status="ok", database="ok", ai_configured=settings.ai_enabled)


@app.get("/api/brands", response_model=list[BrandRead])
def list_brands(db: Session = Depends(get_db)) -> list[BrandRead]:
    brands = db.scalars(select(Brand).options(selectinload(Brand.guidelines)).order_by(Brand.name)).all()
    return [_brand_read(brand) for brand in brands]


@app.post("/api/brands", response_model=BrandRead, status_code=status.HTTP_201_CREATED)
def create_brand(payload: BrandCreate, db: Session = Depends(get_db)) -> BrandRead:
    brand = Brand(name="Untitled")
    _apply_brand_payload(brand, payload)
    db.add(brand)
    db.commit()
    db.refresh(brand)
    return _brand_read(_get_brand(db, brand.id))


@app.get("/api/brands/{brand_id}", response_model=BrandRead)
def get_brand(brand_id: str, db: Session = Depends(get_db)) -> BrandRead:
    return _brand_read(_get_brand(db, brand_id))


@app.put("/api/brands/{brand_id}", response_model=BrandRead)
def update_brand(brand_id: str, payload: BrandUpdate, db: Session = Depends(get_db)) -> BrandRead:
    brand = _get_brand(db, brand_id)
    _apply_brand_payload(brand, payload)
    db.commit()
    return _brand_read(_get_brand(db, brand_id))


def _next_revision_number(db: Session, brand_id: str, prior_review_id: str | None) -> int:
    if prior_review_id is not None:
        prior = _get_review(db, prior_review_id)
        if prior.brand_id != brand_id:
            raise HTTPException(
                status_code=422,
                detail="The prior review belongs to a different brand.",
            )
        return prior.submission.revision_number + 1
    latest = db.scalar(
        select(func.max(Submission.revision_number)).where(Submission.brand_id == brand_id)
    )
    return (latest or 0) + 1


def _persist_findings(review: Review, candidates: list[CandidateFinding]) -> None:
    for candidate in candidates:
        finding = Finding(
            source=candidate.source,
            severity=candidate.severity,
            category=candidate.category,
            label=candidate.label,
            explanation=candidate.explanation,
            suggestion=candidate.suggestion,
            excerpt=candidate.excerpt,
            rule_keys=candidate.rule_keys,
            decision=FindingDecision(state="open"),
        )
        review.findings.append(finding)


@app.post("/api/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(payload: ReviewCreate, db: Session = Depends(get_db)) -> ReviewRead:
    content = payload.text.strip()
    if not content:
        raise HTTPException(status_code=422, detail="Content cannot be blank.")
    brand = _get_brand(db, payload.brand_id)
    revision_number = _next_revision_number(db, brand.id, payload.prior_review_id)
    submission = Submission(brand_id=brand.id, text=content, revision_number=revision_number)
    review = Review(brand_id=brand.id, submission=submission, ai_status="pending")

    deterministic_findings = run_deterministic_checks(content, brand.guidelines)
    ai_result = analyze_with_ai(content, brand.guidelines)
    review.ai_status = ai_result.status
    review.ai_error = ai_result.error
    _persist_findings(review, deterministic_findings + ai_result.findings)

    db.add(review)
    db.commit()
    return _review_read(_get_review(db, review.id))


@app.get("/api/reviews/{review_id}", response_model=ReviewRead)
def get_review(review_id: str, db: Session = Depends(get_db)) -> ReviewRead:
    return _review_read(_get_review(db, review_id))


@app.get("/api/brands/{brand_id}/reviews", response_model=list[ReviewHistoryItem])
def list_review_history(brand_id: str, db: Session = Depends(get_db)) -> list[ReviewHistoryItem]:
    _get_brand(db, brand_id)
    reviews = db.scalars(
        select(Review)
        .where(Review.brand_id == brand_id)
        .options(selectinload(Review.submission), selectinload(Review.findings))
        .order_by(Review.created_at.desc())
    ).all()
    return [
        ReviewHistoryItem(
            id=review.id,
            revision_number=review.submission.revision_number,
            created_at=review.created_at,
            ai_status=review.ai_status,
            finding_count=len(review.findings),
            excerpt=review.submission.text[:180],
        )
        for review in reviews
    ]


@app.patch("/api/findings/{finding_id}/decision", response_model=FindingDecisionRead)
def update_finding_decision(
    finding_id: str,
    payload: FindingDecisionUpdate,
    db: Session = Depends(get_db),
) -> FindingDecisionRead:
    finding = db.scalar(
        select(Finding).where(Finding.id == finding_id).options(selectinload(Finding.decision))
    )
    if finding is None:
        raise _not_found("Finding")
    if finding.decision is None:
        finding.decision = FindingDecision(state=payload.state, note=payload.note.strip())
    else:
        finding.decision.state = payload.state
        finding.decision.note = payload.note.strip()
    db.commit()
    db.refresh(finding.decision)
    return FindingDecisionRead.model_validate(finding.decision)


@app.get("/", include_in_schema=False, response_model=None)
def root() -> FileResponse | JSONResponse:
    index = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    if index.exists():
        return FileResponse(index)
    return JSONResponse(
        {"message": "Inkylens API is running. Start the frontend development server on port 5173."}
    )


frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
