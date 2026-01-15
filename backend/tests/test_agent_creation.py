"""Tests for agent creation API endpoints (USER-7 through USER-10)."""

import pytest
import time
from fastapi.testclient import TestClient

from hamlet.main import app
from hamlet.schemas.agent import (
    TraitsSchema,
    TRAIT_PRESETS,
    generate_trait_summary,
    identify_archetype,
    get_preset_traits,
)


@pytest.fixture
def client(isolated_db_session):
    """Create test client with isolated database session."""
    return TestClient(app)


def create_test_user(client, username="testuser", email="test@example.com", password="password123"):
    """Create a test user via the API."""
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


def login_user(client, username="testuser", password="password123"):
    """Login a user via the API."""
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def get_auth_headers(client, username="testuser", password="password123"):
    """Get auth headers by logging in."""
    response = login_user(client, username, password)
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    return None


@pytest.mark.unit
class TestTraitValidation:
    """Test trait validation logic."""

    def test_valid_traits_default(self):
        """Default traits are valid."""
        traits = TraitsSchema()
        assert traits.curiosity == 5
        assert traits.empathy == 5

    def test_valid_traits_custom(self):
        """Custom valid traits pass validation."""
        traits = TraitsSchema(
            curiosity=7, empathy=8, ambition=6, discretion=5,
            energy=7, courage=4, charm=6, perception=5
        )
        assert traits.curiosity == 7
        assert traits.empathy == 8

    def test_invalid_trait_range_low(self):
        """Traits below 1 are invalid."""
        with pytest.raises(ValueError):
            TraitsSchema(curiosity=0)

    def test_invalid_trait_range_high(self):
        """Traits above 10 are invalid."""
        with pytest.raises(ValueError):
            TraitsSchema(curiosity=11)

    def test_invalid_all_extreme_low(self):
        """All traits at minimum is invalid."""
        with pytest.raises(ValueError) as exc_info:
            TraitsSchema(
                curiosity=1, empathy=1, ambition=1, discretion=1,
                energy=1, courage=1, charm=1, perception=1
            )
        assert "extreme values" in str(exc_info.value).lower()

    def test_invalid_all_extreme_high(self):
        """All traits at maximum is invalid."""
        with pytest.raises(ValueError) as exc_info:
            TraitsSchema(
                curiosity=10, empathy=10, ambition=10, discretion=10,
                energy=10, courage=10, charm=10, perception=10
            )
        assert "extreme values" in str(exc_info.value).lower()

    def test_invalid_high_ambition_low_energy(self):
        """Very high ambition with very low energy is invalid."""
        with pytest.raises(ValueError) as exc_info:
            TraitsSchema(ambition=9, energy=2)
        assert "ambition" in str(exc_info.value).lower() or "energy" in str(exc_info.value).lower()


@pytest.mark.unit
class TestTraitPresets:
    """Test trait preset functionality."""

    def test_all_presets_exist(self):
        """All expected presets are defined."""
        expected = ["scholar", "merchant", "guardian", "trickster", "hermit", "healer", "leader", "artisan"]
        for preset_id in expected:
            assert preset_id in TRAIT_PRESETS

    def test_presets_have_valid_traits(self):
        """All presets have valid trait values."""
        for preset_id, preset_data in TRAIT_PRESETS.items():
            traits = preset_data["traits"]
            # Create TraitsSchema to validate
            schema = TraitsSchema(**traits)
            # All values should be 1-10
            for key, value in traits.items():
                assert 1 <= value <= 10, f"Preset {preset_id} has invalid {key}={value}"

    def test_get_preset_traits(self):
        """Can get traits from preset name."""
        traits = get_preset_traits("scholar")
        assert traits is not None
        assert traits.curiosity == 9  # Scholar has high curiosity
        assert traits.perception == 8

    def test_get_invalid_preset(self):
        """Invalid preset returns None."""
        traits = get_preset_traits("nonexistent")
        assert traits is None

    def test_generate_trait_summary(self):
        """Trait summary generation works."""
        traits = TraitsSchema(curiosity=9, empathy=8, ambition=3)
        summary = generate_trait_summary(traits)
        assert "curious" in summary.lower()
        assert "empathetic" in summary.lower()
        assert "unambitious" in summary.lower()

    def test_identify_archetype(self):
        """Archetype identification works."""
        # Scholar traits
        scholar_traits = TraitsSchema(**TRAIT_PRESETS["scholar"]["traits"])
        archetype = identify_archetype(scholar_traits)
        assert archetype == "Scholar"

        # Unique traits should return "Unique"
        unique_traits = TraitsSchema(
            curiosity=5, empathy=5, ambition=5, discretion=5,
            energy=5, courage=5, charm=5, perception=5
        )
        archetype = identify_archetype(unique_traits)
        # May return "Unique" or a close match
        assert archetype in ["Unique", "Artisan"]  # Artisan is closest to balanced


@pytest.mark.integration
class TestPresetsEndpoint:
    """Test preset API endpoints."""

    def test_list_presets(self, client):
        """Can list all presets."""
        response = client.get("/api/agents/presets")
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert len(data["presets"]) == 8
        # Check structure
        preset = data["presets"][0]
        assert "id" in preset
        assert "name" in preset
        assert "description" in preset

    def test_get_preset_details(self, client):
        """Can get details for specific preset."""
        response = client.get("/api/agents/presets/scholar")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "scholar"
        assert data["name"] == "Scholar"
        assert "traits" in data
        assert data["traits"]["curiosity"] == 9

    def test_get_invalid_preset(self, client):
        """Getting invalid preset returns 404."""
        response = client.get("/api/agents/presets/nonexistent")
        assert response.status_code == 404


@pytest.mark.integration
class TestAgentQuota:
    """Test agent creation quota endpoint."""

    def test_quota_requires_auth(self, client):
        """Quota endpoint requires authentication."""
        response = client.get("/api/agents/quota")
        assert response.status_code == 401

    def test_get_quota_default(self, client):
        """New user gets default quota."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.get("/api/agents/quota", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["max_agents"] == 3
        assert data["agents_created"] == 0
        assert data["remaining"] == 3
        assert data["can_create"] is True


@pytest.mark.integration
class TestAgentPreview:
    """Test agent preview endpoint."""

    def test_preview_without_auth(self, client):
        """Preview works without authentication."""
        response = client.post(
            "/api/agents/preview",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others",
                "traits": {
                    "curiosity": 7, "empathy": 8, "ambition": 5, "discretion": 6,
                    "energy": 6, "courage": 5, "charm": 7, "perception": 6
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Agent"
        assert "trait_summary" in data
        assert "personality_archetype" in data
        assert "compatibility_notes" in data

    def test_preview_with_auth(self, client):
        """Preview works with authentication."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/preview",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others",
                "traits": {
                    "curiosity": 7, "empathy": 8, "ambition": 5, "discretion": 6,
                    "energy": 6, "courage": 5, "charm": 7, "perception": 6
                },
            },
            headers=headers,
        )
        assert response.status_code == 200

    def test_preview_with_location(self, client):
        """Preview includes location name."""
        response = client.post(
            "/api/agents/preview",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others",
                "traits": {},
                "location_id": "town_square",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "Town Square" in data["location_name"]


@pytest.mark.integration
class TestAgentCreation:
    """Test agent creation endpoint."""

    def test_create_requires_auth(self, client):
        """Create endpoint requires authentication."""
        response = client.post(
            "/api/agents/create",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others",
            },
        )
        assert response.status_code == 401

    def test_create_agent_success(self, client):
        """Can create agent with valid data."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "New Villager",
                "personality_prompt": "A curious newcomer to the village with a love of learning",
                "traits": {
                    "curiosity": 8, "empathy": 6, "ambition": 5, "discretion": 7,
                    "energy": 6, "courage": 5, "charm": 5, "perception": 7
                },
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Villager"
        assert data["is_user_created"] is True
        assert data["creator_id"] is not None
        assert "id" in data
        # ID should be generated from name
        assert "new_villager" in data["id"]

    def test_create_agent_with_preset(self, client):
        """Can create agent using preset."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "Scholar Jones",
                "personality_prompt": "A learned person who spends their days reading and researching",
                "preset": "scholar",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        # Should have scholar traits
        assert data["traits"]["curiosity"] == 9
        assert data["traits"]["perception"] == 8

    def test_create_agent_with_location(self, client):
        """Can specify starting location."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "Tavern Regular",
                "personality_prompt": "A sociable person who spends most of their time at the tavern",
                "location_id": "tavern",
            },
            headers=headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["location_id"] == "tavern"

    def test_create_invalid_name_short(self, client):
        """Cannot create agent with too short name."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "A",
                "personality_prompt": "A friendly villager who loves to help others",
            },
            headers=headers,
        )
        assert response.status_code == 422

    def test_create_invalid_personality_short(self, client):
        """Cannot create agent with too short personality prompt."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "Test Agent",
                "personality_prompt": "Short",
            },
            headers=headers,
        )
        assert response.status_code == 422

    def test_create_invalid_location(self, client):
        """Cannot create agent with invalid location."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others in the village",
                "location_id": "nonexistent_location",
            },
            headers=headers,
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_invalid_preset(self, client):
        """Cannot create agent with invalid preset."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/agents/create",
            json={
                "name": "Test Agent",
                "personality_prompt": "A friendly villager who loves to help others",
                "preset": "nonexistent_preset",
            },
            headers=headers,
        )
        assert response.status_code == 400
        assert "preset" in response.json()["detail"].lower()


@pytest.mark.integration
class TestAgentQuotaEnforcement:
    """Test quota and rate limiting enforcement."""

    def test_quota_updated_after_creation(self, client):
        """Quota is updated after agent creation."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Create agent
        client.post(
            "/api/agents/create",
            json={
                "name": "First Agent",
                "personality_prompt": "The first agent created by this user",
            },
            headers=headers,
        )

        # Check quota
        response = client.get("/api/agents/quota", headers=headers)
        data = response.json()
        assert data["agents_created"] == 1
        assert data["remaining"] == 2

    def test_my_agents_endpoint(self, client):
        """Can list agents created by current user."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Create an agent
        client.post(
            "/api/agents/create",
            json={
                "name": "My Agent",
                "personality_prompt": "An agent created by me for testing purposes",
            },
            headers=headers,
        )

        # List my agents
        response = client.get("/api/agents/my-agents", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "My Agent"


@pytest.mark.integration
class TestAgentDeletion:
    """Test agent deletion endpoint."""

    def test_delete_own_agent(self, client):
        """Can delete agent created by self."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Create agent
        create_response = client.post(
            "/api/agents/create",
            json={
                "name": "To Delete",
                "personality_prompt": "This agent will be deleted in this test",
            },
            headers=headers,
        )
        agent_id = create_response.json()["id"]

        # Delete agent
        response = client.delete(f"/api/agents/{agent_id}", headers=headers)
        assert response.status_code == 204

        # Verify quota restored
        quota_response = client.get("/api/agents/quota", headers=headers)
        assert quota_response.json()["agents_created"] == 0

    def test_cannot_delete_others_agent(self, client):
        """Cannot delete agent created by another user."""
        # Create first user and agent
        create_test_user(client, "user1", "user1@example.com")
        headers1 = get_auth_headers(client, "user1")
        create_response = client.post(
            "/api/agents/create",
            json={
                "name": "User One Agent",
                "personality_prompt": "An agent created by user one",
            },
            headers=headers1,
        )
        agent_id = create_response.json()["id"]

        # Create second user and try to delete
        create_test_user(client, "user2", "user2@example.com")
        headers2 = get_auth_headers(client, "user2")
        response = client.delete(f"/api/agents/{agent_id}", headers=headers2)
        assert response.status_code == 403

    def test_cannot_delete_system_agent(self, client):
        """Cannot delete system (seeded) agents."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Try to delete a seeded agent
        response = client.delete("/api/agents/agnes", headers=headers)
        assert response.status_code == 403
        assert "system" in response.json()["detail"].lower()


@pytest.mark.integration
class TestAgentIntegration:
    """Test that created agents integrate with existing system."""

    def test_created_agent_appears_in_list(self, client):
        """Created agent appears in agents list."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Create agent
        create_response = client.post(
            "/api/agents/create",
            json={
                "name": "Listed Agent",
                "personality_prompt": "This agent should appear in the agents list",
            },
            headers=headers,
        )
        agent_id = create_response.json()["id"]

        # Check agents list
        response = client.get("/api/agents")
        assert response.status_code == 200
        agent_ids = [a["id"] for a in response.json()]
        assert agent_id in agent_ids

    def test_created_agent_has_profile(self, client):
        """Created agent has accessible profile."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Create agent
        create_response = client.post(
            "/api/agents/create",
            json={
                "name": "Profile Agent",
                "personality_prompt": "This agent should have an accessible profile page",
            },
            headers=headers,
        )
        agent_id = create_response.json()["id"]

        # Get agent profile
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Profile Agent"
        assert data["state"] == "idle"  # Default state
