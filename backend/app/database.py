"""
database.py — SQLAlchemy engine, session, Base, and table auto-creation.

DATABASE STRATEGY:
  - Local dev:  SQLite (no server needed, file at backend/qpredictor.db)
  - Production: PostgreSQL (Render provides a DATABASE_URL env var)

The DATABASE_URL environment variable controls which DB is used:
  - Not set             → SQLite (local dev default)
  - Starts with postgres → PostgreSQL (Render / any cloud DB)

No code changes needed when deploying — just set DATABASE_URL on Render.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# ── Pick database URL ────────────────────────────────────────────────────────
_DATABASE_URL = os.getenv("DATABASE_URL")

if _DATABASE_URL:
    # Render (and some other hosts) still issue postgres:// URLs which
    # SQLAlchemy 2.x requires as postgresql://
    if _DATABASE_URL.startswith("postgres://"):
        _DATABASE_URL = _DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
    DATABASE_URL = _DATABASE_URL
    _CONNECT_ARGS = {}
else:
    # Local SQLite — stored next to the backend/ folder
    _DB_PATH = Path(__file__).resolve().parent.parent / "qpredictor.db"
    DATABASE_URL = f"sqlite:///{_DB_PATH}"
    _CONNECT_ARGS = {"check_same_thread": False}

# ── Engine ───────────────────────────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args=_CONNECT_ARGS,
    pool_pre_ping=True,   # reconnect if DB went away (important on free tier)
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables that don't exist yet.
    Called once at app startup via FastAPI lifespan.
    Safe to call repeatedly — CREATE TABLE IF NOT EXISTS semantics.
    """
    import app.models  # noqa: F401 — registers all models on Base.metadata
    Base.metadata.create_all(bind=engine)
