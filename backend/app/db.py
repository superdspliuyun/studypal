"""SQLAlchemy engine, session, and declarative base.

Enables SQLite WAL mode and foreign-key enforcement on connect so all
sessions inherit the same pragmas without each caller remembering them.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


def _sqlite_pragmas(dbapi_connection, _connection_record):  # noqa: ANN001
    """Enable WAL journal mode and FK enforcement on every SQLite connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


engine: Engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    future=True,
)

if engine.dialect.name == "sqlite":
    event.listen(engine, "connect", _sqlite_pragmas)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()