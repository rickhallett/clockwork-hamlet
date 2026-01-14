"""SSE streaming endpoint for real-time events."""

import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from hamlet.simulation.events import EventType, SimulationEvent, event_bus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["stream"])

# Heartbeat interval in seconds
HEARTBEAT_INTERVAL = 15


def event_to_dict(event: SimulationEvent) -> dict:
    """Convert SimulationEvent to dictionary for JSON serialization."""
    return {
        "type": event.type.value,
        "summary": event.summary,
        "timestamp": event.timestamp,
        "actors": event.actors,
        "location_id": event.location_id,
        "detail": event.detail,
        "significance": event.significance,
        "data": event.data,
    }


async def event_generator(
    event_types: list[str] | None = None,
    location_id: str | None = None,
    agent_id: str | None = None,
) -> AsyncGenerator[dict, None]:
    """Generate SSE events from the event bus.

    Args:
        event_types: Optional list of event types to filter
        location_id: Optional location to filter events
        agent_id: Optional agent to filter events (must be in actors)

    Yields:
        SSE event dictionaries
    """
    queue = event_bus.subscribe()
    logger.info(
        f"SSE client connected (filters: types={event_types}, location={location_id}, agent={agent_id})"
    )

    try:
        while True:
            try:
                # Wait for event with timeout for heartbeat
                event: SimulationEvent = await asyncio.wait_for(
                    queue.get(), timeout=HEARTBEAT_INTERVAL
                )

                # Apply filters
                if event_types and event.type.value not in event_types:
                    continue

                if location_id and event.location_id != location_id:
                    continue

                if agent_id and agent_id not in event.actors:
                    continue

                # Yield the event (using 'message' event type for browser EventSource.onmessage compatibility)
                yield {
                    "data": json.dumps(event_to_dict(event)),
                }

            except TimeoutError:
                # Send heartbeat to keep connection alive (no event name for onmessage compatibility)
                yield {
                    "data": json.dumps({"type": "heartbeat"}),
                }

    except asyncio.CancelledError:
        logger.info("SSE client disconnected (cancelled)")
        raise
    finally:
        event_bus.unsubscribe(queue)
        logger.info("SSE client unsubscribed")


@router.get("/stream")
async def stream_events(
    types: str | None = Query(None, description="Comma-separated event types to filter"),
    location: str | None = Query(None, description="Filter by location ID"),
    agent: str | None = Query(None, description="Filter by agent ID (events involving this agent)"),
):
    """Stream real-time simulation events via SSE.

    Connect to this endpoint to receive live updates from the simulation.

    Query parameters:
    - types: Comma-separated list of event types (movement, dialogue, action, etc.)
    - location: Only receive events from this location
    - agent: Only receive events involving this agent

    Events are sent in SSE format:
    ```
    event: movement
    data: {"type": "movement", "summary": "Agnes moved to Town Square", ...}

    event: heartbeat
    data: {"type": "heartbeat"}
    ```
    """
    # Parse event types filter
    event_types = None
    if types:
        event_types = [t.strip() for t in types.split(",")]
        # Validate event types
        valid_types = {e.value for e in EventType}
        event_types = [t for t in event_types if t in valid_types]

    return EventSourceResponse(
        event_generator(
            event_types=event_types,
            location_id=location,
            agent_id=agent,
        )
    )


@router.get("/stream/history")
async def get_stream_history(
    limit: int = Query(50, ge=1, le=200, description="Number of recent events"),
):
    """Get recent event history.

    Useful for clients to catch up on events they may have missed.
    """
    history = event_bus.get_history(limit)
    return [event_to_dict(e) for e in history]
