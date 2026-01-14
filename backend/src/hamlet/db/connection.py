"""Database connection and session management."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from hamlet.config import settings

# SQLite connection string
# Handle different DATABASE_URL formats:
# - "file:hamlet.db" -> "sqlite:///hamlet.db"
# - "sqlite:///path/to/db" -> used as-is
if settings.database_url.startswith("sqlite://"):
    DATABASE_URL = settings.database_url
else:
    # Legacy format with "file:" prefix
    DATABASE_URL = f"sqlite:///{settings.database_url.replace('file:', '')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.debug,
)


# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initialize database tables."""
    from hamlet.db.models import Base

    Base.metadata.create_all(bind=engine)
