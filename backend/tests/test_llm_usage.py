"""Tests for LLM usage tracking and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from hamlet.db.seed import seed_database
from hamlet.llm.usage import (
    DEFAULT_PRICING,
    MODEL_PRICING,
    LLMUsageTracker,
    get_usage_tracker,
)
from hamlet.main import app


@pytest.fixture
def client():
    """Create test client."""
    seed_database()
    return TestClient(app)


@pytest.fixture
def tracker():
    """Create a fresh LLMUsageTracker for testing."""
    return LLMUsageTracker()


@pytest.mark.unit
class TestLLMUsageTracker:
    """Unit tests for LLMUsageTracker class."""

    def test_record_call_updates_totals(self, tracker):
        """Recording a call updates total statistics."""
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=100,
            tokens_out=50,
            latency_ms=150.0,
            cached=False,
        )

        stats = tracker.get_stats()
        assert stats.total_calls == 1
        assert stats.tokens_in == 100
        assert stats.tokens_out == 50
        assert stats.total_latency_ms == 150.0
        assert stats.cached_calls == 0

    def test_record_cached_call_no_cost(self, tracker):
        """Cached calls increment call count but not cost or tokens."""
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=100,
            tokens_out=50,
            latency_ms=10.0,
            cached=True,
        )

        stats = tracker.get_stats()
        assert stats.total_calls == 1
        assert stats.cached_calls == 1
        assert stats.tokens_in == 0  # Cached calls don't count tokens
        assert stats.tokens_out == 0
        assert stats.total_cost_usd == 0.0

    def test_calculate_cost_haiku_model(self, tracker):
        """Calculate cost for Haiku model uses correct pricing."""
        # Haiku: $0.25 input, $1.25 output per 1M tokens
        cost = tracker.calculate_cost(
            model="claude-3-haiku-20240307",
            tokens_in=1_000_000,
            tokens_out=1_000_000,
        )
        expected = 0.25 + 1.25  # $0.25 for input + $1.25 for output
        assert cost == pytest.approx(expected)

    def test_calculate_cost_sonnet_model(self, tracker):
        """Calculate cost for Sonnet model uses correct pricing."""
        # Sonnet: $3.00 input, $15.00 output per 1M tokens
        cost = tracker.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            tokens_in=1_000_000,
            tokens_out=1_000_000,
        )
        expected = 3.00 + 15.00  # $3.00 for input + $15.00 for output
        assert cost == pytest.approx(expected)

    def test_calculate_cost_unknown_model_uses_default(self, tracker):
        """Unknown model falls back to default pricing."""
        cost = tracker.calculate_cost(
            model="unknown-model-v1",
            tokens_in=1_000_000,
            tokens_out=1_000_000,
        )
        expected = DEFAULT_PRICING["input"] + DEFAULT_PRICING["output"]
        assert cost == pytest.approx(expected)

    def test_get_stats_returns_correct_totals(self, tracker):
        """get_stats returns accumulated totals across multiple calls."""
        # Record multiple calls
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=100,
            tokens_out=50,
            latency_ms=100.0,
            cached=False,
        )
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=200,
            tokens_out=100,
            latency_ms=150.0,
            cached=False,
        )
        tracker.record_call(
            model="claude-3-5-sonnet-20241022",
            tokens_in=50,
            tokens_out=25,
            latency_ms=200.0,
            cached=True,
        )

        stats = tracker.get_stats()
        assert stats.total_calls == 3
        assert stats.cached_calls == 1
        assert stats.tokens_in == 300  # 100 + 200 (cached not counted)
        assert stats.tokens_out == 150  # 50 + 100 (cached not counted)
        assert stats.total_latency_ms == 250.0  # 100 + 150 (cached not counted)

        # Check by_model tracking
        assert "claude-3-haiku-20240307" in stats.by_model
        assert stats.by_model["claude-3-haiku-20240307"]["calls"] == 2
        assert "claude-3-5-sonnet-20241022" in stats.by_model
        assert stats.by_model["claude-3-5-sonnet-20241022"]["calls"] == 1

    def test_get_recent_calls_limits_results(self, tracker):
        """get_recent_calls respects the limit parameter."""
        # Record 10 calls
        for i in range(10):
            tracker.record_call(
                model="claude-3-haiku-20240307",
                tokens_in=100 + i,
                tokens_out=50 + i,
                latency_ms=100.0,
                cached=False,
            )

        # Request only 5 recent calls
        recent = tracker.get_recent_calls(limit=5)
        assert len(recent) == 5

        # Verify we got the most recent ones (with highest token counts)
        assert recent[-1].tokens_in == 109  # Last recorded call
        assert recent[0].tokens_in == 105  # 5th from the end

    def test_reset_clears_stats(self, tracker):
        """reset() clears all statistics and recent calls."""
        # Record some calls
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=100,
            tokens_out=50,
            latency_ms=100.0,
            cached=False,
        )
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=200,
            tokens_out=100,
            latency_ms=150.0,
            cached=False,
        )

        # Verify we have data
        stats = tracker.get_stats()
        assert stats.total_calls == 2
        assert len(tracker.get_recent_calls()) == 2

        # Reset
        tracker.reset()

        # Verify everything is cleared
        stats = tracker.get_stats()
        assert stats.total_calls == 0
        assert stats.cached_calls == 0
        assert stats.tokens_in == 0
        assert stats.tokens_out == 0
        assert stats.total_cost_usd == 0.0
        assert stats.total_latency_ms == 0.0
        assert len(stats.by_model) == 0
        assert len(tracker.get_recent_calls()) == 0


@pytest.mark.unit
class TestCostCalculation:
    """Tests for cost calculation accuracy."""

    def test_haiku_pricing(self):
        """Verify Haiku pricing: $0.25/$1.25 per 1M tokens."""
        tracker = LLMUsageTracker()

        # Test with exactly 1M tokens
        cost = tracker.calculate_cost(
            model="claude-3-haiku-20240307",
            tokens_in=1_000_000,
            tokens_out=1_000_000,
        )
        assert cost == pytest.approx(0.25 + 1.25)

        # Test with smaller amounts
        cost = tracker.calculate_cost(
            model="claude-3-haiku-20240307",
            tokens_in=1000,
            tokens_out=500,
        )
        # 1000 tokens in = $0.00025, 500 tokens out = $0.000625
        expected = (1000 / 1_000_000) * 0.25 + (500 / 1_000_000) * 1.25
        assert cost == pytest.approx(expected)

    def test_sonnet_pricing(self):
        """Verify Sonnet pricing: $3.00/$15.00 per 1M tokens."""
        tracker = LLMUsageTracker()

        # Test with exactly 1M tokens
        cost = tracker.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            tokens_in=1_000_000,
            tokens_out=1_000_000,
        )
        assert cost == pytest.approx(3.00 + 15.00)

        # Test with smaller amounts
        cost = tracker.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            tokens_in=10000,
            tokens_out=5000,
        )
        # 10000 tokens in = $0.03, 5000 tokens out = $0.075
        expected = (10000 / 1_000_000) * 3.00 + (5000 / 1_000_000) * 15.00
        assert cost == pytest.approx(expected)

    def test_zero_tokens_zero_cost(self):
        """Zero tokens should result in zero cost."""
        tracker = LLMUsageTracker()

        cost = tracker.calculate_cost(
            model="claude-3-5-sonnet-20241022",
            tokens_in=0,
            tokens_out=0,
        )
        assert cost == 0.0

        # Also test with only input or output being zero
        cost_in_only = tracker.calculate_cost(
            model="claude-3-haiku-20240307",
            tokens_in=1000,
            tokens_out=0,
        )
        assert cost_in_only == pytest.approx((1000 / 1_000_000) * 0.25)

        cost_out_only = tracker.calculate_cost(
            model="claude-3-haiku-20240307",
            tokens_in=0,
            tokens_out=1000,
        )
        assert cost_out_only == pytest.approx((1000 / 1_000_000) * 1.25)


@pytest.mark.integration
class TestLLMAPIEndpoints:
    """Integration tests for LLM API endpoints."""

    def test_get_stats_returns_session_and_historical(self, client):
        """GET /api/llm/stats returns both session and historical data."""
        response = client.get("/api/llm/stats")
        assert response.status_code == 200

        data = response.json()

        # Verify session stats structure
        assert "session" in data
        session = data["session"]
        assert "total_calls" in session
        assert "cached_calls" in session
        assert "api_calls" in session
        assert "tokens_in" in session
        assert "tokens_out" in session
        assert "total_tokens" in session
        assert "total_cost_usd" in session
        assert "total_cost_display" in session
        assert "avg_latency_ms" in session
        assert "session_duration_seconds" in session
        assert "by_model" in session

        # Verify historical stats structure
        assert "historical" in data
        historical = data["historical"]
        assert "total_calls" in historical
        assert "api_calls" in historical
        assert "cached_calls" in historical
        assert "tokens_in" in historical
        assert "tokens_out" in historical
        assert "total_tokens" in historical
        assert "total_cost_usd" in historical
        assert "total_cost_display" in historical
        assert "by_model" in historical

        # Verify recent_calls is present
        assert "recent_calls" in data
        assert isinstance(data["recent_calls"], list)

    def test_get_cost_summary_format(self, client):
        """GET /api/llm/cost-summary returns correctly formatted cost data."""
        response = client.get("/api/llm/cost-summary")
        assert response.status_code == 200

        data = response.json()

        # Verify structure
        assert "session_cost" in data
        assert "historical_cost" in data
        assert "session_calls" in data
        assert "session_tokens" in data

        # Verify cost format (should be "$X.XXXX" string)
        assert data["session_cost"].startswith("$")
        assert data["historical_cost"].startswith("$")

        # Verify numeric fields are integers
        assert isinstance(data["session_calls"], int)
        assert isinstance(data["session_tokens"], int)

    def test_reset_clears_session_stats(self, client):
        """POST /api/llm/reset clears session statistics."""
        # First, record a call using the global tracker to ensure there's data
        tracker = get_usage_tracker()
        tracker.record_call(
            model="claude-3-haiku-20240307",
            tokens_in=100,
            tokens_out=50,
            latency_ms=100.0,
            cached=False,
        )

        # Reset via API
        response = client.post("/api/llm/reset")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "reset" in data["message"].lower() or "reset" in data.get("message", "").lower()

        # Verify session stats are cleared
        stats_response = client.get("/api/llm/stats")
        assert stats_response.status_code == 200

        session_stats = stats_response.json()["session"]
        assert session_stats["total_calls"] == 0
        assert session_stats["tokens_in"] == 0
        assert session_stats["tokens_out"] == 0
        assert session_stats["total_cost_usd"] == 0.0


@pytest.mark.unit
class TestModelPricing:
    """Tests for MODEL_PRICING configuration."""

    def test_all_models_have_input_and_output_pricing(self):
        """Every model in MODEL_PRICING has both input and output rates."""
        for model, pricing in MODEL_PRICING.items():
            assert "input" in pricing, f"Model {model} missing input pricing"
            assert "output" in pricing, f"Model {model} missing output pricing"
            assert pricing["input"] >= 0, f"Model {model} has negative input pricing"
            assert pricing["output"] >= 0, f"Model {model} has negative output pricing"

    def test_default_pricing_structure(self):
        """DEFAULT_PRICING has correct structure."""
        assert "input" in DEFAULT_PRICING
        assert "output" in DEFAULT_PRICING
        assert DEFAULT_PRICING["input"] >= 0
        assert DEFAULT_PRICING["output"] >= 0

    def test_expected_models_present(self):
        """Key Claude models are present in pricing."""
        expected_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022",
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
        ]
        for model in expected_models:
            assert model in MODEL_PRICING, f"Expected model {model} not in MODEL_PRICING"
