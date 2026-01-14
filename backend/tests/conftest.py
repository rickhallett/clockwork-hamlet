"""Pytest configuration with database isolation.

This module provides test fixtures for isolated database testing.
Each test module gets its own database file, and each test uses
transaction rollback for isolation within the module.

Phase 2 Implementation:
- 2.1: Module-scoped database isolation using tempfile
- 2.2: Transaction rollback pattern for per-test isolation

Phase 6 Implementation:
- 6.1: Test metrics tracking hook for monitoring test execution

This ensures:
1. Tests can run in any order without affecting each other
2. No state pollution between tests
3. Efficient database reuse within a module
4. Test metrics are tracked for performance monitoring
"""

import json
import os
import tempfile
import time
from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from hamlet.db.models import Base


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track test execution metrics (Phase 6.1).

    Records test name, duration, outcome, and timestamp to a JSONL file
    for monitoring test performance over time and detecting regressions.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        metrics = {
            "test": item.name,
            "module": item.module.__name__ if item.module else None,
            "duration": report.duration,
            "outcome": report.outcome,
            "timestamp": time.time(),
        }

        # Append to metrics file in the tests directory
        metrics_file = os.path.join(os.path.dirname(__file__), ".test-metrics.jsonl")
        try:
            with open(metrics_file, "a") as f:
                f.write(json.dumps(metrics) + "\n")
        except OSError:
            # Don't fail tests if metrics can't be written
            pass


@pytest.fixture(scope="module")
def test_db_path() -> Generator[str, None, None]:
    """Create a temporary database file per test module."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup after module completes
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture(scope="module")
def test_engine(test_db_path: str):
    """Create a SQLAlchemy engine for the test database (module-scoped)."""
    database_url = f"sqlite:///{test_db_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture(scope="module")
def TestSessionLocal(test_engine):
    """Create a sessionmaker bound to the test engine (module-scoped)."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="module")
def seeded_db(test_engine, TestSessionLocal) -> Generator[None, None, None]:
    """Seed the test database with initial data (module-scoped)."""
    from hamlet.db.seed import seed_agents, seed_locations, seed_relationships, seed_world_state

    session = TestSessionLocal()
    try:
        # Seed in order (respecting foreign keys)
        seed_locations(session)
        agents = seed_agents(session)
        seed_relationships(session, agents)
        seed_world_state(session)
        session.commit()
    finally:
        session.close()

    yield


@pytest.fixture(autouse=True)
def isolated_db_session(
    test_engine, TestSessionLocal, seeded_db, request
) -> Generator[Session, None, None]:
    """Provide an isolated database session for each test.

    This fixture uses the transaction rollback pattern:
    1. Begin a transaction before each test
    2. Execute the test within that transaction
    3. Rollback the transaction after the test

    Combined with module-scoped database, this ensures:
    - Fast test execution (reuse seeded database)
    - Complete isolation (rollback undoes all changes)
    - Tests can run in any order
    """
    # Create a connection and begin a transaction
    connection = test_engine.connect()
    transaction = connection.begin()

    # Create a session bound to this connection
    session = TestSessionLocal(bind=connection)

    # Create a session factory that returns our test session
    def test_session_factory(*args, **kwargs):
        return session

    # Create get_db that yields our session
    def mock_get_db():
        try:
            yield session
        finally:
            pass  # Don't close - we manage the session

    # Patch SessionLocal everywhere it's imported
    patchers = [
        patch("hamlet.db.connection.engine", test_engine),
        patch("hamlet.db.connection.SessionLocal", test_session_factory),
        patch("hamlet.db.SessionLocal", test_session_factory),
        patch("hamlet.db.engine", test_engine),
        patch("hamlet.db.connection.get_db", mock_get_db),
        patch("hamlet.db.get_db", mock_get_db),
        patch("hamlet.simulation.world.SessionLocal", test_session_factory),
        patch("hamlet.api.deps.SessionLocal", test_session_factory),
    ]

    # Start all patchers
    for p in patchers:
        p.start()

    try:
        yield session
    finally:
        # Stop all patchers
        for p in patchers:
            p.stop()

        # TRANSACTION ROLLBACK: Undo all changes made during the test
        try:
            session.close()
            transaction.rollback()
        except Exception:
            pass
        finally:
            connection.close()


@pytest.fixture
def db(isolated_db_session) -> Session:
    """Convenience fixture that provides the isolated database session.

    This fixture name matches what many tests expect.
    """
    return isolated_db_session


@pytest.fixture
def world(isolated_db_session) -> Generator:
    """Create a test World instance with isolated database.

    The World's internal session uses the test database via patched SessionLocal.
    Transaction rollback ensures any changes are undone after each test.
    """
    from hamlet.simulation.world import World

    w = World()
    # Force the world to use our session
    w._db = isolated_db_session
    yield w
    # Session rollback handled by isolated_db_session fixture


@pytest.fixture
def agent(world):
    """Get Agnes as the default test agent.

    Returns the agent as-is from the seeded database.
    Tests that need specific state should modify it themselves.
    """
    return world.get_agent("agnes")
