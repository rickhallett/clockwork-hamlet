"""Verify API response schemas.

Phase 4 implementation: API contract tests to ensure response shapes
match expected schemas. These tests verify that the API returns data
in the correct format for frontend consumption.
"""

import pytest
from fastapi.testclient import TestClient

from hamlet.db.seed import seed_database
from hamlet.main import app


@pytest.fixture
def client():
    """Create test client."""
    seed_database()
    return TestClient(app)


@pytest.mark.unit
class TestAgentAPIContract:
    """Test agent API response shapes match schemas."""

    def test_agent_response_schema(self, client):
        """Agent endpoint returns valid schema."""
        response = client.get("/api/agents/agnes")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "id" in data
        assert "name" in data
        assert "traits" in data
        assert "mood" in data
        assert "location_id" in data

        # Types
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["traits"], dict)
        assert isinstance(data["mood"], dict)

    def test_agent_list_response_schema(self, client):
        """Agent list endpoint returns valid list of agents."""
        response = client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()

        assert isinstance(agents, list)
        assert len(agents) >= 1

        for agent in agents:
            assert "id" in agent
            assert "name" in agent
            assert isinstance(agent["id"], str)
            assert isinstance(agent["name"], str)

    def test_agent_memory_response_schema(self, client):
        """Agent memory endpoint returns valid schema."""
        response = client.get("/api/agents/agnes/memory")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "agent_id" in data
        assert "working" in data
        assert "recent" in data
        assert "longterm" in data
        assert "context" in data

        # Types - all memory fields should be lists
        assert isinstance(data["working"], list)
        assert isinstance(data["recent"], list)
        assert isinstance(data["longterm"], list)


@pytest.mark.unit
class TestEventAPIContract:
    """Test event API response shapes match schemas."""

    def test_event_list_response_schema(self, client):
        """Events endpoint returns valid list."""
        response = client.get("/api/events?limit=5")
        assert response.status_code == 200
        events = response.json()

        assert isinstance(events, list)
        for event in events:
            assert "type" in event
            assert "summary" in event
            assert "timestamp" in event
            assert isinstance(event["type"], str)
            assert isinstance(event["summary"], str)
            assert isinstance(event["timestamp"], int)

    def test_event_highlights_response_schema(self, client):
        """Event highlights endpoint returns valid list."""
        response = client.get("/api/events/highlights")
        assert response.status_code == 200
        highlights = response.json()

        assert isinstance(highlights, list)


@pytest.mark.unit
class TestLocationAPIContract:
    """Test location API response shapes match schemas."""

    def test_location_response_schema(self, client):
        """Location endpoint returns valid schema."""
        response = client.get("/api/locations/town_square")
        assert response.status_code == 200
        location = response.json()

        # Required fields
        assert "id" in location
        assert "name" in location
        assert "connections" in location
        assert "agents_present" in location

        # Types
        assert isinstance(location["id"], str)
        assert isinstance(location["name"], str)
        assert isinstance(location["connections"], list)
        assert isinstance(location["agents_present"], list)

    def test_location_list_response_schema(self, client):
        """Location list endpoint returns valid list."""
        response = client.get("/api/locations")
        assert response.status_code == 200
        locations = response.json()

        assert isinstance(locations, list)
        assert len(locations) >= 1

        for loc in locations:
            assert "id" in loc
            assert "name" in loc
            assert isinstance(loc["id"], str)
            assert isinstance(loc["name"], str)


@pytest.mark.unit
class TestWorldAPIContract:
    """Test world API response shapes match schemas."""

    def test_world_response_schema(self, client):
        """World endpoint returns valid schema."""
        response = client.get("/api/world")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "current_tick" in data
        assert "current_day" in data
        assert "current_hour" in data
        assert "season" in data
        assert "weather" in data

        # Types
        assert isinstance(data["current_tick"], int)
        assert isinstance(data["current_day"], int)
        assert isinstance(data["current_hour"], (int, float))
        assert isinstance(data["season"], str)
        assert isinstance(data["weather"], str)


@pytest.mark.unit
class TestRelationshipAPIContract:
    """Test relationship API response shapes match schemas."""

    def test_relationship_graph_response_schema(self, client):
        """Relationship graph endpoint returns valid schema."""
        response = client.get("/api/relationships")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "nodes" in data
        assert "edges" in data

        # Types
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

        # Node schema
        for node in data["nodes"]:
            assert "id" in node
            assert isinstance(node["id"], str)

        # Edge schema (if there are any)
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert isinstance(edge["source"], str)
            assert isinstance(edge["target"], str)

    def test_agent_relationships_response_schema(self, client):
        """Agent relationships endpoint returns valid list."""
        response = client.get("/api/relationships/agent/agnes")
        assert response.status_code == 200
        relationships = response.json()

        assert isinstance(relationships, list)
        for rel in relationships:
            # Relationship should have target and score at minimum
            assert "target_id" in rel or "agent_id" in rel


@pytest.mark.unit
class TestDigestAPIContract:
    """Test digest API response shapes match schemas."""

    def test_daily_digest_response_schema(self, client):
        """Daily digest endpoint returns valid schema."""
        response = client.get("/api/digest/daily")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "day" in data
        assert "headlines" in data
        assert "other_events" in data

        # Types
        assert isinstance(data["day"], int)
        assert isinstance(data["headlines"], list)
        assert isinstance(data["other_events"], list)

    def test_weekly_digest_response_schema(self, client):
        """Weekly digest endpoint returns valid schema."""
        response = client.get("/api/digest/weekly")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "week_ending_day" in data
        assert "top_stories" in data
        assert "events_by_type" in data

        # Types
        assert isinstance(data["week_ending_day"], int)
        assert isinstance(data["top_stories"], list)
        assert isinstance(data["events_by_type"], dict)


@pytest.mark.unit
class TestPollAPIContract:
    """Test poll API response shapes match schemas."""

    def test_polls_list_response_schema(self, client):
        """Polls list endpoint returns valid list."""
        response = client.get("/api/polls")
        assert response.status_code == 200
        polls = response.json()

        assert isinstance(polls, list)

    def test_active_poll_response_schema(self, client):
        """Active poll endpoint returns valid schema or null."""
        response = client.get("/api/polls/active")
        assert response.status_code == 200
        # May be null or a poll object


@pytest.mark.unit
class TestHealthAPIContract:
    """Test health API response shapes match schemas."""

    def test_health_response_schema(self, client):
        """Health endpoint returns valid schema."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] == "ok"
