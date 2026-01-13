"""Tests for SSE streaming endpoint."""

import json
import time

import pytest
from fastapi.testclient import TestClient

from hamlet.main import app
from hamlet.simulation.events import EventType, SimulationEvent, event_bus


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestStreamHistoryEndpoint:
    """Test stream history endpoint."""

    def test_stream_history_endpoint(self, client):
        """Stream history endpoint returns recent events."""
        response = client.get("/api/stream/history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_stream_history_limit(self, client):
        """Stream history respects limit parameter."""
        response = client.get("/api/stream/history?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_stream_history_limit_bounds(self, client):
        """Stream history validates limit bounds."""
        # Too small
        response = client.get("/api/stream/history?limit=0")
        assert response.status_code == 422  # Validation error

        # Too large
        response = client.get("/api/stream/history?limit=500")
        assert response.status_code == 422


class TestEventBusIntegration:
    """Test event bus integration with SSE."""

    @pytest.mark.asyncio
    async def test_event_bus_subscribe_unsubscribe(self):
        """Can subscribe and unsubscribe from event bus."""
        queue = event_bus.subscribe()
        assert queue in event_bus._subscribers

        event_bus.unsubscribe(queue)
        assert queue not in event_bus._subscribers

    @pytest.mark.asyncio
    async def test_event_bus_publish(self):
        """Published events are received by subscribers."""
        queue = event_bus.subscribe()

        try:
            # Publish an event
            event = SimulationEvent(
                type=EventType.MOVEMENT,
                summary="Test movement event",
                timestamp=int(time.time()),
                actors=["test_agent"],
                location_id="test_location",
            )
            await event_bus.publish(event)

            # Should receive it immediately
            received = queue.get_nowait()
            assert received.type == EventType.MOVEMENT
            assert received.summary == "Test movement event"
        finally:
            event_bus.unsubscribe(queue)

    @pytest.mark.asyncio
    async def test_event_bus_history(self):
        """Event bus maintains history of events."""
        initial_count = len(event_bus.get_history())

        # Publish a few events
        for i in range(5):
            event = SimulationEvent(
                type=EventType.DIALOGUE,
                summary=f"Test dialogue {i}",
                timestamp=int(time.time()),
            )
            await event_bus.publish(event)

        history = event_bus.get_history()
        assert len(history) >= initial_count + 5


class TestSSEFormat:
    """Test SSE response format."""

    def test_event_to_dict_format(self):
        """Events are properly formatted for SSE."""
        from hamlet.api.stream import event_to_dict

        event = SimulationEvent(
            type=EventType.ACTION,
            summary="Agnes examined the fountain",
            timestamp=1234567890,
            actors=["agnes"],
            location_id="town_square",
            detail="She noticed something shiny",
            significance=2,
            data={"action": "examine", "target": "fountain"},
        )

        result = event_to_dict(event)

        assert result["type"] == "action"
        assert result["summary"] == "Agnes examined the fountain"
        assert result["timestamp"] == 1234567890
        assert result["actors"] == ["agnes"]
        assert result["location_id"] == "town_square"
        assert result["detail"] == "She noticed something shiny"
        assert result["significance"] == 2
        assert result["data"]["action"] == "examine"

    def test_event_serializes_to_json(self):
        """Event dict can be serialized to JSON."""
        from hamlet.api.stream import event_to_dict

        event = SimulationEvent(
            type=EventType.DIALOGUE,
            summary="Test",
            timestamp=int(time.time()),
        )

        result = event_to_dict(event)
        # Should not raise
        json_str = json.dumps(result)
        assert "Test" in json_str


class TestStreamEndpoint:
    """Test SSE streaming endpoint configuration."""

    def test_stream_endpoint_registered(self, client):
        """Stream endpoint is registered in the app."""
        # Check that the route exists by looking at OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})
        assert "/api/stream" in paths
        assert "/api/stream/history" in paths

    def test_stream_endpoint_accepts_filters(self, client):
        """Stream endpoint documents filter parameters."""
        response = client.get("/openapi.json")
        schema = response.json()
        stream_path = schema["paths"]["/api/stream"]["get"]
        params = stream_path.get("parameters", [])
        param_names = [p["name"] for p in params]
        assert "types" in param_names
        assert "location" in param_names
        assert "agent" in param_names
