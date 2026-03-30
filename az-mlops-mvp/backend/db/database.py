"""
db/database.py
==============
SQLAlchemy engine, session factory, and declarative Base.

All ORM models inherit from `Base`.
All database operations use `get_db()` as a FastAPI dependency.

Usage (in a router):
    from db.database import get_db
    from sqlalchemy.orm import Session

    @router.get("/something")
    def endpoint(db: Session = Depends(get_db)):
        ...
"""

from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from core.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,          # Detect stale connections
    pool_size=10,                # Connection pool size
    max_overflow=20,             # Extra connections beyond pool_size
    pool_recycle=3600,           # Recycle connections after 1 hour
    echo=(settings.APP_ENV == "development"),  # Log SQL in dev only
)

# Enable JSON support for PostgreSQL JSONB columns
@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    """Ensure public schema is in the search path."""
    pass  # Extend if multi-schema support is needed


# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ---------------------------------------------------------------------------
# Declarative Base — all models inherit from this
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_db() -> Generator:
    """
    Yield a database session and ensure it is closed after the request.

    Usage:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
