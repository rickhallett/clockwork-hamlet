"""Event bus for broadcasting simulation events."""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of simulation events."""

    MOVEMENT = "movement"
    DIALOGUE = "dialogue"
    ACTION = "action"
    RELATIONSHIP = "relationship"
    DISCOVERY = "discovery"
    SYSTEM = "system"
    TICK = "tick"


@dataclass
class SimulationEvent:
    """An event in the simulation."""

    type: EventType
    summary: str
    timestamp: int
    actors: list[str] = field(default_factory=list)
    location_id: str | None = None
    detail: str | None = None
    significance: int = 1
    data: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Async event bus for broadcasting simulation events."""

    def __init__(self):
        self._subscribers: list[asyncio.Queue] = []
        self._history: list[SimulationEvent] = []
        self._max_history = 1000

    def subscribe(self) -> asyncio.Queue:
        """Subscribe to events. Returns a queue that will receive events."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from events."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    async def publish(self, event: SimulationEvent) -> None:
        """Publish an event to all subscribers."""
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history :]

        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                # Drop event if queue is full
                pass

    def get_history(self, limit: int = 100) -> list[SimulationEvent]:
        """Get recent event history."""
        return self._history[-limit:]


# Global event bus instance
event_bus = EventBus()
