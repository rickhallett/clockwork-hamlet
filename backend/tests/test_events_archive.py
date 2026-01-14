"""Tests for event archival mode API (FEED-9)."""

import time

import pytest
from fastapi.testclient import TestClient

from hamlet.db import Event
from hamlet.main import app


def create_test_events(db, count: int, base_timestamp: int | None = None) -> list[Event]:
    """Create test events for archive testing."""
    if base_timestamp is None:
        base_timestamp = int(time.time())

    # Use valid location IDs from the seeded database
    locations = ["town_square", "bakery", "tavern", "church"]
    event_types = ["dialogue", "movement", "action", "discovery"]

    events = []
    for i in range(count):
        event = Event(
            timestamp=base_timestamp + (i * 3600),  # Each event 1 hour apart
            type=event_types[i % len(event_types)],
            actors=f'["agent_{i % 3}"]',
            location_id=locations[i % len(locations)],
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
    return TestClient(app)


@pytest.mark.integration
class TestArchiveStats:
    """Test /api/events/archive/stats endpoint."""

    def test_archive_stats_empty(self, api_client, db):
        """Archive stats returns correct structure when empty."""
        response = api_client.get("/api/events/archive/stats")
        assert response.status_code == 200

        data = response.json()
        assert "total_events" in data
        assert "oldest_timestamp" in data
        assert "newest_timestamp" in data
        assert "event_types" in data
        assert "date_range_days" in data

    def test_archive_stats_with_events(self, api_client, db):
        """Archive stats returns correct counts."""
        base_ts = 1000000
        create_test_events(db, 10, base_timestamp=base_ts)

        response = api_client.get("/api/events/archive/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_events"] == 10
        assert data["oldest_timestamp"] == base_ts
        assert data["newest_timestamp"] == base_ts + (9 * 3600)  # 9 hours later

    def test_archive_stats_event_types(self, api_client, db):
        """Archive stats returns correct event type breakdown."""
        create_test_events(db, 12)  # Creates 3 of each type

        response = api_client.get("/api/events/archive/stats")
        assert response.status_code == 200

        data = response.json()
        event_types = data["event_types"]

        # Should have 3 of each type (12 / 4 types)
        assert event_types.get("dialogue", 0) == 3
        assert event_types.get("movement", 0) == 3
        assert event_types.get("action", 0) == 3
        assert event_types.get("discovery", 0) == 3

    def test_archive_stats_date_range(self, api_client, db):
        """Archive stats calculates date range correctly."""
        base_ts = 1000000
        # Create events spanning 3 days (72 hours)
        events = []
        for i in range(4):
            event = Event(
                timestamp=base_ts + (i * 86400),  # Each day
                type="dialogue",
                actors='["agent_0"]',
                location_id="town_square",
                summary=f"Day {i} event",
                significance=1,
            )
            db.add(event)
            events.append(event)
        db.commit()

        response = api_client.get("/api/events/archive/stats")
        assert response.status_code == 200

        data = response.json()
        # 4 events spanning 3 full days (day 0, 1, 2, 3)
        assert data["date_range_days"] == 3


@pytest.mark.integration
class TestFeedModeInfo:
    """Test /api/events/feed-mode endpoint."""

    def test_feed_mode_live_default(self, api_client, db):
        """Feed mode defaults to live."""
        response = api_client.get("/api/events/feed-mode")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "live"
        assert data["live_connected"] is True
        assert data["archive_stats"] is None

    def test_feed_mode_live_explicit(self, api_client, db):
        """Feed mode can be explicitly set to live."""
        response = api_client.get("/api/events/feed-mode?mode=live")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "live"
        assert data["archive_stats"] is None

    def test_feed_mode_archive(self, api_client, db):
        """Feed mode archive includes stats."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/feed-mode?mode=archive")
        assert response.status_code == 200

        data = response.json()
        assert data["mode"] == "archive"
        assert data["archive_stats"] is not None
        assert data["archive_stats"]["total_events"] == 10

    def test_feed_mode_invalid(self, api_client, db):
        """Invalid feed mode returns 422."""
        response = api_client.get("/api/events/feed-mode?mode=invalid")
        assert response.status_code == 422


@pytest.mark.integration
class TestArchiveWithHistoryEndpoint:
    """Test that archive mode works with existing /history endpoint."""

    def test_history_endpoint_for_archive(self, api_client, db):
        """The existing /history endpoint serves archive mode queries."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/history?limit=10")
        assert response.status_code == 200

        data = response.json()
        assert len(data["events"]) == 10
        assert data["has_more"] is True

    def test_history_with_type_filter(self, api_client, db):
        """Archive mode filtering by event type."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/history?event_type=dialogue")
        assert response.status_code == 200

        data = response.json()
        for event in data["events"]:
            assert event["type"] == "dialogue"

    def test_history_with_timestamp_filter(self, api_client, db):
        """Archive mode filtering by timestamp range."""
        base_ts = 2000000
        create_test_events(db, 10, base_timestamp=base_ts)

        # Get events from hours 2-5
        response = api_client.get(
            f"/api/events/history?timestamp_from={base_ts + 7200}&timestamp_to={base_ts + 18000}"
        )
        assert response.status_code == 200

        data = response.json()
        for event in data["events"]:
            assert base_ts + 7200 <= event["timestamp"] <= base_ts + 18000

    def test_history_pagination_for_archive(self, api_client, db):
        """Archive mode pagination works correctly."""
        create_test_events(db, 50)

        # First page
        response1 = api_client.get("/api/events/history?limit=20")
        assert response1.status_code == 200
        data1 = response1.json()

        assert len(data1["events"]) == 20
        assert data1["has_more"] is True
        assert data1["next_cursor"] is not None

        # Second page
        cursor = data1["next_cursor"]
        response2 = api_client.get(f"/api/events/history?limit=20&cursor={cursor}")
        assert response2.status_code == 200
        data2 = response2.json()

        assert len(data2["events"]) == 20
        assert data2["has_more"] is True

        # Ensure no overlap
        page1_ids = {e["id"] for e in data1["events"]}
        page2_ids = {e["id"] for e in data2["events"]}
        assert page1_ids.isdisjoint(page2_ids)


@pytest.mark.integration
class TestArchiveVsLiveWorkflow:
    """Test the complete archive vs live mode workflow for FEED-9."""

    def test_workflow_check_mode_then_fetch(self, api_client, db):
        """Typical workflow: check mode info then fetch appropriate data."""
        create_test_events(db, 30)

        # Step 1: Check archive stats
        stats_response = api_client.get("/api/events/archive/stats")
        assert stats_response.status_code == 200
        stats = stats_response.json()
        total = stats["total_events"]

        # Step 2: Get feed mode info for archive
        mode_response = api_client.get("/api/events/feed-mode?mode=archive")
        assert mode_response.status_code == 200
        mode_info = mode_response.json()
        assert mode_info["archive_stats"]["total_events"] == total

        # Step 3: Fetch archived events
        history_response = api_client.get("/api/events/history?limit=50")
        assert history_response.status_code == 200
        history = history_response.json()
        assert len(history["events"]) == total

    def test_mode_switch_preserves_data(self, api_client, db):
        """Switching modes doesn't affect data availability."""
        create_test_events(db, 10)

        # Check archive mode
        archive_response = api_client.get("/api/events/feed-mode?mode=archive")
        assert archive_response.status_code == 200
        archive_count = archive_response.json()["archive_stats"]["total_events"]

        # Switch to live mode
        live_response = api_client.get("/api/events/feed-mode?mode=live")
        assert live_response.status_code == 200
        assert live_response.json()["mode"] == "live"

        # Switch back to archive
        archive_response2 = api_client.get("/api/events/feed-mode?mode=archive")
        assert archive_response2.status_code == 200
        assert archive_response2.json()["archive_stats"]["total_events"] == archive_count
