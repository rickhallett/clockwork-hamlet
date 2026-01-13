"""Digest API routes."""

import time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Event, WorldState

router = APIRouter(prefix="/api/digest", tags=["digest"])


@router.get("/daily")
async def get_daily_digest(db: Session = Depends(get_db)):
    """Get today's summary/digest."""
    # Get world state to determine current day
    world_state = db.query(WorldState).first()
    current_day = world_state.current_day if world_state else 1

    # Get recent significant events (from the last day)
    now = int(time.time())
    day_ago = now - 86400

    events = (
        db.query(Event)
        .filter(Event.timestamp >= day_ago, Event.significance >= 2)
        .order_by(Event.significance.desc(), Event.timestamp.desc())
        .limit(10)
        .all()
    )

    # Build digest
    headlines = []
    for event in events[:3]:
        headlines.append(
            {"summary": event.summary, "significance": event.significance, "type": event.type}
        )

    other_events = []
    for event in events[3:]:
        other_events.append({"summary": event.summary, "type": event.type})

    return {
        "day": current_day,
        "generated_at": now,
        "headlines": headlines,
        "other_events": other_events,
        "total_events_today": len(events),
    }


@router.get("/weekly")
async def get_weekly_digest(db: Session = Depends(get_db)):
    """Get this week's summary/digest."""
    world_state = db.query(WorldState).first()
    current_day = world_state.current_day if world_state else 1

    # Get events from the last 7 in-game days worth of ticks
    now = int(time.time())
    week_ago = now - (86400 * 7)

    events = (
        db.query(Event)
        .filter(Event.timestamp >= week_ago, Event.significance >= 2)
        .order_by(Event.significance.desc())
        .limit(20)
        .all()
    )

    # Group by type
    by_type: dict[str, list[str]] = {}
    for event in events:
        if event.type not in by_type:
            by_type[event.type] = []
        by_type[event.type].append(event.summary)

    return {
        "week_ending_day": current_day,
        "generated_at": now,
        "top_stories": [e.summary for e in events[:5]],
        "events_by_type": by_type,
        "total_significant_events": len(events),
    }
