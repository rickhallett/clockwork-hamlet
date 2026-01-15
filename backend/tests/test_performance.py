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


@pytest.mark.slow
class TestStatsPerformance:
    """Performance tests for stats endpoints (DASH-3)."""

    def test_stats_agents_under_100ms(self, client):
        """Stats agents endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/stats/agents")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Stats agents took {duration:.3f}s (expected < 0.1s)"

    def test_stats_events_under_100ms(self, client):
        """Stats events endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/stats/events")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Stats events took {duration:.3f}s (expected < 0.1s)"

    def test_stats_relationships_under_100ms(self, client):
        """Stats relationships endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/stats/relationships")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Stats relationships took {duration:.3f}s (expected < 0.1s)"

    def test_stats_simulation_under_50ms(self, client):
        """Stats simulation endpoint should respond in under 50ms."""
        start = time.time()
        response = client.get("/api/stats/simulation")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.05, f"Stats simulation took {duration:.3f}s (expected < 0.05s)"


@pytest.mark.slow
class TestDashboardPerformance:
    """Performance tests for dashboard endpoints (DASH-11 through DASH-15)."""

    def test_dashboard_health_under_20ms(self, client):
        """Dashboard health endpoint should respond in under 20ms."""
        start = time.time()
        response = client.get("/api/dashboard/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.02, f"Dashboard health took {duration:.3f}s (expected < 0.02s)"

    def test_dashboard_positions_under_100ms(self, client):
        """Dashboard positions endpoint should respond in under 100ms."""
        start = time.time()
        response = client.get("/api/dashboard/positions")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Dashboard positions took {duration:.3f}s (expected < 0.1s)"

    def test_dashboard_event_rates_under_200ms(self, client):
        """Dashboard event rates endpoint should respond in under 200ms."""
        start = time.time()
        response = client.get("/api/dashboard/event-rates")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.2, f"Dashboard event-rates took {duration:.3f}s (expected < 0.2s)"

    def test_dashboard_event_rates_large_window_under_500ms(self, client):
        """Dashboard event rates with large window should respond in under 500ms."""
        start = time.time()
        response = client.get("/api/dashboard/event-rates?minutes=1440&bucket_size=60")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5, f"Dashboard event-rates (24h) took {duration:.3f}s (expected < 0.5s)"

    def test_dashboard_summary_under_150ms(self, client):
        """Dashboard summary endpoint should respond in under 150ms."""
        start = time.time()
        response = client.get("/api/dashboard/summary")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.15, f"Dashboard summary took {duration:.3f}s (expected < 0.15s)"
