"""Database engine and request-scoped session helpers."""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings


engine_options: dict[str, object] = {"future": True}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    """Base class for all persisted Inkylens records."""


def get_db() -> Generator[Session, None, None]:
    """Yield one database session and always release it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
