"""Faction API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db.models import Agent, Faction, FactionMembership, FactionRelationship, Location
from hamlet.factions import FactionManager
from hamlet.factions.types import FactionRole, FactionStatus, FactionType
from hamlet.schemas.faction import (
    FactionCreate,
    FactionMemberResponse,
    FactionRelationshipResponse,
    FactionResponse,
    FactionSummaryResponse,
)

router = APIRouter(prefix="/api/factions", tags=["factions"])


@router.get("", response_model=FactionSummaryResponse)
async def get_factions(
    active_only: bool = Query(True, description="Only return active factions"),
    db: Session = Depends(get_db),
):
    """Get all factions."""
    manager = FactionManager(db)
    factions = manager.get_all_factions(active_only=active_only)

    total_members = 0
    faction_responses = []

    for faction in factions:
        members = manager.get_faction_members(faction.id)
        total_members += len(members)
        faction_responses.append(_faction_to_response(faction, len(members), db))

    return FactionSummaryResponse(
        total_factions=len(factions),
        active_factions=len([f for f in factions if f.status == FactionStatus.ACTIVE.value]),
        total_members=total_members,
        factions=faction_responses,
    )


@router.get("/{faction_id}", response_model=FactionResponse)
async def get_faction(
    faction_id: int,
    db: Session = Depends(get_db),
):
    """Get a specific faction."""
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    manager = FactionManager(db)
    members = manager.get_faction_members(faction_id)

    return _faction_to_response(faction, len(members), db)


@router.post("", response_model=FactionResponse)
async def create_faction(
    faction_data: FactionCreate,
    db: Session = Depends(get_db),
):
    """Create a new faction."""
    # Verify founder exists
    founder = db.query(Agent).filter(Agent.id == faction_data.founder_id).first()
    if not founder:
        raise HTTPException(status_code=404, detail="Founder agent not found")

    manager = FactionManager(db)
    faction = manager.create_faction(
        name=faction_data.name,
        founder_id=faction_data.founder_id,
        description=faction_data.description,
        beliefs=faction_data.beliefs,
        goals=faction_data.goals,
        location_id=faction_data.location_id,
    )

    db.commit()

    return _faction_to_response(faction, 1, db)


@router.get("/{faction_id}/members", response_model=list[FactionMemberResponse])
async def get_faction_members(
    faction_id: int,
    active_only: bool = Query(True, description="Only return active members"),
    db: Session = Depends(get_db),
):
    """Get members of a faction."""
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    manager = FactionManager(db)
    members = manager.get_faction_members(faction_id, active_only=active_only)

    return [_member_to_response(m, db) for m in members]


@router.post("/{faction_id}/members/{agent_id}", response_model=FactionMemberResponse)
async def add_faction_member(
    faction_id: int,
    agent_id: str,
    role: str = Query("recruit", description="Initial role for the member"),
    db: Session = Depends(get_db),
):
    """Add a member to a faction."""
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        faction_role = FactionRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {role}")

    manager = FactionManager(db)
    membership = manager.add_member(faction_id, agent_id, faction_role)

    if not membership:
        raise HTTPException(
            status_code=400,
            detail="Could not add member (may already be a member or at membership limit)",
        )

    db.commit()

    return _member_to_response(membership, db)


@router.delete("/{faction_id}/members/{agent_id}")
async def remove_faction_member(
    faction_id: int,
    agent_id: str,
    expel: bool = Query(False, description="Whether this is an expulsion"),
    db: Session = Depends(get_db),
):
    """Remove a member from a faction."""
    manager = FactionManager(db)
    success = manager.remove_member(faction_id, agent_id, expelled=expel)

    if not success:
        raise HTTPException(status_code=404, detail="Membership not found")

    db.commit()

    return {"status": "success", "message": "Member removed"}


@router.get("/{faction_id}/relationships", response_model=list[FactionRelationshipResponse])
async def get_faction_relationships(
    faction_id: int,
    db: Session = Depends(get_db),
):
    """Get relationships between this faction and others."""
    faction = db.query(Faction).filter(Faction.id == faction_id).first()
    if not faction:
        raise HTTPException(status_code=404, detail="Faction not found")

    relationships = (
        db.query(FactionRelationship)
        .filter(
            (FactionRelationship.faction_1_id == faction_id)
            | (FactionRelationship.faction_2_id == faction_id)
        )
        .all()
    )

    return [_faction_rel_to_response(r, db) for r in relationships]


@router.get("/agent/{agent_id}", response_model=list[FactionResponse])
async def get_agent_factions(
    agent_id: str,
    db: Session = Depends(get_db),
):
    """Get factions an agent belongs to."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    manager = FactionManager(db)
    memberships = manager.get_agent_factions(agent_id)

    responses = []
    for membership in memberships:
        faction = db.query(Faction).filter(Faction.id == membership.faction_id).first()
        if faction:
            members = manager.get_faction_members(faction.id)
            responses.append(_faction_to_response(faction, len(members), db))

    return responses


def _faction_to_response(faction: Faction, member_count: int, db: Session) -> FactionResponse:
    """Convert Faction model to response schema."""
    founder = db.query(Agent).filter(Agent.id == faction.founder_id).first() if faction.founder_id else None
    location = db.query(Location).filter(Location.id == faction.location_id).first() if faction.location_id else None

    return FactionResponse(
        id=faction.id,
        name=faction.name,
        description=faction.description,
        founder_id=faction.founder_id,
        founder_name=founder.name if founder else None,
        location_id=faction.location_id,
        location_name=location.name if location else None,
        beliefs=faction.beliefs_list,
        goals=faction.goals_list,
        treasury=faction.treasury,
        reputation=faction.reputation,
        status=faction.status,
        member_count=member_count,
        created_at=faction.created_at,
    )


def _member_to_response(membership: FactionMembership, db: Session) -> FactionMemberResponse:
    """Convert FactionMembership model to response schema."""
    agent = db.query(Agent).filter(Agent.id == membership.agent_id).first()

    return FactionMemberResponse(
        id=membership.id,
        faction_id=membership.faction_id,
        agent_id=membership.agent_id,
        agent_name=agent.name if agent else None,
        role=membership.role,
        loyalty=membership.loyalty,
        contributions=membership.contributions,
        joined_at=membership.joined_at,
        left_at=membership.left_at,
    )


def _faction_rel_to_response(rel: FactionRelationship, db: Session) -> FactionRelationshipResponse:
    """Convert FactionRelationship model to response schema."""
    faction_1 = db.query(Faction).filter(Faction.id == rel.faction_1_id).first()
    faction_2 = db.query(Faction).filter(Faction.id == rel.faction_2_id).first()

    return FactionRelationshipResponse(
        id=rel.id,
        faction_1_id=rel.faction_1_id,
        faction_1_name=faction_1.name if faction_1 else None,
        faction_2_id=rel.faction_2_id,
        faction_2_name=faction_2.name if faction_2 else None,
        type=rel.type,
        score=rel.score,
        history=rel.history_list,
    )
