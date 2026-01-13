"""Tests for main application."""

from fastapi.testclient import TestClient

from hamlet.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to Clockwork Hamlet"


def test_health():
    """Test health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
