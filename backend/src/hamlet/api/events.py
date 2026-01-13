"""Event API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Event
from hamlet.schemas.event import EventResponse

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
