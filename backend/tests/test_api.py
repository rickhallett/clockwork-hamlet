"""Tests for REST API endpoints."""

import pytest
from fastapi.testclient import TestClient

from hamlet.db.seed import seed_database
from hamlet.main import app


@pytest.fixture
def client():
    """Create test client."""
    # Ensure database is seeded
    seed_database()
    return TestClient(app)


@pytest.mark.unit
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health(self, client):
        """Health endpoint returns ok."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


@pytest.mark.integration
class TestWorldEndpoint:
    """Test world state endpoint."""

    def test_get_world(self, client):
        """Can get world state."""
        response = client.get("/api/world")
        assert response.status_code == 200
        data = response.json()
        assert "current_tick" in data
        assert "current_day" in data
        assert "current_hour" in data
        assert "season" in data
        assert "weather" in data


@pytest.mark.integration
class TestAgentsEndpoints:
    """Test agent endpoints."""

    def test_list_agents(self, client):
        """Can list all agents."""
        response = client.get("/api/agents")
        assert response.status_code == 200
        agents = response.json()
        assert len(agents) >= 3  # Seeded with at least 3 agents
        assert all("id" in a and "name" in a for a in agents)

    def test_get_agent(self, client):
        """Can get specific agent."""
        response = client.get("/api/agents/agnes")
        assert response.status_code == 200
        agent = response.json()
        assert agent["id"] == "agnes"
        assert "Agnes" in agent["name"]  # Name may include surname
        assert "traits" in agent
        assert "mood" in agent

    def test_get_agent_not_found(self, client):
        """Returns 404 for non-existent agent."""
        response = client.get("/api/agents/nonexistent")
        assert response.status_code == 404

    def test_get_agent_memory(self, client):
        """Can get agent memories."""
        response = client.get("/api/agents/agnes/memory")
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agnes"
        assert "working" in data
        assert "recent" in data
        assert "longterm" in data
        assert "context" in data


@pytest.mark.integration
class TestLocationsEndpoints:
    """Test location endpoints."""

    def test_list_locations(self, client):
        """Can list all locations."""
        response = client.get("/api/locations")
        assert response.status_code == 200
        locations = response.json()
        assert len(locations) >= 3  # Seeded with at least 3 locations
        assert all("id" in loc and "name" in loc for loc in locations)

    def test_get_location(self, client):
        """Can get specific location."""
        response = client.get("/api/locations/town_square")
        assert response.status_code == 200
        location = response.json()
        assert location["id"] == "town_square"
        assert "connections" in location
        assert "agents_present" in location

    def test_get_location_not_found(self, client):
        """Returns 404 for non-existent location."""
        response = client.get("/api/locations/nonexistent")
        assert response.status_code == 404


@pytest.mark.integration
class TestEventsEndpoints:
    """Test event endpoints."""

    def test_list_events(self, client):
        """Can list events."""
        response = client.get("/api/events")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_events_pagination(self, client):
        """Events support pagination."""
        response = client.get("/api/events?skip=0&limit=5")
        assert response.status_code == 200
        events = response.json()
        assert len(events) <= 5

    def test_get_highlights(self, client):
        """Can get highlighted events."""
        response = client.get("/api/events/highlights")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestRelationshipsEndpoints:
    """Test relationship endpoints."""

    def test_get_relationship_graph(self, client):
        """Can get full relationship graph."""
        response = client.get("/api/relationships")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
        # Should have nodes for seeded agents
        assert len(data["nodes"]) >= 3

    def test_get_agent_relationships(self, client):
        """Can get relationships for specific agent."""
        response = client.get("/api/relationships/agent/agnes")
        assert response.status_code == 200
        relationships = response.json()
        assert isinstance(relationships, list)


@pytest.mark.integration
class TestPollsEndpoints:
    """Test poll endpoints."""

    def test_get_active_poll_none(self, client):
        """Returns null when no active poll."""
        response = client.get("/api/polls/active")
        assert response.status_code == 200
        # May be null or a poll object

    def test_list_polls(self, client):
        """Can list all polls."""
        response = client.get("/api/polls")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_vote_invalid_poll(self, client):
        """Vote fails for non-existent poll."""
        response = client.post("/api/polls/vote", json={"poll_id": 99999, "option": 0})
        assert response.status_code == 404

    def test_list_polls_returns_category_and_tags_fields(self, client):
        """Poll response schema includes category and tags fields."""
        response = client.get("/api/polls")
        assert response.status_code == 200
        polls = response.json()
        # Schema should include category and tags fields (even if empty list)
        if polls:
            poll = polls[0]
            assert "category" in poll
            assert "tags" in poll
            assert isinstance(poll["tags"], list)

    def test_list_polls_accepts_category_filter(self, client):
        """List polls accepts category query parameter."""
        # Should not error with category parameter
        response = client.get("/api/polls?category=test")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


@pytest.mark.integration
class TestDigestEndpoints:
    """Test digest endpoints."""

    def test_get_daily_digest(self, client):
        """Can get daily digest."""
        response = client.get("/api/digest/daily")
        assert response.status_code == 200
        data = response.json()
        assert "day" in data
        assert "headlines" in data
        assert "other_events" in data

    def test_get_weekly_digest(self, client):
        """Can get weekly digest."""
        response = client.get("/api/digest/weekly")
        assert response.status_code == 200
        data = response.json()
        assert "week_ending_day" in data
        assert "top_stories" in data
        assert "events_by_type" in data
