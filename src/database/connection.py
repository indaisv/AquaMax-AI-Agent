"""Database connection and session management."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config.settings import settings
from src.database.models import Base
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Ensure data directory exists
os.makedirs(os.path.dirname(settings.db_path) if settings.db_path.parent else ".", exist_ok=True)

engine = create_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseSession:
    """Injectable database session dependency (for FastAPI and manual use)."""

    def __init__(self) -> None:
        self._session = SessionLocal()

    def __enter__(self) -> Session:
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            self._session.rollback()
        else:
            self._session.commit()
        self._session.close()


def init_database() -> None:
    """Create all tables from ORM models."""
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")


def drop_database() -> None:
    """Drop all tables (use with caution)."""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("Database dropped.")
