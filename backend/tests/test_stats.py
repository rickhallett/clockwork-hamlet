"""Tests for stats API endpoints.

Implements tests for DASH-3 story (Stats API Endpoints):
- DASH-9: /api/stats/agents
- DASH-10: /api/stats/events
- DASH-11: /api/stats/relationships
- DASH-12: /api/stats/simulation
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

        # Check nested structure
        assert "idle" in data["state_distribution"]
        assert "busy" in data["state_distribution"]
        assert "sleeping" in data["state_distribution"]

        assert "happiness" in data["mood_averages"]
        assert "energy" in data["mood_averages"]

        assert "hunger" in data["needs_averages"]
        assert "energy" in data["needs_averages"]
        assert "social" in data["needs_averages"]

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

    def test_agent_stats_with_modified_agent_state(self, client, db):
        """Test stats reflect agent state changes."""
        # Modify an agent to sleeping state
        agent = db.query(Agent).first()
        original_state = agent.state
        agent.state = "sleeping"
        db.flush()

        response = client.get("/api/stats/agents")
        data = response.json()

        assert data["state_distribution"]["sleeping"] >= 1

        # Restore original state
        agent.state = original_state

    def test_agent_stats_mood_averages_are_numeric(self, client, db):
        """Test that mood averages are numeric values."""
        response = client.get("/api/stats/agents")
        data = response.json()

        assert isinstance(data["mood_averages"]["happiness"], (int, float))
        assert isinstance(data["mood_averages"]["energy"], (int, float))

    def test_agent_stats_needs_averages_are_numeric(self, client, db):
        """Test that needs averages are numeric values."""
        response = client.get("/api/stats/agents")
        data = response.json()

        assert isinstance(data["needs_averages"]["hunger"], (int, float))
        assert isinstance(data["needs_averages"]["energy"], (int, float))
        assert isinstance(data["needs_averages"]["social"], (int, float))


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
        for item in data["by_type"]:
            assert "type" in item
            assert "count" in item

    def test_event_stats_by_significance_is_list(self, client, db):
        """Test that by_significance returns a list of level counts."""
        response = client.get("/api/stats/events")
        data = response.json()

        assert isinstance(data["by_significance"], list)
        for item in data["by_significance"]:
            assert "level" in item
            assert "count" in item
            assert 1 <= item["level"] <= 3

    def test_event_stats_with_new_event(self, client, db):
        """Test stats update when new event is added."""
        initial_response = client.get("/api/stats/events")
        initial_count = initial_response.json()["total_count"]

        # Add a new event
        event = Event(
            timestamp=int(time.time()),
            type="test_event",
            actors="[]",
            location_id=None,
            summary="Test event for stats",
            significance=2,
        )
        db.add(event)
        db.flush()

        response = client.get("/api/stats/events")
        data = response.json()

        assert data["total_count"] == initial_count + 1

    def test_event_stats_recent_count_reflects_timestamp(self, client, db):
        """Test that recent_count only includes recent events."""
        response = client.get("/api/stats/events")
        data = response.json()

        # recent_count should be non-negative
        assert data["recent_count"] >= 0
        assert isinstance(data["recent_count"], int)


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

    def test_relationship_stats_count_matches_database(self, client, db):
        """Test that total_count matches actual relationship count."""
        actual_count = db.query(Relationship).count()
        response = client.get("/api/stats/relationships")
        data = response.json()

        assert data["total_count"] == actual_count

    def test_relationship_stats_sentiment_counts_sum_to_total(self, client, db):
        """Test that positive + negative + neutral = total."""
        response = client.get("/api/stats/relationships")
        data = response.json()

        sentiment_sum = (
            data["positive_count"] + data["negative_count"] + data["neutral_count"]
        )
        assert sentiment_sum == data["total_count"]

    def test_relationship_stats_network_density_in_range(self, client, db):
        """Test that network density is between 0 and 1."""
        response = client.get("/api/stats/relationships")
        data = response.json()

        assert 0 <= data["network_density"] <= 1

    def test_relationship_stats_average_score_in_range(self, client, db):
        """Test that average score is between -10 and 10."""
        response = client.get("/api/stats/relationships")
        data = response.json()

        if data["total_count"] > 0:
            assert -10 <= data["average_score"] <= 10

    def test_relationship_stats_by_type_is_list(self, client, db):
        """Test that by_type returns a list of type counts."""
        response = client.get("/api/stats/relationships")
        data = response.json()

        assert isinstance(data["by_type"], list)
        for item in data["by_type"]:
            assert "type" in item
            assert "count" in item


class TestSimulationStats:
    """Tests for /api/stats/simulation endpoint (DASH-12)."""

    def test_get_simulation_stats_returns_correct_structure(self, client, db):
        """Test that simulation stats endpoint returns expected fields."""
        response = client.get("/api/stats/simulation")
        assert response.status_code == 200

        data = response.json()
        assert "current_tick" in data
        assert "current_day" in data
        assert "current_hour" in data
        assert "season" in data
        assert "weather" in data
        assert "is_running" in data
        assert "tick_interval_seconds" in data
        assert "events_per_tick" in data
        assert "uptime_ticks" in data

    def test_simulation_stats_tick_is_non_negative(self, client, db):
        """Test that current_tick is non-negative."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["current_tick"] >= 0

    def test_simulation_stats_day_is_positive(self, client, db):
        """Test that current_day is positive."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["current_day"] >= 1

    def test_simulation_stats_hour_in_range(self, client, db):
        """Test that current_hour is between 0 and 24."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert 0 <= data["current_hour"] < 24

    def test_simulation_stats_season_is_valid(self, client, db):
        """Test that season is a valid string."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        valid_seasons = ["spring", "summer", "autumn", "fall", "winter"]
        assert data["season"] in valid_seasons

    def test_simulation_stats_tick_interval_is_positive(self, client, db):
        """Test that tick_interval_seconds is positive."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["tick_interval_seconds"] > 0

    def test_simulation_stats_events_per_tick_non_negative(self, client, db):
        """Test that events_per_tick is non-negative."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["events_per_tick"] >= 0

    def test_simulation_stats_uptime_matches_tick(self, client, db):
        """Test that uptime_ticks equals current_tick."""
        response = client.get("/api/stats/simulation")
        data = response.json()

        assert data["uptime_ticks"] == data["current_tick"]

    def test_simulation_stats_reflects_world_state(self, client, db):
        """Test that stats reflect the actual world state."""
        world_state = db.query(WorldState).first()

        response = client.get("/api/stats/simulation")
        data = response.json()

        if world_state:
            assert data["current_tick"] == world_state.current_tick
            assert data["current_day"] == world_state.current_day
            assert data["season"] == world_state.season
            assert data["weather"] == world_state.weather


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
            # Should not raise an exception
            data = response.json()
            assert isinstance(data, dict), f"Expected dict for {endpoint}"

    def test_stats_consistency_agent_count(self, client, db):
        """Test that agent count is consistent across endpoints."""
        agent_stats = client.get("/api/stats/agents").json()
        rel_stats = client.get("/api/stats/relationships").json()

        agent_count = agent_stats["total_count"]

        # If there are agents, avg_connections calculation should work
        if agent_count > 0 and rel_stats["total_count"] > 0:
            expected_avg = rel_stats["total_count"] / agent_count
            assert abs(rel_stats["average_connections_per_agent"] - expected_avg) < 0.01
