"""API dependencies."""

from collections.abc import Generator

from sqlalchemy.orm import Session

from hamlet.db.connection import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
