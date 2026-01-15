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

    def test_create_poll(self, client):
        """Can create a new poll."""
        response = client.post(
            "/api/polls",
            json={
                "question": "What should Agnes do next?",
                "options": ["Go to market", "Visit the tavern", "Take a nap"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["question"] == "What should Agnes do next?"
        assert data["options"] == ["Go to market", "Visit the tavern", "Take a nap"]
        assert data["status"] == "active"
        assert data["allow_multiple"] is False
        assert data["votes"] == {}
        assert "id" in data
        assert "created_at" in data
        assert "opens_at" in data

    def test_create_multiple_choice_poll(self, client):
        """Can create a poll allowing multiple selections."""
        response = client.post(
            "/api/polls",
            json={
                "question": "Which activities interest you?",
                "options": ["Reading", "Walking", "Cooking", "Gardening"],
                "allow_multiple": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["allow_multiple"] is True

    def test_vote_multiple_on_multi_poll(self, client):
        """Can vote for multiple options on allow_multiple poll."""
        # Create a multi-choice poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Select all that apply",
                "options": ["Option A", "Option B", "Option C"],
                "allow_multiple": True,
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Vote for multiple options
        vote_resp = client.post(
            "/api/polls/vote-multiple",
            json={"poll_id": poll_id, "option_indices": [0, 2]},
        )
        assert vote_resp.status_code == 200
        data = vote_resp.json()
        assert data["success"] is True
        assert data["votes_cast"] == 2
        assert len(data["options"]) == 2

    def test_vote_multiple_on_single_poll_fails(self, client):
        """Cannot vote multiple on single-choice poll."""
        # Create a single-choice poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Single choice only",
                "options": ["Yes", "No"],
                "allow_multiple": False,
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Try to vote multiple - should fail
        vote_resp = client.post(
            "/api/polls/vote-multiple",
            json={"poll_id": poll_id, "option_indices": [0, 1]},
        )
        assert vote_resp.status_code == 400
        assert "does not allow multiple" in vote_resp.json()["detail"]

    def test_vote_multiple_no_duplicates(self, client):
        """Cannot vote for same option twice."""
        # Create a multi-choice poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "No duplicates",
                "options": ["A", "B", "C"],
                "allow_multiple": True,
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Try duplicate options
        vote_resp = client.post(
            "/api/polls/vote-multiple",
            json={"poll_id": poll_id, "option_indices": [0, 0]},
        )
        assert vote_resp.status_code == 400
        assert "Duplicate" in vote_resp.json()["detail"]

    def test_create_poll_with_closes_at(self, client):
        """Can create poll with closing time."""
        import time

        closes_at = int(time.time()) + 3600  # 1 hour from now
        response = client.post(
            "/api/polls",
            json={
                "question": "Best time for festival?",
                "options": ["Morning", "Afternoon"],
                "closes_at": closes_at,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["closes_at"] == closes_at

    def test_create_scheduled_poll(self, client):
        """Can create a scheduled poll with future opens_at."""
        import time

        opens_at = int(time.time()) + 3600  # 1 hour from now
        response = client.post(
            "/api/polls",
            json={
                "question": "What should happen tomorrow?",
                "options": ["Option A", "Option B"],
                "opens_at": opens_at,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["opens_at"] == opens_at

    def test_create_poll_too_few_options(self, client):
        """Poll creation fails with fewer than 2 options."""
        response = client.post(
            "/api/polls",
            json={
                "question": "Only one choice?",
                "options": ["Only option"],
            },
        )
        assert response.status_code == 400
        assert "at least 2 options" in response.json()["detail"]

    def test_create_poll_too_many_options(self, client):
        """Poll creation fails with more than 10 options."""
        response = client.post(
            "/api/polls",
            json={
                "question": "Too many choices?",
                "options": [f"Option {i}" for i in range(11)],
            },
        )
        assert response.status_code == 400
        assert "more than 10 options" in response.json()["detail"]

    def test_process_schedules_endpoint(self, client):
        """Can manually trigger schedule processing."""
        response = client.post("/api/polls/process-schedules")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "polls_opened" in data
        assert "polls_closed" in data

    def test_get_poll_by_id(self, client):
        """Can get a specific poll by ID."""
        # Create a poll first
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Test poll for get by ID",
                "options": ["Option A", "Option B"],
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Get the poll by ID
        response = client.get(f"/api/polls/{poll_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == poll_id
        assert data["question"] == "Test poll for get by ID"

    def test_get_poll_by_id_not_found(self, client):
        """Get poll returns 404 for non-existent ID."""
        response = client.get("/api/polls/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.integration
class TestAgentVotingEndpoints:
    """Test agent voting endpoints (POLL-9, POLL-10)."""

    def test_agent_vote_success(self, client):
        """Agent can vote on a poll based on personality traits."""
        # Create a poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Should we explore the mysterious cave?",
                "options": ["Yes, explore it", "No, too dangerous", "Send scouts first"],
                "category": "exploration",
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Have Agnes vote
        response = client.post(
            f"/api/polls/{poll_id}/agent-vote",
            json={"agent_id": "agnes"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["agent_id"] == "agnes"
        assert data["poll_id"] == poll_id
        assert 0 <= data["option_index"] <= 2
        assert data["option_text"] in [
            "Yes, explore it",
            "No, too dangerous",
            "Send scouts first",
        ]
        assert 0 <= data["confidence"] <= 1

    def test_agent_vote_invalid_agent(self, client):
        """Agent vote fails for non-existent agent."""
        # Create a poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Test poll",
                "options": ["A", "B"],
            },
        )
        poll_id = create_resp.json()["id"]

        response = client.post(
            f"/api/polls/{poll_id}/agent-vote",
            json={"agent_id": "nonexistent_agent"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_agent_vote_invalid_poll(self, client):
        """Agent vote fails for non-existent poll."""
        response = client.post(
            "/api/polls/99999/agent-vote",
            json={"agent_id": "agnes"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_agent_vote_inactive_poll(self, client):
        """Agent vote fails for inactive poll."""
        import time

        # Create a scheduled poll (not yet active)
        opens_at = int(time.time()) + 3600
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Future poll",
                "options": ["A", "B"],
                "opens_at": opens_at,
            },
        )
        poll_id = create_resp.json()["id"]

        response = client.post(
            f"/api/polls/{poll_id}/agent-vote",
            json={"agent_id": "agnes"},
        )
        assert response.status_code == 400
        assert "not active" in response.json()["detail"]

    def test_agent_vote_updates_poll_votes(self, client):
        """Agent vote increments the poll vote count."""
        # Create a poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Vote count test",
                "options": ["A", "B"],
            },
        )
        poll_id = create_resp.json()["id"]

        # Have Agnes vote
        vote_resp = client.post(
            f"/api/polls/{poll_id}/agent-vote",
            json={"agent_id": "agnes"},
        )
        assert vote_resp.status_code == 200
        voted_option = vote_resp.json()["option_index"]

        # Check poll votes updated
        poll_resp = client.get(f"/api/polls/{poll_id}")
        votes = poll_resp.json()["votes"]
        assert votes.get(str(voted_option), 0) >= 1

    def test_bulk_agent_voting_success(self, client):
        """All agents can vote on a poll at once."""
        # Create a poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "What should the village do?",
                "options": ["Build a well", "Plant more crops", "Hold a festival"],
                "category": "governance",
            },
        )
        assert create_resp.status_code == 201
        poll_id = create_resp.json()["id"]

        # Trigger bulk voting
        response = client.post(f"/api/polls/{poll_id}/agent-voting")
        assert response.status_code == 200
        data = response.json()

        assert data["poll_id"] == poll_id
        assert data["total_votes"] > 0
        assert len(data["votes"]) == data["total_votes"]
        assert "summary" in data

        # Verify each vote has required fields
        for vote in data["votes"]:
            assert "agent_id" in vote
            assert "poll_id" in vote
            assert "option_index" in vote
            assert "option_text" in vote
            assert "confidence" in vote

    def test_bulk_agent_voting_summary(self, client):
        """Bulk voting returns correct summary statistics."""
        # Create a poll
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Summary test poll",
                "options": ["Option A", "Option B"],
            },
        )
        poll_id = create_resp.json()["id"]

        response = client.post(f"/api/polls/{poll_id}/agent-voting")
        data = response.json()
        summary = data["summary"]

        assert "total_votes" in summary
        assert "option_counts" in summary
        assert "avg_confidence" in summary
        assert summary["total_votes"] == data["total_votes"]

    def test_bulk_agent_voting_invalid_poll(self, client):
        """Bulk voting fails for non-existent poll."""
        response = client.post("/api/polls/99999/agent-voting")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_bulk_agent_voting_inactive_poll(self, client):
        """Bulk voting fails for inactive poll."""
        import time

        # Create a scheduled poll
        opens_at = int(time.time()) + 3600
        create_resp = client.post(
            "/api/polls",
            json={
                "question": "Future poll",
                "options": ["A", "B"],
                "opens_at": opens_at,
            },
        )
        poll_id = create_resp.json()["id"]

        response = client.post(f"/api/polls/{poll_id}/agent-voting")
        assert response.status_code == 400
        assert "not active" in response.json()["detail"]


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
