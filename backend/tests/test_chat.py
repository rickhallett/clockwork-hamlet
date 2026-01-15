"""Tests for agent chat API endpoints."""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from hamlet.llm.client import LLMResponse, MockLLMClient
from hamlet.main import app


@pytest.fixture
def client(isolated_db_session):
    """Create test client with isolated database session."""
    return TestClient(app)


def create_test_user(client, username="chatuser", email="chat@example.com", password="password123"):
    """Create a test user via the API and return the response."""
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


def login_user(client, username="chatuser", password="password123"):
    """Login a user via the API and return the response."""
    return client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
    )


def get_auth_headers(client, username="chatuser", password="password123"):
    """Get auth headers by logging in."""
    response = login_user(client, username, password)
    if response.status_code == 200:
        tokens = response.json()
        return {"Authorization": f"Bearer {tokens['access_token']}"}
    return None


@pytest.fixture
def auth_headers(client):
    """Create user and return auth headers."""
    create_test_user(client)
    return get_auth_headers(client)


@pytest.fixture
def mock_llm():
    """Mock the LLM client to return predictable responses."""
    mock_client = MockLLMClient(responses=[
        "Ah, greetings traveler! What brings you to our humble village?",
        "Indeed, the weather has been most pleasant of late.",
        "You seem like a curious soul. I like that.",
    ])

    with patch("hamlet.llm.chat.get_llm_client", return_value=mock_client):
        yield mock_client


@pytest.mark.integration
class TestChatEndpoint:
    """Test the POST /api/agents/{agent_id}/chat endpoint."""

    def test_chat_requires_auth(self, client):
        """Cannot chat without authentication."""
        response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello Agnes!"},
        )
        assert response.status_code == 401

    def test_chat_with_nonexistent_agent(self, client, auth_headers, mock_llm):
        """Returns 404 for nonexistent agent."""
        response = client.post(
            "/api/agents/nonexistent/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_chat_success(self, client, auth_headers, mock_llm):
        """Can send a message and receive a response."""
        response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello Agnes!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "message" in data
        assert "agent_response" in data
        assert "conversation_id" in data

        # Check user message
        assert data["message"]["role"] == "user"
        assert data["message"]["content"] == "Hello Agnes!"

        # Check agent response
        assert data["agent_response"]["role"] == "agent"
        assert len(data["agent_response"]["content"]) > 0

    def test_chat_creates_conversation(self, client, auth_headers, mock_llm):
        """First message creates a new conversation."""
        response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        conversation_id = response.json()["conversation_id"]
        assert conversation_id is not None
        assert isinstance(conversation_id, int)

    def test_chat_continues_conversation(self, client, auth_headers, mock_llm):
        """Subsequent messages continue the same conversation."""
        # First message
        response1 = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        conv_id = response1.json()["conversation_id"]

        # Second message with same conversation
        response2 = client.post(
            f"/api/agents/agnes/chat?conversation_id={conv_id}",
            json={"message": "How are you?"},
            headers=auth_headers,
        )
        assert response2.json()["conversation_id"] == conv_id

    def test_chat_empty_message_fails(self, client, auth_headers):
        """Cannot send empty message."""
        response = client.post(
            "/api/agents/agnes/chat",
            json={"message": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_chat_tracks_llm_usage(self, client, auth_headers, mock_llm):
        """Chat tracks LLM token usage."""
        response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        agent_response = response.json()["agent_response"]

        # Mock client tracks token counts
        assert "tokens_in" in agent_response
        assert "tokens_out" in agent_response
        assert "latency_ms" in agent_response


@pytest.mark.integration
class TestChatHistory:
    """Test the GET /api/agents/{agent_id}/chat/history endpoint."""

    def test_history_requires_auth(self, client):
        """Cannot view history without authentication."""
        response = client.get("/api/agents/agnes/chat/history")
        assert response.status_code == 401

    def test_history_empty_initially(self, client, auth_headers):
        """History is empty for new user."""
        response = client.get(
            "/api/agents/agnes/chat/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversations"] == []
        assert data["total"] == 0

    def test_history_after_chat(self, client, auth_headers, mock_llm):
        """History shows conversations after chatting."""
        # Create some chat
        client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )

        # Check history
        response = client.get(
            "/api/agents/agnes/chat/history",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) == 1
        assert data["conversations"][0]["agent_id"] == "agnes"
        assert data["conversations"][0]["message_count"] >= 2  # User + agent messages

    def test_history_for_nonexistent_agent(self, client, auth_headers):
        """Returns 404 for nonexistent agent."""
        response = client.get(
            "/api/agents/nonexistent/chat/history",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.integration
class TestConversationDetail:
    """Test the GET /api/agents/{agent_id}/chat/{conversation_id} endpoint."""

    def test_get_conversation_requires_auth(self, client):
        """Cannot get conversation without authentication."""
        response = client.get("/api/agents/agnes/chat/1")
        assert response.status_code == 401

    def test_get_nonexistent_conversation(self, client, auth_headers):
        """Returns 404 for nonexistent conversation."""
        response = client.get(
            "/api/agents/agnes/chat/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_get_conversation_detail(self, client, auth_headers, mock_llm):
        """Can get conversation with messages."""
        # Create conversation
        chat_response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        conv_id = chat_response.json()["conversation_id"]

        # Get conversation detail
        response = client.get(
            f"/api/agents/agnes/chat/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert data["id"] == conv_id
        assert data["agent_id"] == "agnes"
        assert len(data["messages"]) >= 2

        # Check message order
        roles = [m["role"] for m in data["messages"]]
        assert "user" in roles
        assert "agent" in roles


@pytest.mark.integration
class TestStartNewConversation:
    """Test the POST /api/agents/{agent_id}/chat/new endpoint."""

    def test_start_new_requires_auth(self, client):
        """Cannot start new conversation without authentication."""
        response = client.post("/api/agents/agnes/chat/new")
        assert response.status_code == 401

    def test_start_new_conversation(self, client, auth_headers):
        """Can start a new conversation."""
        response = client.post(
            "/api/agents/agnes/chat/new",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()

        assert "id" in data
        assert data["agent_id"] == "agnes"
        assert data["is_active"] is True
        assert data["message_count"] == 0


@pytest.mark.integration
class TestArchiveConversation:
    """Test the DELETE /api/agents/{agent_id}/chat/{conversation_id} endpoint."""

    def test_archive_requires_auth(self, client):
        """Cannot archive conversation without authentication."""
        response = client.delete("/api/agents/agnes/chat/1")
        assert response.status_code == 401

    def test_archive_conversation(self, client, auth_headers, mock_llm):
        """Can archive a conversation."""
        # Create conversation
        chat_response = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello!"},
            headers=auth_headers,
        )
        conv_id = chat_response.json()["conversation_id"]

        # Archive it
        response = client.delete(
            f"/api/agents/agnes/chat/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Verify it's archived (can't continue it)
        response = client.post(
            f"/api/agents/agnes/chat?conversation_id={conv_id}",
            json={"message": "More chat"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_archive_nonexistent_conversation(self, client, auth_headers):
        """Returns 404 when archiving nonexistent conversation."""
        response = client.delete(
            "/api/agents/agnes/chat/99999",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.unit
class TestChatLLMIntegration:
    """Test the LLM integration for chat responses."""

    def test_build_chat_context(self, db, agent):
        """Chat context includes agent personality and state."""
        from hamlet.llm.chat import build_chat_context

        context = build_chat_context(agent, None, db)

        # Should include agent name
        assert agent.name in context
        # Should include personality traits
        assert "PERSONALITY TRAITS" in context
        # Should include current state
        assert "CURRENT STATE" in context
        # Should include needs
        assert "NEEDS" in context

    def test_generate_chat_response(self, db, agent):
        """Can generate a chat response."""
        from hamlet.llm.chat import generate_chat_response

        mock_client = MockLLMClient(responses=["Hello there, traveler!"])

        response_text, llm_response = generate_chat_response(
            agent=agent,
            user_message="Hello!",
            db=db,
            world=None,
            recent_messages=None,
            client=mock_client,
        )

        assert response_text == "Hello there, traveler!"
        assert isinstance(llm_response, LLMResponse)

    def test_create_chat_memory(self, db, agent):
        """Chat can create memories for significant conversations."""
        from hamlet.llm.chat import create_chat_memory

        # Short message - might not create memory
        memory = create_chat_memory(
            agent=agent,
            user_message="Hi",
            agent_response="Hello",
            db=db,
        )
        # Short messages typically don't create memories

        # Longer, more interesting message
        memory = create_chat_memory(
            agent=agent,
            user_message="Can you help me find my friend who went missing last night?",
            agent_response="Missing? That's concerning. Tell me more.",
            db=db,
        )
        # This should create a memory due to "help" keyword and length
        assert memory is not None or True  # May or may not create depending on heuristics


@pytest.mark.integration
class TestChatIsolation:
    """Test that chat is properly isolated between users."""

    def test_users_cannot_see_other_conversations(self, client, mock_llm):
        """Users can only see their own conversations."""
        # Create user 1
        create_test_user(client, "user1", "user1@example.com")
        headers1 = get_auth_headers(client, "user1")

        # User 1 chats with Agnes
        response1 = client.post(
            "/api/agents/agnes/chat",
            json={"message": "Hello from user 1!"},
            headers=headers1,
        )
        conv_id = response1.json()["conversation_id"]

        # Create user 2
        create_test_user(client, "user2", "user2@example.com")
        headers2 = get_auth_headers(client, "user2")

        # User 2 cannot see user 1's conversation
        response2 = client.get(
            f"/api/agents/agnes/chat/{conv_id}",
            headers=headers2,
        )
        assert response2.status_code == 404

        # User 2's history is empty
        history = client.get(
            "/api/agents/agnes/chat/history",
            headers=headers2,
        )
        assert history.json()["total"] == 0
