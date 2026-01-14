"""LLM usage tracking and cost calculation."""

import asyncio
import threading
import time
from dataclasses import dataclass, field

# Anthropic pricing per 1M tokens (as of 2024)
# https://www.anthropic.com/pricing
MODEL_PRICING = {
    # Claude 3.5 family
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00},
    "claude-3-5-sonnet-20240620": {"input": 3.00, "output": 15.00},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00},
    # Claude 3 family
    "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
    "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
}

# Default pricing for unknown models (assume haiku-like)
DEFAULT_PRICING = {"input": 0.25, "output": 1.25}


@dataclass
class UsageStats:
    """Accumulated usage statistics."""

    total_calls: int = 0
    cached_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    by_model: dict = field(default_factory=dict)
    session_start: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "total_calls": self.total_calls,
            "cached_calls": self.cached_calls,
            "api_calls": self.total_calls - self.cached_calls,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "total_tokens": self.tokens_in + self.tokens_out,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "total_cost_display": f"${self.total_cost_usd:.4f}",
            "avg_latency_ms": round(self.total_latency_ms / max(1, self.total_calls - self.cached_calls), 1),
            "session_duration_seconds": round(time.time() - self.session_start, 1),
            "by_model": self.by_model,
        }


@dataclass
class CallRecord:
    """Record of a single LLM call."""

    timestamp: float
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    latency_ms: float
    cached: bool
    agent_id: str | None = None
    call_type: str = "decision"  # decision, dialogue, compression, etc.


class LLMUsageTracker:
    """Thread-safe tracker for LLM API usage and costs."""

    def __init__(self):
        self._lock = threading.Lock()
        self._stats = UsageStats()
        self._recent_calls: list[CallRecord] = []
        self._max_recent = 100
        self._listeners: list[asyncio.Queue] = []
        self._db_callback = None  # Set by integration code

    def calculate_cost(self, model: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for a call in USD."""
        pricing = MODEL_PRICING.get(model, DEFAULT_PRICING)
        cost_in = (tokens_in / 1_000_000) * pricing["input"]
        cost_out = (tokens_out / 1_000_000) * pricing["output"]
        return cost_in + cost_out

    def record_call(
        self,
        model: str,
        tokens_in: int,
        tokens_out: int,
        latency_ms: float,
        cached: bool = False,
        agent_id: str | None = None,
        call_type: str = "decision",
    ) -> CallRecord:
        """Record an LLM call and update stats."""
        cost = 0.0 if cached else self.calculate_cost(model, tokens_in, tokens_out)

        record = CallRecord(
            timestamp=time.time(),
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
            latency_ms=latency_ms,
            cached=cached,
            agent_id=agent_id,
            call_type=call_type,
        )

        with self._lock:
            self._stats.total_calls += 1
            if cached:
                self._stats.cached_calls += 1
            else:
                self._stats.tokens_in += tokens_in
                self._stats.tokens_out += tokens_out
                self._stats.total_cost_usd += cost
                self._stats.total_latency_ms += latency_ms

            # Track by model
            if model not in self._stats.by_model:
                self._stats.by_model[model] = {
                    "calls": 0,
                    "tokens_in": 0,
                    "tokens_out": 0,
                    "cost_usd": 0.0,
                }
            self._stats.by_model[model]["calls"] += 1
            if not cached:
                self._stats.by_model[model]["tokens_in"] += tokens_in
                self._stats.by_model[model]["tokens_out"] += tokens_out
                self._stats.by_model[model]["cost_usd"] += cost

            # Keep recent calls
            self._recent_calls.append(record)
            if len(self._recent_calls) > self._max_recent:
                self._recent_calls = self._recent_calls[-self._max_recent:]

        # Notify listeners (async)
        self._notify_listeners(record)

        # Persist if callback set
        if self._db_callback:
            self._db_callback(record)

        return record

    def get_stats(self) -> UsageStats:
        """Get current usage statistics."""
        with self._lock:
            return UsageStats(
                total_calls=self._stats.total_calls,
                cached_calls=self._stats.cached_calls,
                tokens_in=self._stats.tokens_in,
                tokens_out=self._stats.tokens_out,
                total_cost_usd=self._stats.total_cost_usd,
                total_latency_ms=self._stats.total_latency_ms,
                by_model=dict(self._stats.by_model),
                session_start=self._stats.session_start,
            )

    def get_recent_calls(self, limit: int = 20) -> list[CallRecord]:
        """Get recent call records."""
        with self._lock:
            return list(self._recent_calls[-limit:])

    def reset(self) -> None:
        """Reset session statistics."""
        with self._lock:
            self._stats = UsageStats()
            self._recent_calls.clear()

    def subscribe(self, queue: asyncio.Queue) -> None:
        """Subscribe to usage updates."""
        self._listeners.append(queue)

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from usage updates."""
        if queue in self._listeners:
            self._listeners.remove(queue)

    def _notify_listeners(self, record: CallRecord) -> None:
        """Notify all listeners of a new call."""
        stats = self.get_stats()
        event_data = {
            "type": "llm_usage",
            "call": {
                "model": record.model,
                "tokens_in": record.tokens_in,
                "tokens_out": record.tokens_out,
                "cost_usd": round(record.cost_usd, 6),
                "latency_ms": round(record.latency_ms, 1),
                "cached": record.cached,
                "agent_id": record.agent_id,
                "call_type": record.call_type,
            },
            "totals": stats.to_dict(),
        }
        for queue in self._listeners:
            try:
                queue.put_nowait(event_data)
            except asyncio.QueueFull:
                pass

    def set_db_callback(self, callback) -> None:
        """Set callback for persisting calls to database."""
        self._db_callback = callback

    def set_event_callback(self, callback) -> None:
        """Set async callback for publishing events."""
        self._event_callback = callback

    def _notify_listeners(self, record: CallRecord) -> None:
        """Notify all listeners of a new call."""
        stats = self.get_stats()
        event_data = {
            "type": "llm_usage",
            "call": {
                "model": record.model,
                "tokens_in": record.tokens_in,
                "tokens_out": record.tokens_out,
                "cost_usd": round(record.cost_usd, 6),
                "latency_ms": round(record.latency_ms, 1),
                "cached": record.cached,
                "agent_id": record.agent_id,
                "call_type": record.call_type,
            },
            "totals": stats.to_dict(),
        }

        # Queue-based listeners
        for queue in self._listeners:
            try:
                queue.put_nowait(event_data)
            except asyncio.QueueFull:
                pass

        # Event callback (for SSE integration)
        if hasattr(self, "_event_callback") and self._event_callback:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self._event_callback(record, stats))
            except RuntimeError:
                pass  # No event loop available


# Global tracker instance
_tracker: LLMUsageTracker | None = None


def get_usage_tracker() -> LLMUsageTracker:
    """Get or create the global usage tracker."""
    global _tracker
    if _tracker is None:
        _tracker = LLMUsageTracker()
    return _tracker
