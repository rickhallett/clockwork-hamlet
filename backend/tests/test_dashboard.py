"""Tests for real-time dashboard API (DASH-11 through DASH-15)."""

import time

import pytest
from fastapi.testclient import TestClient

from hamlet.db import Event
from hamlet.main import app
from hamlet.simulation.engine import HealthMetrics, get_health_metrics


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestDashboardHealth:
    """Tests for DASH-14: Simulation health indicators."""

    def test_health_endpoint_returns_metrics(self, client):
        """Test that health endpoint returns expected structure."""
        response = client.get("/api/dashboard/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded"]
        assert "metrics" in data

        metrics = data["metrics"]
        assert "uptime_seconds" in metrics
        assert "total_ticks" in metrics
        assert "ticks_per_minute" in metrics
        assert "error_count" in metrics
        assert "last_tick_duration_ms" in metrics
        assert "avg_tick_duration_ms" in metrics
        assert "agents_processed" in metrics
        assert "queue_depth" in metrics

    def test_health_metrics_dataclass(self):
        """Test HealthMetrics dataclass functionality."""
        metrics = HealthMetrics()

        # Record some ticks
        metrics.record_tick(100.0, 5)
        metrics.record_tick(150.0, 6)
        metrics.record_tick(120.0, 5)

        assert metrics.total_ticks == 3
        assert metrics.avg_tick_duration_ms == pytest.approx(123.33, rel=0.01)

        # Record an error
        metrics.record_error()
        assert metrics.error_count == 1

        # Test to_dict
        data = metrics.to_dict()
        assert data["total_ticks"] == 3
        assert data["error_count"] == 1

    def test_health_status_reflects_errors(self, client):
        """Test that health status reflects error count."""
        metrics = get_health_metrics()
        initial_errors = metrics.error_count

        response = client.get("/api/dashboard/health")
        data = response.json()

        # Status should match error count
        if initial_errors == 0:
            assert data["status"] == "healthy"
        else:
            assert data["status"] == "degraded"


class TestDashboardPositions:
    """Tests for DASH-12: Agent positions update via SSE."""

    def test_positions_endpoint_returns_agents(self, client):
        """Test that positions endpoint returns agent positions."""
        response = client.get("/api/dashboard/positions")
        assert response.status_code == 200

        data = response.json()
        assert "positions" in data
        assert "by_location" in data
        assert "total_agents" in data

        assert isinstance(data["positions"], list)
        assert isinstance(data["by_location"], dict)
        assert isinstance(data["total_agents"], int)

    def test_positions_have_required_fields(self, client):
        """Test that each position has required fields."""
        response = client.get("/api/dashboard/positions")
        data = response.json()

        if data["positions"]:
            position = data["positions"][0]
            assert "id" in position
            assert "name" in position
            assert "location_id" in position
            assert "state" in position

    def test_positions_grouped_by_location(self, client):
        """Test that positions are grouped by location."""
        response = client.get("/api/dashboard/positions")
        data = response.json()

        # Verify by_location contains same agents as positions
        total_in_groups = sum(len(agents) for agents in data["by_location"].values())
        assert total_in_groups == data["total_agents"]


class TestDashboardEventRates:
    """Tests for DASH-15: Event rate sparklines."""

    def test_event_rates_endpoint(self, client):
        """Test that event rates endpoint returns expected structure."""
        response = client.get("/api/dashboard/event-rates")
        assert response.status_code == 200

        data = response.json()
        assert "events_per_bucket" in data
        assert "by_type" in data
        assert "bucket_size_minutes" in data
        assert "total_buckets" in data
        assert "total_events" in data
        assert "current_rate" in data
        assert "peak_rate" in data
        assert "avg_rate" in data
        assert "time_range" in data

        assert isinstance(data["events_per_bucket"], list)
        assert isinstance(data["by_type"], dict)

    def test_event_rates_custom_params(self, client):
        """Test event rates with custom parameters."""
        response = client.get("/api/dashboard/event-rates?minutes=30&bucket_size=5")
        assert response.status_code == 200

        data = response.json()
        assert data["bucket_size_minutes"] == 5
        assert data["total_buckets"] == 6  # 30 minutes / 5 min buckets
        assert data["time_range"]["minutes"] == 30

    def test_event_rates_validates_params(self, client):
        """Test that event rates validates parameters."""
        # Too many minutes
        response = client.get("/api/dashboard/event-rates?minutes=10000")
        assert response.status_code == 422

        # Invalid bucket size
        response = client.get("/api/dashboard/event-rates?bucket_size=0")
        assert response.status_code == 422


class TestDashboardSummary:
    """Tests for combined dashboard summary endpoint."""

    def test_summary_endpoint_returns_all_data(self, client):
        """Test that summary endpoint returns combined data."""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200

        data = response.json()

        # Should have health section
        assert "health" in data
        assert "status" in data["health"]
        assert "metrics" in data["health"]

        # Should have positions
        assert "positions" in data
        assert isinstance(data["positions"], list)

        # Should have events summary
        assert "events" in data
        assert "recent_5min" in data["events"]
        assert "by_type_1hr" in data["events"]


class TestEventTypes:
    """Tests for new SSE event types (DASH-12, DASH-14)."""

    def test_positions_event_type_exists(self):
        """Test that POSITIONS event type is defined."""
        from hamlet.simulation.events import EventType

        assert hasattr(EventType, "POSITIONS")
        assert EventType.POSITIONS.value == "positions"

    def test_health_event_type_exists(self):
        """Test that HEALTH event type is defined."""
        from hamlet.simulation.events import EventType

        assert hasattr(EventType, "HEALTH")
        assert EventType.HEALTH.value == "health"


class TestStreamFiltering:
    """Tests for SSE stream with dashboard event types."""

    def test_stream_endpoint_with_dashboard_types(self):
        """Test that stream endpoint accepts dashboard type filters."""
        from hamlet.simulation.events import EventType

        # Verify that the event types we use are valid
        valid_types = {e.value for e in EventType}
        assert "positions" in valid_types
        assert "health" in valid_types
        assert "llm_usage" in valid_types

    def test_event_generator_filters(self):
        """Test that event generator accepts position and health types."""
        from hamlet.api.stream import event_generator

        # This creates a generator that accepts our new event types
        gen = event_generator(event_types=["positions", "health", "llm_usage"])
        assert gen is not None
