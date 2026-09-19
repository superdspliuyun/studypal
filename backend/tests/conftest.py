"""Pytest fixtures: in-memory SQLite + dependency overrides for the FastAPI app."""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Force a stable dev secret before app modules import settings.
os.environ.setdefault("JWT_SECRET", "test-secret-not-for-prod")
os.environ.setdefault("ENV", "dev")

from app import db as db_module  # noqa: E402
from app.deps import get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture()
def session_factory():
    """Yield a fresh in-memory SQLite session factory, patched into app.db."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    from app.db import Base
    import app.models  # noqa: F401  -- register models on Base.metadata
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    # Patch the app's module-level engine / SessionLocal so get_db() uses ours.
    original_engine, original_session = db_module.engine, db_module.SessionLocal
    db_module.engine = engine
    db_module.SessionLocal = TestingSession
    try:
        yield TestingSession
    finally:
        db_module.engine = original_engine
        db_module.SessionLocal = original_session
        engine.dispose()


@pytest.fixture()
def client(session_factory):
    """FastAPI TestClient with get_db overridden to the in-memory session."""
    from app.db import get_db as real_get_db

    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[real_get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()