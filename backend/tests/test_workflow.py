from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app import main
from backend.app.ai import AIAnalysisResult
from backend.app.database import Base
from backend.app.schemas import FindingDecisionUpdate, ReviewCreate
from backend.app.seed import seed_demo_brand


def test_review_history_and_human_decision_persist(monkeypatch):
    engine = create_engine("sqlite://")
    session_factory = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(engine)
    db = session_factory()
    monkeypatch.setattr(
        main,
        "analyze_with_ai",
        lambda *_args, **_kwargs: AIAnalysisResult(
            status="unavailable",
            findings=[],
            error="AI test fallback",
        ),
    )
    try:
        brand = seed_demo_brand(db)
        first = main.create_review(
            ReviewCreate(
                brand_id=brand.id,
                text="Our REVOLUTIONARY plan is GUARANTEED for every customer.",
            ),
            db,
        )
        assert first.revision_number == 1
        assert first.ai_status == "unavailable"
        assert any(item.label == "unsupported/unverified" for item in first.findings)

        decision = main.update_finding_decision(
            first.findings[0].id,
            FindingDecisionUpdate(state="resolved", note="Rewritten in revision two."),
            db,
        )
        assert decision.state == "resolved"

        second = main.create_review(
            ReviewCreate(
                brand_id=brand.id,
                text="Our coffee plan is ready for every guest.",
                prior_review_id=first.id,
            ),
            db,
        )
        assert second.revision_number == 2

        db.expire_all()
        reopened = main.get_review(first.id, db)
        assert reopened.submission_text.startswith("Our REVOLUTIONARY")
        assert reopened.findings[0].decision is not None
        assert reopened.findings[0].decision.state == "resolved"

        history = main.list_review_history(brand.id, db)
        assert [item.revision_number for item in history] == [2, 1]
    finally:
        db.close()
        engine.dispose()
