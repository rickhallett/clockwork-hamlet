"""Tests for cursor-based event pagination API (FEED-8)."""

import time
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from hamlet.db import Event
from hamlet.main import app


def create_test_events(db, count: int, base_timestamp: int | None = None) -> list[Event]:
    """Create test events for pagination testing."""
    if base_timestamp is None:
        base_timestamp = int(time.time())

    events = []
    for i in range(count):
        event = Event(
            timestamp=base_timestamp + i,
            type="dialogue" if i % 2 == 0 else "movement",
            actors=f'["agent_{i % 3}"]',
            location_id="town_square",
            summary=f"Test event {i}",
            detail=f"Detail for test event {i}",
            significance=(i % 3) + 1,  # 1, 2, 3, 1, 2, 3...
        )
        db.add(event)
        events.append(event)
    db.commit()

    # Refresh to get IDs
    for e in events:
        db.refresh(e)

    return events


@pytest.fixture
def api_client(db):
    """Create test client that uses isolated db session."""
    # The db fixture from conftest.py patches get_db, so TestClient will use it
    return TestClient(app)


@pytest.mark.integration
class TestEventHistoryEndpoint:
    """Test /api/events/history cursor-based pagination endpoint."""

    def test_basic_pagination(self, api_client, db):
        """Basic cursor-based pagination returns correct structure."""
        # Create some events
        create_test_events(db, 10)

        response = api_client.get("/api/events/history")
        assert response.status_code == 200

        data = response.json()
        assert "events" in data
        assert "next_cursor" in data
        assert "has_more" in data
        assert "total_count" in data
        assert isinstance(data["events"], list)

    def test_pagination_limit(self, api_client, db):
        """Limit parameter controls page size."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/history?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) == 5

    def test_pagination_has_more(self, api_client, db):
        """has_more is true when there are more events."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/history?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert data["has_more"] is True
        assert data["next_cursor"] is not None

    def test_pagination_no_more(self, api_client, db):
        """has_more is false when all events returned."""
        create_test_events(db, 5)

        response = api_client.get("/api/events/history?limit=50")
        assert response.status_code == 200

        data = response.json()
        # All 5 events should be returned
        assert len(data["events"]) == 5
        assert data["has_more"] is False

    def test_cursor_continues_from_last(self, api_client, db):
        """Cursor properly continues from last event."""
        create_test_events(db, 15)

        # Get first page
        response1 = api_client.get("/api/events/history?limit=5")
        assert response1.status_code == 200
        data1 = response1.json()
        first_page_ids = {e["id"] for e in data1["events"]}

        # Get second page using cursor
        cursor = data1["next_cursor"]
        response2 = api_client.get(f"/api/events/history?limit=5&cursor={cursor}")
        assert response2.status_code == 200
        data2 = response2.json()
        second_page_ids = {e["id"] for e in data2["events"]}

        # Pages should not overlap
        assert first_page_ids.isdisjoint(second_page_ids)

        # Second page should have smaller IDs (descending order)
        assert min(first_page_ids) > max(second_page_ids)

    def test_filter_by_event_type(self, api_client, db):
        """event_type filter works correctly."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history?event_type=dialogue")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) > 0
        for event in data["events"]:
            assert event["type"] == "dialogue"

    def test_filter_by_location(self, api_client, db):
        """location_id filter works correctly."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history?location_id=town_square")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) > 0
        for event in data["events"]:
            assert event["location_id"] == "town_square"

    def test_filter_by_actor(self, api_client, db):
        """actor_id filter works correctly."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history?actor_id=agent_0")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) > 0
        for event in data["events"]:
            assert "agent_0" in event["actors"]

    def test_filter_by_min_significance(self, api_client, db):
        """min_significance filter works correctly."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history?min_significance=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) > 0
        for event in data["events"]:
            assert event["significance"] >= 2

    def test_filter_by_timestamp_range(self, api_client, db):
        """Timestamp range filters work correctly."""
        base_ts = 1000000
        create_test_events(db, 10, base_timestamp=base_ts)

        # Get events in middle of range
        response = api_client.get(
            f"/api/events/history?timestamp_from={base_ts + 3}&timestamp_to={base_ts + 6}"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) > 0
        for event in data["events"]:
            assert base_ts + 3 <= event["timestamp"] <= base_ts + 6

    def test_include_count(self, api_client, db):
        """include_count returns total count."""
        create_test_events(db, 15)

        response = api_client.get("/api/events/history?include_count=true&limit=5")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] is not None
        assert data["total_count"] == 15

    def test_count_not_included_by_default(self, api_client, db):
        """total_count is null when include_count is false."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history")
        assert response.status_code == 200

        data = response.json()
        assert data["total_count"] is None

    def test_combined_filters(self, api_client, db):
        """Multiple filters work together."""
        base_ts = 2000000
        create_test_events(db, 20, base_timestamp=base_ts)

        response = api_client.get(
            f"/api/events/history?event_type=dialogue&min_significance=2"
            f"&timestamp_from={base_ts}&timestamp_to={base_ts + 15}"
        )
        assert response.status_code == 200

        data = response.json()
        for event in data["events"]:
            assert event["type"] == "dialogue"
            assert event["significance"] >= 2
            assert base_ts <= event["timestamp"] <= base_ts + 15

    def test_empty_result(self, api_client, db):
        """Empty results return proper structure."""
        response = api_client.get("/api/events/history?event_type=nonexistent_type")
        assert response.status_code == 200

        data = response.json()
        assert data["events"] == []
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    def test_limit_validation(self, api_client, db):
        """Limit parameter is validated."""
        # Too small
        response = api_client.get("/api/events/history?limit=0")
        assert response.status_code == 422

        # Too large
        response = api_client.get("/api/events/history?limit=101")
        assert response.status_code == 422

    def test_significance_validation(self, api_client, db):
        """min_significance is validated."""
        # Too small
        response = api_client.get("/api/events/history?min_significance=0")
        assert response.status_code == 422

        # Too large
        response = api_client.get("/api/events/history?min_significance=4")
        assert response.status_code == 422

    def test_events_ordered_descending(self, api_client, db):
        """Events are returned in descending ID order (newest first)."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/history?limit=10")
        assert response.status_code == 200

        data = response.json()
        events = data["events"]

        assert len(events) == 10
        # IDs should be in descending order
        for i in range(len(events) - 1):
            assert events[i]["id"] > events[i + 1]["id"]

    def test_full_pagination_walk(self, api_client, db):
        """Can walk through all events using cursor pagination."""
        create_test_events(db, 25)

        all_event_ids = set()
        cursor = None
        pages = 0
        max_pages = 10  # Safety limit

        while pages < max_pages:
            url = "/api/events/history?limit=5"
            if cursor:
                url += f"&cursor={cursor}"

            response = api_client.get(url)
            assert response.status_code == 200

            data = response.json()
            page_ids = {e["id"] for e in data["events"]}

            # No duplicates across pages
            assert all_event_ids.isdisjoint(page_ids)
            all_event_ids.update(page_ids)

            pages += 1

            if not data["has_more"]:
                break

            cursor = data["next_cursor"]

        # Should have fetched exactly 25 events in 5 pages
        assert len(all_event_ids) == 25
        assert pages == 5
