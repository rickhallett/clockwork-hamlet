"""Dashboard API endpoints for real-time monitoring (DASH-11 through DASH-15)."""

import time
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from hamlet.db import Agent, Event, get_db
from hamlet.simulation.engine import get_health_metrics

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/health")
async def get_simulation_health() -> dict:
    """Get current simulation health metrics (DASH-14).

    Returns real-time health indicators including:
    - Tick rate (ticks per minute)
    - Queue depth (pending agents)
    - Error count
    - Processing latency
    - Uptime
    """
    metrics = get_health_metrics()
    return {
        "status": "healthy" if metrics.error_count == 0 else "degraded",
        "metrics": metrics.to_dict(),
    }


@router.get("/positions")
async def get_agent_positions(db: Session = Depends(get_db)) -> dict:
    """Get current agent positions (DASH-12).

    Returns the current location of all agents. Use SSE stream
    with type=positions for real-time updates.
    """
    agents = db.query(Agent).all()

    positions = [
        {
            "id": agent.id,
            "name": agent.name,
            "location_id": agent.location_id,
            "state": agent.state,
        }
        for agent in agents
    ]

    # Group by location for map display
    by_location: dict[str, list[dict]] = defaultdict(list)
    for pos in positions:
        loc_id = pos["location_id"] or "unknown"
        by_location[loc_id].append(pos)

    return {
        "positions": positions,
        "by_location": dict(by_location),
        "total_agents": len(positions),
    }


@router.get("/event-rates")
async def get_event_rates(
    minutes: int = Query(60, ge=1, le=1440, description="Minutes of history"),
    bucket_size: int = Query(1, ge=1, le=60, description="Bucket size in minutes"),
    db: Session = Depends(get_db),
) -> dict:
    """Get event rates over time for sparklines (DASH-15).

    Returns event counts bucketed by time for visualization.

    Args:
        minutes: How many minutes of history to include (default 60)
        bucket_size: Size of each time bucket in minutes (default 1)
    """
    now = int(time.time())
    start_time = now - (minutes * 60)

    # Query events in time range
    events = (
        db.query(Event.timestamp, Event.type)
        .filter(Event.timestamp >= start_time)
        .all()
    )

    # Initialize buckets
    num_buckets = minutes // bucket_size
    buckets = [0] * num_buckets
    by_type: dict[str, list[int]] = defaultdict(lambda: [0] * num_buckets)

    # Fill buckets
    for event in events:
        # Calculate bucket index (0 = oldest, num_buckets-1 = most recent)
        elapsed = event.timestamp - start_time
        bucket_idx = min(int(elapsed / (bucket_size * 60)), num_buckets - 1)
        if 0 <= bucket_idx < num_buckets:
            buckets[bucket_idx] += 1
            by_type[event.type][bucket_idx] += 1

    # Calculate rates
    total_events = sum(buckets)
    current_rate = buckets[-1] / bucket_size if buckets else 0  # events/minute in last bucket
    peak_rate = max(buckets) / bucket_size if buckets else 0
    avg_rate = (total_events / minutes) if minutes > 0 else 0

    return {
        "events_per_bucket": buckets,
        "by_type": dict(by_type),
        "bucket_size_minutes": bucket_size,
        "total_buckets": num_buckets,
        "total_events": total_events,
        "current_rate": round(current_rate, 2),
        "peak_rate": round(peak_rate, 2),
        "avg_rate": round(avg_rate, 2),
        "time_range": {
            "start": start_time,
            "end": now,
            "minutes": minutes,
        },
    }


@router.get("/summary")
async def get_dashboard_summary(db: Session = Depends(get_db)) -> dict:
    """Get a combined summary for the dashboard.

    Combines health, positions, and recent event stats into one response
    for efficient initial page load.
    """
    # Health
    metrics = get_health_metrics()

    # Positions
    agents = db.query(Agent).all()
    positions = [
        {
            "id": a.id,
            "name": a.name,
            "location_id": a.location_id,
            "state": a.state,
        }
        for a in agents
    ]

    # Recent event counts (last 5 minutes)
    five_min_ago = int(time.time()) - 300
    recent_count = db.query(func.count(Event.id)).filter(
        Event.timestamp >= five_min_ago
    ).scalar() or 0

    # Events by type (last hour)
    one_hour_ago = int(time.time()) - 3600
    by_type = dict(
        db.query(Event.type, func.count(Event.id))
        .filter(Event.timestamp >= one_hour_ago)
        .group_by(Event.type)
        .all()
    )

    return {
        "health": {
            "status": "healthy" if metrics.error_count == 0 else "degraded",
            "metrics": metrics.to_dict(),
        },
        "positions": positions,
        "events": {
            "recent_5min": recent_count,
            "by_type_1hr": by_type,
        },
    }
