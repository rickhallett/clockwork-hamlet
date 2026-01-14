"""Event API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Event
from hamlet.schemas.event import EventPage, EventResponse

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("", response_model=list[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0, description="Number of events to skip"),
    limit: int = Query(50, ge=1, le=100, description="Max events to return"),
    event_type: str | None = Query(None, description="Filter by event type"),
    location_id: str | None = Query(None, description="Filter by location"),
    db: Session = Depends(get_db),
):
    """List events with pagination and optional filters."""
    query = db.query(Event)

    if event_type:
        query = query.filter(Event.type == event_type)
    if location_id:
        query = query.filter(Event.location_id == location_id)

    events = query.order_by(Event.timestamp.desc()).offset(skip).limit(limit).all()

    return [_event_to_response(e) for e in events]


@router.get("/history", response_model=EventPage)
async def get_event_history(
    cursor: int | None = Query(
        None,
        description="Cursor for pagination. Pass the next_cursor from the previous response.",
    ),
    limit: int = Query(50, ge=1, le=100, description="Max events to return per page"),
    event_type: str | None = Query(None, description="Filter by event type"),
    location_id: str | None = Query(None, description="Filter by location"),
    actor_id: str | None = Query(None, description="Filter by actor (agent ID)"),
    min_significance: int | None = Query(
        None, ge=1, le=3, description="Minimum significance level"
    ),
    timestamp_from: int | None = Query(
        None, description="Filter events from this Unix timestamp (inclusive)"
    ),
    timestamp_to: int | None = Query(
        None, description="Filter events up to this Unix timestamp (inclusive)"
    ),
    include_count: bool = Query(
        False,
        description="Include total count (may impact performance for large datasets)",
    ),
    db: Session = Depends(get_db),
):
    """Get event history with cursor-based pagination.

    Cursor-based pagination provides efficient, consistent paging through large
    event datasets. Events are returned in descending order (newest first).

    The cursor is the event ID - pass the `next_cursor` from the response to
    get the next page.
    """
    query = db.query(Event)

    # Apply filters
    if event_type:
        query = query.filter(Event.type == event_type)
    if location_id:
        query = query.filter(Event.location_id == location_id)
    if actor_id:
        # actors is stored as JSON array, use LIKE for SQLite compatibility
        query = query.filter(Event.actors.like(f'%"{actor_id}"%'))
    if min_significance:
        query = query.filter(Event.significance >= min_significance)
    if timestamp_from:
        query = query.filter(Event.timestamp >= timestamp_from)
    if timestamp_to:
        query = query.filter(Event.timestamp <= timestamp_to)

    # Apply cursor (get events with id < cursor for descending order)
    if cursor is not None:
        query = query.filter(Event.id < cursor)

    # Get total count if requested (before applying limit)
    total_count = None
    if include_count:
        # Count query without cursor filter for accurate total
        count_query = db.query(func.count(Event.id))
        if event_type:
            count_query = count_query.filter(Event.type == event_type)
        if location_id:
            count_query = count_query.filter(Event.location_id == location_id)
        if actor_id:
            count_query = count_query.filter(Event.actors.like(f'%"{actor_id}"%'))
        if min_significance:
            count_query = count_query.filter(Event.significance >= min_significance)
        if timestamp_from:
            count_query = count_query.filter(Event.timestamp >= timestamp_from)
        if timestamp_to:
            count_query = count_query.filter(Event.timestamp <= timestamp_to)
        total_count = count_query.scalar()

    # Fetch one extra to determine if there are more results
    events = query.order_by(Event.id.desc()).limit(limit + 1).all()

    # Determine if there are more results
    has_more = len(events) > limit
    if has_more:
        events = events[:limit]  # Remove the extra event

    # Determine next cursor
    next_cursor = events[-1].id if has_more and events else None

    return EventPage(
        events=[_event_to_response(e) for e in events],
        next_cursor=next_cursor,
        has_more=has_more,
        total_count=total_count,
    )


@router.get("/highlights", response_model=list[EventResponse])
async def get_highlights(
    limit: int = Query(10, ge=1, le=50, description="Max highlights to return"),
    db: Session = Depends(get_db),
):
    """Get significant/highlighted events."""
    events = (
        db.query(Event)
        .filter(Event.significance >= 2)
        .order_by(Event.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [_event_to_response(e) for e in events]


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    from fastapi import HTTPException

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail=f"Event {event_id} not found")
    return _event_to_response(event)


def _event_to_response(event: Event) -> EventResponse:
    """Convert Event model to response schema."""
    return EventResponse(
        id=event.id,
        timestamp=event.timestamp,
        type=event.type,
        actors=event.actors_list,
        location_id=event.location_id,
        summary=event.summary,
        detail=event.detail,
        significance=event.significance,
    )
