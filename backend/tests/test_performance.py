"""Performance regression tests (Phase 6.2).

These tests ensure API endpoints meet performance baselines
to detect regressions early. All tests are marked with @pytest.mark.slow
as they measure real execution times.

Performance baselines:
- Agent list: < 100ms
- Events query: < 200ms
"""

import time

import pytest
from fastapi.testclient import TestClient

from hamlet.db.seed import seed_database
from hamlet.main import app


@pytest.fixture
def client():
    """Create test client with seeded database."""
    seed_database()
    return TestClient(app)


@pytest.mark.slow
class TestPerformance:
    """Performance regression tests."""

    def test_agent_list_under_100ms(self, client):
        """Agent list endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/agents")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Agent list took {duration:.3f}s (expected < 0.1s)"

    def test_event_query_under_200ms(self, client):
        """Event query endpoint should respond in under 200ms."""
        start = time.time()
        response = client.get("/api/events?limit=100")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.2, f"Event query took {duration:.3f}s (expected < 0.2s)"

    def test_single_agent_under_50ms(self, client):
        """Single agent endpoint should respond in under 50ms."""
        start = time.time()
        response = client.get("/api/agents/agnes")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.05, f"Single agent took {duration:.3f}s (expected < 0.05s)"

    def test_health_under_10ms(self, client):
        """Health check endpoint should respond in under 10ms."""
        start = time.time()
        response = client.get("/api/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.01, f"Health check took {duration:.3f}s (expected < 0.01s)"

    def test_locations_under_100ms(self, client):
        """Locations endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/locations")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Locations took {duration:.3f}s (expected < 0.1s)"
