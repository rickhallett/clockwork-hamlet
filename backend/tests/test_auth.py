"""Tests for authentication API endpoints."""

import pytest
from fastapi.testclient import TestClient

from hamlet.main import app


@pytest.fixture
def client(isolated_db_session):
    """Create test client with isolated database session.

    The isolated_db_session fixture from conftest.py patches SessionLocal
    and provides transaction rollback isolation between tests.
    """
    return TestClient(app)


def create_test_user(client, username="testuser", email="test@example.com", password="password123"):
    """Create a test user via the API and return the response."""
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )


def login_user(client, username="testuser", password="password123"):
    """Login a user via the API and return the response."""
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


@pytest.mark.integration
class TestRegistration:
    """Test user registration."""

    def test_register_success(self, client):
        """Can register a new user."""
        response = create_test_user(client, "newuser", "newuser@example.com")
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data  # Ensure password not leaked

    def test_register_duplicate_username(self, client):
        """Cannot register with existing username."""
        # First registration
        create_test_user(client, "dupuser", "first@example.com")

        # Second registration with same username
        response = create_test_user(client, "dupuser", "second@example.com")
        assert response.status_code == 400
        assert "Username already registered" in response.json()["detail"]

    def test_register_duplicate_email(self, client):
        """Cannot register with existing email."""
        # First registration
        create_test_user(client, "user1", "same@example.com")

        # Second registration with same email
        response = create_test_user(client, "user2", "same@example.com")
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Cannot register with invalid email."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "not-an-email",
                "password": "password123",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_register_short_password(self, client):
        """Cannot register with too short password."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "newuser@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_register_short_username(self, client):
        """Cannot register with too short username."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "ab",
                "email": "newuser@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 422


@pytest.mark.integration
class TestLogin:
    """Test user login."""

    def test_login_success(self, client):
        """Can login with valid credentials."""
        # Create user first
        create_test_user(client)

        # Login
        response = login_user(client)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        """Cannot login with wrong password."""
        create_test_user(client)
        response = login_user(client, password="wrongpassword")
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Cannot login with nonexistent user."""
        response = login_user(client, username="nonexistent")
        assert response.status_code == 401


@pytest.mark.integration
class TestTokenRefresh:
    """Test token refresh."""

    def test_refresh_success(self, client):
        """Can refresh tokens with valid refresh token."""
        # Create and login user
        create_test_user(client)
        login_response = login_user(client)
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        # Should get a new refresh token
        assert data["refresh_token"] != refresh_token

    def test_refresh_invalid_token(self, client):
        """Cannot refresh with invalid token."""
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
        assert response.status_code == 401

    def test_refresh_token_reuse_fails(self, client):
        """Cannot reuse a refresh token after it's been used."""
        # Create and login
        create_test_user(client)
        login_response = login_user(client)
        refresh_token = login_response.json()["refresh_token"]

        # First refresh - should succeed
        response1 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response1.status_code == 200

        # Second refresh with same token - should fail
        response2 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response2.status_code == 401
        assert "revoked" in response2.json()["detail"]


@pytest.mark.integration
class TestLogout:
    """Test logout functionality."""

    def test_logout_success(self, client):
        """Can logout and revoke refresh token."""
        # Create and login
        create_test_user(client)
        login_response = login_user(client)
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Logout
        response = client.post(
            "/api/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers=headers,
        )
        assert response.status_code == 200

        # Try to use refresh token - should fail
        refresh_response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh_response.status_code == 401

    def test_logout_all_sessions(self, client):
        """Can logout from all sessions."""
        # Create user
        create_test_user(client)

        # Login twice to create multiple sessions
        login1 = login_user(client)
        login2 = login_user(client)

        headers = {"Authorization": f"Bearer {login1.json()['access_token']}"}

        # Logout all
        response = client.post("/api/auth/logout-all", headers=headers)
        assert response.status_code == 200

        # Try to use both refresh tokens - should fail
        refresh1 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": login1.json()["refresh_token"]},
        )
        refresh2 = client.post(
            "/api/auth/refresh",
            json={"refresh_token": login2.json()["refresh_token"]},
        )
        assert refresh1.status_code == 401
        assert refresh2.status_code == 401


@pytest.mark.integration
class TestProtectedEndpoints:
    """Test protected endpoint access."""

    def test_get_current_user(self, client):
        """Can get current user profile with valid token."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_no_token(self, client):
        """Cannot get profile without token."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client):
        """Cannot get profile with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    def test_update_user_email(self, client):
        """Can update user email."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.patch(
            "/api/auth/me",
            json={"email": "newemail@example.com"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["email"] == "newemail@example.com"

    def test_change_password(self, client):
        """Can change password."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "password123",
                "new_password": "newpassword456",
            },
            headers=headers,
        )
        assert response.status_code == 200

        # Verify new password works
        login_response = login_user(client, password="newpassword456")
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client):
        """Cannot change password with wrong current password."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.post(
            "/api/auth/change-password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
            headers=headers,
        )
        assert response.status_code == 400


@pytest.mark.integration
class TestPreferences:
    """Test user preferences."""

    def test_get_default_preferences(self, client):
        """Get default preferences for new user."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.get("/api/auth/preferences", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "light"
        assert data["notifications_enabled"] is True

    def test_update_preferences(self, client):
        """Can update preferences."""
        create_test_user(client)
        headers = get_auth_headers(client)

        response = client.put(
            "/api/auth/preferences",
            json={
                "theme": "dark",
                "feed_filter_type": "dialogue",
                "notifications_enabled": False,
                "sound_enabled": True,
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["feed_filter_type"] == "dialogue"
        assert data["notifications_enabled"] is False
        assert data["sound_enabled"] is True

    def test_preferences_persist(self, client):
        """Preferences persist across requests."""
        create_test_user(client)
        headers = get_auth_headers(client)

        # Update
        client.put(
            "/api/auth/preferences",
            json={"theme": "dark"},
            headers=headers,
        )

        # Get
        response = client.get("/api/auth/preferences", headers=headers)
        assert response.json()["theme"] == "dark"


@pytest.mark.unit
class TestSecurityUtils:
    """Test security utility functions."""

    def test_password_hashing(self):
        """Password hashing works correctly."""
        from hamlet.auth.security import get_password_hash, verify_password

        password = "testpassword123"
        hashed = get_password_hash(password)

        # Should verify correctly
        assert verify_password(password, hashed)
        # Wrong password should fail
        assert not verify_password("wrongpassword", hashed)
        # Hash should be different each time (due to salt)
        hashed2 = get_password_hash(password)
        assert hashed != hashed2

    def test_token_creation_and_verification(self):
        """JWT token creation and verification works."""
        from hamlet.auth.security import create_access_token, verify_token

        token = create_access_token({"sub": "123"})
        payload = verify_token(token)

        assert payload is not None
        assert payload["sub"] == "123"
        assert payload["type"] == "access"

    def test_invalid_token_verification(self):
        """Invalid tokens fail verification."""
        from hamlet.auth.security import verify_token

        assert verify_token("invalid-token") is None
        assert verify_token("") is None


@pytest.mark.integration
class TestAPIContracts:
    """Test API response schemas match expected contracts."""

    def test_user_response_schema(self, client):
        """User registration returns valid schema."""
        response = create_test_user(client, "contractuser", "contract@example.com")
        assert response.status_code == 201
        data = response.json()

        # Required fields
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "is_active" in data
        assert "is_admin" in data
        assert "created_at" in data

        # Types
        assert isinstance(data["id"], int)
        assert isinstance(data["username"], str)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_active"], bool)
        assert isinstance(data["is_admin"], bool)
        assert isinstance(data["created_at"], (int, float))

        # Security - password must not be exposed
        assert "password" not in data
        assert "hashed_password" not in data

    def test_token_response_schema(self, client):
        """Login returns valid token schema."""
        create_test_user(client, "tokenuser", "token@example.com")
        response = login_user(client, "tokenuser")
        assert response.status_code == 200
        data = response.json()

        # Required fields
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data

        # Types
        assert isinstance(data["access_token"], str)
        assert isinstance(data["refresh_token"], str)
        assert data["token_type"] == "bearer"

        # Tokens should be non-empty
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20

    def test_preferences_response_schema(self, client):
        """Preferences endpoint returns valid schema."""
        create_test_user(client, "prefuser", "pref@example.com")
        headers = get_auth_headers(client, "prefuser")

        response = client.get("/api/auth/preferences", headers=headers)
        assert response.status_code == 200
        data = response.json()

        # Required fields with defaults
        assert "theme" in data
        assert "notifications_enabled" in data
        assert "sound_enabled" in data

        # Types
        assert isinstance(data["theme"], str)
        assert isinstance(data["notifications_enabled"], bool)
        assert isinstance(data["sound_enabled"], bool)

    def test_error_response_schema(self, client):
        """Error responses follow standard format."""
        # Try invalid login
        response = client.post(
            "/api/auth/login",
            data={"username": "nonexistent", "password": "wrong"},
        )
        assert response.status_code == 401
        data = response.json()

        # Standard error format
        assert "detail" in data
        assert isinstance(data["detail"], str)


@pytest.mark.slow
class TestAuthPerformance:
    """Performance tests for auth endpoints."""

    def test_login_under_500ms(self, client):
        """Login should complete in under 500ms."""
        import time

        create_test_user(client, "perfuser", "perf@example.com")

        start = time.time()
        response = login_user(client, "perfuser")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5, f"Login took {duration:.3f}s, expected < 0.5s"

    def test_token_refresh_under_200ms(self, client):
        """Token refresh should be fast."""
        import time

        create_test_user(client, "refreshperf", "refreshperf@example.com")
        login_response = login_user(client, "refreshperf")
        refresh_token = login_response.json()["refresh_token"]

        start = time.time()
        response = client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.2, f"Refresh took {duration:.3f}s, expected < 0.2s"

    def test_get_profile_under_100ms(self, client):
        """Getting user profile should be very fast."""
        import time

        create_test_user(client, "profileperf", "profileperf@example.com")
        headers = get_auth_headers(client, "profileperf")

        start = time.time()
        response = client.get("/api/auth/me", headers=headers)
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.1, f"Profile fetch took {duration:.3f}s, expected < 0.1s"

    def test_registration_under_500ms(self, client):
        """Registration should complete in under 500ms."""
        import time

        start = time.time()
        response = create_test_user(client, "regperf", "regperf@example.com")
        duration = time.time() - start

        assert response.status_code == 201
        assert duration < 0.5, f"Registration took {duration:.3f}s, expected < 0.5s"
