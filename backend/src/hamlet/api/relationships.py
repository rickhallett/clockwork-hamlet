"""Relationship API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Relationship
from hamlet.schemas.relationship import RelationshipGraphResponse, RelationshipResponse

router = APIRouter(prefix="/api/relationships", tags=["relationships"])


@router.get("", response_model=RelationshipGraphResponse)
async def get_relationship_graph(db: Session = Depends(get_db)):
    """Get the full relationship graph."""
    relationships = db.query(Relationship).all()
    agents = db.query(Agent).all()

    # Build nodes (agents)
    nodes = [{"id": a.id, "name": a.name} for a in agents]

    # Build edges (relationships)
    edges = [
        {
            "source": r.agent_id,
            "target": r.target_id,
            "type": r.type,
            "score": r.score,
        }
        for r in relationships
    ]

    return RelationshipGraphResponse(nodes=nodes, edges=edges)


@router.get("/agent/{agent_id}", response_model=list[RelationshipResponse])
async def get_agent_relationships(
    agent_id: str,
    direction: str = Query("both", description="Filter: outgoing, incoming, or both"),
    db: Session = Depends(get_db),
):
    """Get relationships for a specific agent."""
    relationships = []

    if direction in ("outgoing", "both"):
        outgoing = db.query(Relationship).filter(Relationship.agent_id == agent_id).all()
        relationships.extend(outgoing)

    if direction in ("incoming", "both"):
        incoming = db.query(Relationship).filter(Relationship.target_id == agent_id).all()
        # Avoid duplicates if both directions requested
        existing_ids = {r.id for r in relationships}
        relationships.extend([r for r in incoming if r.id not in existing_ids])

    return [_relationship_to_response(r, db) for r in relationships]


def _relationship_to_response(rel: Relationship, db: Session) -> RelationshipResponse:
    """Convert Relationship model to response schema."""
    agent = db.query(Agent).filter(Agent.id == rel.agent_id).first()
    target = db.query(Agent).filter(Agent.id == rel.target_id).first()

    return RelationshipResponse(
        id=rel.id,
        agent_id=rel.agent_id,
        agent_name=agent.name if agent else None,
        target_id=rel.target_id,
        target_name=target.name if target else None,
        type=rel.type,
        score=rel.score,
        history=rel.history_list,
    )
