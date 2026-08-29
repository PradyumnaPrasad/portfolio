"""Database engine and session.

Local dev falls back to a SQLite file so the app runs with zero setup.
Production sets DATABASE_URL to a Postgres URL (Neon). Render / Heroku style
``postgres://`` URLs are normalised to the psycopg v3 driver.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

_DEFAULT = f"sqlite:///{Path(__file__).resolve().parent.parent / 'portfolio.db'}"


def _normalise(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


DATABASE_URL = _normalise(os.getenv("DATABASE_URL", "").strip() or _DEFAULT)

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
