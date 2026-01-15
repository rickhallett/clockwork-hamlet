"""Life events API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db.models import Agent, LifeEvent
from hamlet.life_events import LifeEventConsequences, LifeEventGenerator
from hamlet.life_events.types import LifeEventStatus, LifeEventType
from hamlet.schemas.life_event import (
    LifeEventCreate,
    LifeEventResponse,
    LifeEventSummaryResponse,
)

router = APIRouter(prefix="/api/life-events", tags=["life-events"])


@router.get("", response_model=LifeEventSummaryResponse)
async def get_life_events(
    limit: int = Query(50, description="Maximum number of events to return"),
    status: str | None = Query(None, description="Filter by status"),
    event_type: str | None = Query(None, description="Filter by event type"),
    db: Session = Depends(get_db),
):
    """Get life events summary."""
    query = db.query(LifeEvent)

    if status:
        query = query.filter(LifeEvent.status == status)

    if event_type:
        query = query.filter(LifeEvent.type == event_type)

    total = query.count()
    active = query.filter(LifeEvent.status == LifeEventStatus.ACTIVE.value).count()

    # Get counts by type
    all_events = db.query(LifeEvent).all()
    events_by_type = {}
    for event in all_events:
        events_by_type[event.type] = events_by_type.get(event.type, 0) + 1

    # Get recent events
    recent = (
        query.order_by(LifeEvent.timestamp.desc())
        .limit(limit)
        .all()
    )

    return LifeEventSummaryResponse(
        total_events=total,
        active_events=active,
        events_by_type=events_by_type,
        recent_events=[_event_to_response(e, db) for e in recent],
    )


@router.get("/{event_id}", response_model=LifeEventResponse)
async def get_life_event(
    event_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific life event."""
    event = db.query(LifeEvent).filter(LifeEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Life event not found")

    return _event_to_response(event, db)


@router.post("", response_model=LifeEventResponse)
async def create_life_event(
    event_data: LifeEventCreate,
    db: Session = Depends(get_db),
):
    """Manually create a life event."""
    # Verify primary agent exists
    primary = db.query(Agent).filter(Agent.id == event_data.primary_agent_id).first()
    if not primary:
        raise HTTPException(status_code=404, detail="Primary agent not found")

    # Verify secondary agent if provided
    secondary = None
    if event_data.secondary_agent_id:
        secondary = db.query(Agent).filter(Agent.id == event_data.secondary_agent_id).first()
        if not secondary:
            raise HTTPException(status_code=404, detail="Secondary agent not found")

    # Validate event type
    try:
        event_type = LifeEventType(event_data.type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_data.type}")

    # Create the event
    generator = LifeEventGenerator(db)
    event = generator._create_event(
        event_type,
        event_data.primary_agent_id,
        event_data.secondary_agent_id,
    )

    # Apply consequences
    consequences = LifeEventConsequences(db)
    consequences.apply_event_consequences(event)

    db.commit()

    return _event_to_response(event, db)


@router.post("/{event_id}/resolve")
async def resolve_life_event(
    event_id: int,
    outcome: str = Query("success", description="Outcome of the resolution"),
    db: Session = Depends(get_db),
):
    """Resolve an active life event."""
    event = db.query(LifeEvent).filter(LifeEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Life event not found")

    if event.status != LifeEventStatus.ACTIVE.value:
        raise HTTPException(status_code=400, detail="Event is not active")

    consequences = LifeEventConsequences(db)
    consequences.resolve_event(event, outcome)

    db.commit()

    return {"status": "success", "message": f"Event resolved with outcome: {outcome}"}


@router.get("/agent/{agent_id}", response_model=list[LifeEventResponse])
async def get_agent_life_events(
    agent_id: str,
    active_only: bool = Query(False, description="Only return active events"),
    db: Session = Depends(get_db),
):
    """Get life events involving a specific agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    query = db.query(LifeEvent).filter(
        (LifeEvent.primary_agent_id == agent_id)
        | (LifeEvent.secondary_agent_id == agent_id)
    )

    if active_only:
        query = query.filter(LifeEvent.status == LifeEventStatus.ACTIVE.value)

    events = query.order_by(LifeEvent.timestamp.desc()).all()

    return [_event_to_response(e, db) for e in events]


@router.post("/check")
async def check_life_events(
    db: Session = Depends(get_db),
):
    """Manually trigger life event detection."""
    generator = LifeEventGenerator(db)
    new_events = generator.check_for_life_events()

    consequences = LifeEventConsequences(db)
    for event in new_events:
        consequences.apply_event_consequences(event)

    db.commit()

    return {
        "status": "success",
        "events_detected": len(new_events),
        "events": [_event_to_response(e, db) for e in new_events],
    }


def _event_to_response(event: LifeEvent, db: Session) -> LifeEventResponse:
    """Convert LifeEvent model to response schema."""
    primary = db.query(Agent).filter(Agent.id == event.primary_agent_id).first()
    secondary = (
        db.query(Agent).filter(Agent.id == event.secondary_agent_id).first()
        if event.secondary_agent_id
        else None
    )

    return LifeEventResponse(
        id=event.id,
        type=event.type,
        primary_agent_id=event.primary_agent_id,
        primary_agent_name=primary.name if primary else None,
        secondary_agent_id=event.secondary_agent_id,
        secondary_agent_name=secondary.name if secondary else None,
        description=event.description,
        significance=event.significance,
        status=event.status,
        related_agents=event.related_agents_list,
        effects=event.effects_dict,
        timestamp=event.timestamp,
        resolved_at=event.resolved_at,
    )
