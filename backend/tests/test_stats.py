"""Tests for stats API endpoints.

Tests for DASH-3 story (Stats API Endpoints) + DASH-15 (Simulation Health):
- DASH-9: /api/stats/agents
- DASH-10: /api/stats/events
- DASH-11: /api/stats/relationships
- DASH-12 + DASH-15: /api/stats/simulation (with health indicators)
"""

import time

import pytest
from fastapi.testclient import TestClient

from hamlet.db import Agent, Event, Relationship, WorldState
from hamlet.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


class TestAgentStats:
    """Tests for /api/stats/agents endpoint (DASH-9)."""

    def test_get_agent_stats_returns_correct_structure(self, client, db):
        """Test that agent stats endpoint returns expected fields."""
        response = client.get("/api/stats/agents")
        assert response.status_code == 200

        data = response.json()
        assert "total_count" in data
        assert "state_distribution" in data
        assert "mood_averages" in data
        assert "needs_averages" in data

    def test_agent_stats_count_matches_database(self, client, db):
        """Test that total_count matches actual agent count."""
        actual_count = db.query(Agent).count()
        response = client.get("/api/stats/agents")
        data = response.json()

        assert data["total_count"] == actual_count

    def test_agent_stats_state_distribution_sums_to_total(self, client, db):
        """Test that state distribution sums to total count."""
        response = client.get("/api/stats/agents")
        data = response.json()

        state_sum = (
            data["state_distribution"]["idle"]
            + data["state_distribution"]["busy"]
            + data["state_distribution"]["sleeping"]
        )
        assert state_sum == data["total_count"]


class TestEventStats:
    """Tests for /api/stats/events endpoint (DASH-10)."""

    def test_get_event_stats_returns_correct_structure(self, client, db):
        """Test that event stats endpoint returns expected fields."""
        response = client.get("/api/stats/events")
        assert response.status_code == 200

        data = response.json()
        assert "total_count" in data
        assert "by_type" in data
        assert "by_significance" in data
        assert "recent_count" in data

    def test_event_stats_by_type_is_list(self, client, db):
        """Test that by_type returns a list of type counts."""
        response = client.get("/api/stats/events")
        data = response.json()

        assert isinstance(data["by_type"], list)


class TestRelationshipStats:
    """Tests for /api/stats/relationships endpoint (DASH-11)."""

    def test_get_relationship_stats_returns_correct_structure(self, client, db):
        """Test that relationship stats endpoint returns expected fields."""
        response = client.get("/api/stats/relationships")
        assert response.status_code == 200

        data = response.json()
        assert "total_count" in data
        assert "by_type" in data
        assert "average_score" in data
        assert "positive_count" in data
        assert "negative_count" in data
        assert "neutral_count" in data
        assert "network_density" in data
        assert "average_connections_per_agent" in data

    def test_relationship_stats_sentiment_counts_sum_to_total(self, client, db):
        """Test that positive + negative + neutral = total."""
        response = client.get("/api/stats/relationships")
        data = response.json()

        sentiment_sum = (
            data["positive_count"] + data["negative_count"] + data["neutral_count"]
        )
        assert sentiment_sum == data["total_count"]


class TestSimulationStats:
    """Tests for /api/stats/simulation endpoint (DASH-12 + DASH-15)."""

    def test_get_simulation_stats_returns_correct_structure(self, client, db):
        """Test that simulation stats endpoint returns expected fields."""
        response = client.get("/api/stats/simulation")
        assert response.status_code == 200

        data = response.json()
        # Basic state (DASH-12)
        assert "current_tick" in data
        assert "current_day" in data
        assert "current_hour" in data
        assert "season" in data
        assert "weather" in data

        # Health indicators (DASH-15)
        assert "is_running" in data
        assert "queue_depth" in data
        assert "tick_rate" in data
        assert "events_per_tick" in data
        assert "uptime_ticks" in data
        assert "tick_interval_seconds" in data

    def test_simulation_stats_tick_is_non_negative(self, client, db):
        """Test that current_tick is non-negative."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["current_tick"] >= 0

    def test_simulation_stats_queue_depth_is_non_negative(self, client, db):
        """Test that queue_depth is non-negative (DASH-15)."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["queue_depth"] >= 0

    def test_simulation_stats_tick_rate_is_positive(self, client, db):
        """Test that tick_rate is positive (DASH-15)."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["tick_rate"] > 0


class TestStatsEndpointsIntegration:
    """Integration tests for all stats endpoints."""

    def test_all_stats_endpoints_accessible(self, client, db):
        """Test that all stats endpoints return 200 OK."""
        endpoints = [
            "/api/stats/agents",
            "/api/stats/events",
            "/api/stats/relationships",
            "/api/stats/simulation",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"Failed for {endpoint}"

    def test_stats_endpoints_return_json(self, client, db):
        """Test that all stats endpoints return valid JSON."""
        endpoints = [
            "/api/stats/agents",
            "/api/stats/events",
            "/api/stats/relationships",
            "/api/stats/simulation",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert isinstance(data, dict), f"Expected dict for {endpoint}"
