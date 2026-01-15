"""Narrative arcs API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db.models import Agent, ArcEvent, Event, NarrativeArc
from hamlet.narrative_arcs import NarrativeAnalyzer, NarrativeArcDetector
from hamlet.narrative_arcs.types import ACT_NAMES, Act, ArcStatus, ArcType
from hamlet.schemas.narrative_arc import (
    ActResponse,
    ArcEventResponse,
    ArcTimelineResponse,
    NarrativeArcResponse,
    NarrativeArcSummaryResponse,
    StoryDigestResponse,
)

router = APIRouter(prefix="/api/narrative-arcs", tags=["narrative-arcs"])


@router.get("", response_model=NarrativeArcSummaryResponse)
async def get_narrative_arcs(
    db: Session = Depends(get_db),
):
    """Get narrative arcs summary."""
    all_arcs = db.query(NarrativeArc).all()

    active = [a for a in all_arcs if a.status not in [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]]
    completed = [a for a in all_arcs if a.status == ArcStatus.RESOLUTION.value]
    abandoned = [a for a in all_arcs if a.status == ArcStatus.ABANDONED.value]

    # Count by type
    arcs_by_type = {}
    for arc in active:
        arcs_by_type[arc.type] = arcs_by_type.get(arc.type, 0) + 1

    # Find most dramatic (at climax with highest significance)
    climax_arcs = [a for a in active if a.status == ArcStatus.CLIMAX.value]
    most_dramatic = max(climax_arcs, key=lambda a: a.significance) if climax_arcs else None

    # Calculate intensity
    if not active:
        intensity = "quiet"
    elif len(climax_arcs) >= 2:
        intensity = "explosive"
    elif len(climax_arcs) >= 1:
        intensity = "dramatic"
    elif len([a for a in active if a.status == ArcStatus.RISING_ACTION.value]) >= 3:
        intensity = "building"
    elif len(active) >= 3:
        intensity = "active"
    else:
        intensity = "developing"

    return NarrativeArcSummaryResponse(
        total_arcs=len(all_arcs),
        active_arcs=len(active),
        completed_arcs=len(completed),
        abandoned_arcs=len(abandoned),
        arcs_by_type=arcs_by_type,
        most_dramatic=_arc_to_response(most_dramatic, db) if most_dramatic else None,
        narrative_intensity=intensity,
    )


@router.get("/digest", response_model=StoryDigestResponse)
async def get_story_digest(
    db: Session = Depends(get_db),
):
    """Get the daily story digest."""
    analyzer = NarrativeAnalyzer(db)
    digest = analyzer.generate_daily_digest()

    return StoryDigestResponse(
        title=digest.title,
        summary=digest.summary,
        active_arcs=digest.active_arcs,
        completed_arcs=digest.completed_arcs,
        notable_moments=digest.notable_moments,
        suggested_focus=digest.suggested_focus,
        village_state=analyzer.get_village_story_state(),
    )


@router.get("/{arc_id}", response_model=NarrativeArcResponse)
async def get_narrative_arc(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific narrative arc."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    return _arc_to_response(arc, db)


@router.get("/{arc_id}/timeline", response_model=ArcTimelineResponse)
async def get_arc_timeline(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Get the timeline of events for a narrative arc."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    analyzer = NarrativeAnalyzer(db)
    timeline = analyzer.get_arc_timeline(arc_id)

    return ArcTimelineResponse(
        arc_id=arc_id,
        arc_title=arc.title,
        timeline=timeline,
    )


@router.get("/{arc_id}/narrative")
async def get_arc_narrative(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Get a prose narrative summary of an arc."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    analyzer = NarrativeAnalyzer(db)
    narrative = analyzer.generate_arc_narrative(arc)

    return {"arc_id": arc_id, "narrative": narrative}


@router.get("/{arc_id}/events", response_model=list[ArcEventResponse])
async def get_arc_events(
    arc_id: int,
    db: Session = Depends(get_db),
):
    """Get events associated with a narrative arc."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    arc_events = (
        db.query(ArcEvent)
        .filter(ArcEvent.arc_id == arc_id)
        .order_by(ArcEvent.act_number)
        .all()
    )

    return [_arc_event_to_response(ae, db) for ae in arc_events]


@router.post("/{arc_id}/advance")
async def advance_arc(
    arc_id: int,
    turning_point: str = Query(..., description="Description of the turning point"),
    db: Session = Depends(get_db),
):
    """Manually advance an arc to the next act."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    if arc.status in [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]:
        raise HTTPException(status_code=400, detail="Arc is already complete")

    detector = NarrativeArcDetector(db)
    success = detector.advance_arc(arc, turning_point)

    if not success:
        raise HTTPException(status_code=400, detail="Cannot advance arc further")

    db.commit()

    return {
        "status": "success",
        "message": f"Arc advanced to act {arc.current_act}",
        "arc": _arc_to_response(arc, db),
    }


@router.post("/{arc_id}/complete")
async def complete_arc(
    arc_id: int,
    resolution: str = Query(..., description="Description of the resolution"),
    db: Session = Depends(get_db),
):
    """Complete a narrative arc."""
    arc = db.query(NarrativeArc).filter(NarrativeArc.id == arc_id).first()
    if not arc:
        raise HTTPException(status_code=404, detail="Narrative arc not found")

    if arc.status == ArcStatus.RESOLUTION.value:
        raise HTTPException(status_code=400, detail="Arc is already complete")

    detector = NarrativeArcDetector(db)
    detector.complete_arc(arc, resolution)

    db.commit()

    return {"status": "success", "message": "Arc completed"}


@router.get("/agent/{agent_id}", response_model=list[NarrativeArcResponse])
async def get_agent_arcs(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Get narrative arcs involving a specific agent."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    detector = NarrativeArcDetector(db)
    arcs = detector.get_arcs_for_agent(agent_id)

    return [_arc_to_response(arc, db) for arc in arcs]


@router.post("/detect")
async def detect_arcs(
    db: Session = Depends(get_db),
):
    """Manually trigger arc detection."""
    detector = NarrativeArcDetector(db)
    new_arcs = detector.detect_arcs()

    db.commit()

    return {
        "status": "success",
        "arcs_detected": len(new_arcs),
        "arcs": [_arc_to_response(arc, db) for arc in new_arcs],
    }


def _arc_to_response(arc: NarrativeArc, db: Session) -> NarrativeArcResponse:
    """Convert NarrativeArc model to response schema."""
    primary = db.query(Agent).filter(Agent.id == arc.primary_agent_id).first()
    secondary = (
        db.query(Agent).filter(Agent.id == arc.secondary_agent_id).first()
        if arc.secondary_agent_id
        else None
    )

    # Parse acts
    acts_data = arc.acts_list
    acts = []
    for act_data in acts_data:
        act = Act.from_dict(act_data)
        acts.append(ActResponse(
            number=act.number,
            name=ACT_NAMES.get(act.number, "Unknown"),
            status=act.status.value,
            events=act.events,
            key_moments=act.key_moments,
            turning_point=act.turning_point,
        ))

    return NarrativeArcResponse(
        id=arc.id,
        type=arc.type,
        title=arc.title,
        primary_agent_id=arc.primary_agent_id,
        primary_agent_name=primary.name if primary else None,
        secondary_agent_id=arc.secondary_agent_id,
        secondary_agent_name=secondary.name if secondary else None,
        theme=arc.theme,
        acts=acts,
        current_act=arc.current_act,
        current_act_name=ACT_NAMES.get(arc.current_act),
        status=arc.status,
        significance=arc.significance,
        discovered_at=arc.discovered_at,
        completed_at=arc.completed_at,
    )


def _arc_event_to_response(arc_event: ArcEvent, db: Session) -> ArcEventResponse:
    """Convert ArcEvent model to response schema."""
    event = db.query(Event).filter(Event.id == arc_event.event_id).first()

    return ArcEventResponse(
        id=arc_event.id,
        arc_id=arc_event.arc_id,
        event_id=arc_event.event_id,
        act_number=arc_event.act_number,
        is_turning_point=arc_event.is_turning_point,
        notes=arc_event.notes,
        event_summary=event.summary if event else None,
        event_timestamp=event.timestamp if event else None,
    )
