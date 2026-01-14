"""Tests for event export API (FEED-8)."""

import csv
import io
import json
import time

import pytest
from fastapi.testclient import TestClient

from hamlet.db import Event
from hamlet.main import app


def create_test_events(db, count: int, base_timestamp: int | None = None) -> list[Event]:
    """Create test events for export testing."""
    if base_timestamp is None:
        base_timestamp = int(time.time())

    # Use valid location IDs from the seeded database
    locations = ["town_square", "bakery", "tavern", "church"]

    events = []
    for i in range(count):
        event = Event(
            timestamp=base_timestamp + i,
            type="dialogue" if i % 2 == 0 else "movement",
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
class TestEventExportJSON:
    """Test /api/events/export/json endpoint."""

    def test_export_json_basic(self, api_client, db):
        """Basic JSON export returns valid JSON array."""
        create_test_events(db, 5)

        response = api_client.get("/api/events/export/json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment" in response.headers.get("content-disposition", "")

        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5

    def test_export_json_structure(self, api_client, db):
        """JSON export has correct field structure."""
        create_test_events(db, 1)

        response = api_client.get("/api/events/export/json")
        assert response.status_code == 200

        data = response.json()
        event = data[0]

        assert "id" in event
        assert "timestamp" in event
        assert "type" in event
        assert "actors" in event
        assert "location_id" in event
        assert "summary" in event
        assert "detail" in event
        assert "significance" in event
        assert isinstance(event["actors"], list)

    def test_export_json_filter_by_type(self, api_client, db):
        """JSON export respects event_type filter."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/json?event_type=dialogue")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for event in data:
            assert event["type"] == "dialogue"

    def test_export_json_filter_by_location(self, api_client, db):
        """JSON export respects location_id filter."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/json?location_id=town_square")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for event in data:
            assert event["location_id"] == "town_square"

    def test_export_json_filter_by_actor(self, api_client, db):
        """JSON export respects actor_id filter."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/json?actor_id=agent_0")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for event in data:
            assert "agent_0" in event["actors"]

    def test_export_json_filter_by_significance(self, api_client, db):
        """JSON export respects min_significance filter."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/json?min_significance=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for event in data:
            assert event["significance"] >= 2

    def test_export_json_filter_by_timestamp_range(self, api_client, db):
        """JSON export respects timestamp range filters."""
        base_ts = 1000000
        create_test_events(db, 10, base_timestamp=base_ts)

        response = api_client.get(
            f"/api/events/export/json?timestamp_from={base_ts + 3}&timestamp_to={base_ts + 6}"
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data) > 0
        for event in data:
            assert base_ts + 3 <= event["timestamp"] <= base_ts + 6

    def test_export_json_with_limit(self, api_client, db):
        """JSON export respects limit parameter."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/export/json?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 5

    def test_export_json_empty_result(self, api_client, db):
        """JSON export returns empty array when no matches."""
        response = api_client.get("/api/events/export/json?event_type=nonexistent")
        assert response.status_code == 200

        data = response.json()
        assert data == []

    def test_export_json_ordered_by_timestamp(self, api_client, db):
        """JSON export events are ordered by timestamp descending."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/json")
        assert response.status_code == 200

        data = response.json()
        timestamps = [e["timestamp"] for e in data]
        assert timestamps == sorted(timestamps, reverse=True)


@pytest.mark.integration
class TestEventExportCSV:
    """Test /api/events/export/csv endpoint."""

    def test_export_csv_basic(self, api_client, db):
        """Basic CSV export returns valid CSV."""
        create_test_events(db, 5)

        response = api_client.get("/api/events/export/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers.get("content-disposition", "")

        # Parse CSV content
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Header + 5 data rows
        assert len(rows) == 6

    def test_export_csv_header(self, api_client, db):
        """CSV export has correct header."""
        create_test_events(db, 1)

        response = api_client.get("/api/events/export/csv")
        assert response.status_code == 200

        content = response.text
        reader = csv.reader(io.StringIO(content))
        header = next(reader)

        expected_header = [
            "id",
            "timestamp",
            "type",
            "actors",
            "location_id",
            "summary",
            "detail",
            "significance",
        ]
        assert header == expected_header

    def test_export_csv_data_format(self, api_client, db):
        """CSV export has correct data format."""
        create_test_events(db, 1)

        response = api_client.get("/api/events/export/csv")
        assert response.status_code == 200

        content = response.text
        reader = csv.reader(io.StringIO(content))
        next(reader)  # Skip header
        row = next(reader)

        # Check data types/format
        assert row[0].isdigit()  # id
        assert row[1].isdigit()  # timestamp
        assert row[2] in ["dialogue", "movement"]  # type
        # actors is comma-separated string
        assert row[4] in ["town_square", "bakery", "tavern", "church", ""]  # location_id
        assert row[7].isdigit()  # significance

    def test_export_csv_filter_by_type(self, api_client, db):
        """CSV export respects event_type filter."""
        create_test_events(db, 10)

        response = api_client.get("/api/events/export/csv?event_type=dialogue")
        assert response.status_code == 200

        content = response.text
        reader = csv.reader(io.StringIO(content))
        next(reader)  # Skip header
        rows = list(reader)

        assert len(rows) > 0
        for row in rows:
            assert row[2] == "dialogue"

    def test_export_csv_with_limit(self, api_client, db):
        """CSV export respects limit parameter."""
        create_test_events(db, 20)

        response = api_client.get("/api/events/export/csv?limit=5")
        assert response.status_code == 200

        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Header + 5 data rows
        assert len(rows) == 6

    def test_export_csv_empty_result(self, api_client, db):
        """CSV export returns only header when no matches."""
        response = api_client.get("/api/events/export/csv?event_type=nonexistent")
        assert response.status_code == 200

        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)

        # Only header row
        assert len(rows) == 1

    def test_export_csv_special_characters(self, api_client, db):
        """CSV export properly escapes special characters."""
        # Create event with special characters
        event = Event(
            timestamp=int(time.time()),
            type="dialogue",
            actors='["agent_0"]',
            location_id="town_square",
            summary='Test with "quotes" and, commas',
            detail="Detail with\nnewline",
            significance=1,
        )
        db.add(event)
        db.commit()
        db.refresh(event)

        response = api_client.get("/api/events/export/csv")
        assert response.status_code == 200

        # Parse should succeed even with special characters
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 2


@pytest.mark.integration
class TestExportValidation:
    """Test export parameter validation."""

    def test_invalid_format(self, api_client, db):
        """Invalid export format returns 422."""
        response = api_client.get("/api/events/export/xml")
        assert response.status_code == 422

    def test_limit_too_large(self, api_client, db):
        """Limit exceeding max returns 422."""
        response = api_client.get("/api/events/export/json?limit=10001")
        assert response.status_code == 422

    def test_limit_too_small(self, api_client, db):
        """Limit less than 1 returns 422."""
        response = api_client.get("/api/events/export/json?limit=0")
        assert response.status_code == 422

    def test_invalid_significance(self, api_client, db):
        """Invalid significance returns 422."""
        response = api_client.get("/api/events/export/json?min_significance=5")
        assert response.status_code == 422


@pytest.mark.integration
class TestExportPerformance:
    """Test export performance requirements from FEED-8."""

    def test_export_10k_under_5_seconds(self, api_client, db):
        """Export 10k events should complete in under 5 seconds.

        This is a key acceptance criterion from FEED-8:
        'Export 10k events in <5 seconds'
        """
        # Create 10,000 events
        create_test_events(db, 10000)

        start_time = time.time()
        response = api_client.get("/api/events/export/json")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 10000
        assert elapsed < 5.0, f"Export took {elapsed:.2f}s, expected < 5s"

    def test_export_csv_10k_under_5_seconds(self, api_client, db):
        """CSV export of 10k events should also complete in under 5 seconds."""
        # Reuse events from previous test (if module-scoped)
        # or create new ones
        existing = db.query(Event).count()
        if existing < 10000:
            create_test_events(db, 10000 - existing)

        start_time = time.time()
        response = api_client.get("/api/events/export/csv")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        content = response.text
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 10001  # header + 10k data
        assert elapsed < 5.0, f"Export took {elapsed:.2f}s, expected < 5s"
