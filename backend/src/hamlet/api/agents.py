"""Agent API routes."""

import json
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.auth.deps import get_current_active_user, get_current_user
from hamlet.db import Agent, Location, Memory, User, UserAgentQuota
from hamlet.memory import build_memory_context, get_all_memories
from hamlet.schemas.agent import (
    AgentCreateRequest,
    AgentCreateResponse,
    AgentPreviewRequest,
    AgentPreviewResponse,
    AgentQuotaResponse,
    AgentResponse,
    TRAIT_PRESETS,
    TraitsSchema,
    generate_trait_summary,
    get_preset_traits,
    identify_archetype,
)
from hamlet.schemas.memory import MemoryResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


# Constants for rate limiting and quotas
DEFAULT_MAX_AGENTS = 3
DEFAULT_RATE_LIMIT_SECONDS = 3600  # 1 hour between creations


# Helper functions for agent creation

def _get_or_create_quota(user_id: int, db: Session) -> UserAgentQuota:
    """Get or create a quota record for a user."""
    quota = db.query(UserAgentQuota).filter(UserAgentQuota.user_id == user_id).first()
    if not quota:
        quota = UserAgentQuota(
            user_id=user_id,
            max_agents=DEFAULT_MAX_AGENTS,
            agents_created=0,
            rate_limit_window=DEFAULT_RATE_LIMIT_SECONDS,
        )
        db.add(quota)
        db.commit()
        db.refresh(quota)
    return quota


def _check_rate_limit(quota: UserAgentQuota) -> tuple[bool, float | None]:
    """Check if user is rate limited. Returns (is_allowed, next_available_time)."""
    if quota.last_creation_at is None:
        return True, None

    elapsed = time.time() - quota.last_creation_at
    if elapsed >= quota.rate_limit_window:
        return True, None

    next_available = quota.last_creation_at + quota.rate_limit_window
    return False, next_available


def _generate_agent_id(name: str, db: Session) -> str:
    """Generate a unique agent ID based on name."""
    # Convert name to lowercase, replace spaces with underscores
    base_id = name.lower().replace(" ", "_").replace("'", "").replace("-", "_")
    # Remove duplicate underscores
    while "__" in base_id:
        base_id = base_id.replace("__", "_")

    # Check if ID exists, add suffix if needed
    candidate_id = base_id
    counter = 1
    while db.query(Agent).filter(Agent.id == candidate_id).first():
        candidate_id = f"{base_id}_{counter}"
        counter += 1

    return candidate_id


def _generate_compatibility_notes(traits: TraitsSchema, db: Session) -> list[str]:
    """Generate notes about how this agent might interact with existing agents."""
    notes = []
    existing_agents = db.query(Agent).limit(5).all()

    for agent in existing_agents:
        agent_traits = agent.traits_dict
        if not agent_traits:
            continue

        # Check for potential conflicts or friendships
        if traits.empathy >= 7 and agent_traits.get("empathy", 5) >= 7:
            notes.append(f"May form a close friendship with {agent.name} (both empathetic)")
        elif traits.ambition >= 7 and agent_traits.get("ambition", 5) >= 7:
            notes.append(f"Potential rivalry with {agent.name} (both ambitious)")
        elif traits.discretion <= 3 and agent_traits.get("discretion", 5) >= 7:
            notes.append(f"May frustrate {agent.name} (indiscreet vs. private)")

    if not notes:
        notes.append("Should integrate well with existing village residents")

    return notes[:3]  # Limit to 3 notes


# Static routes (must be before /{agent_id} to avoid conflicts)


@router.get("/presets")
async def list_presets():
    """Get all available trait presets."""
    return {
        "presets": [
            {"id": key, "name": data["name"], "description": data["description"]}
            for key, data in TRAIT_PRESETS.items()
        ]
    }


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get details for a specific preset."""
    preset = TRAIT_PRESETS.get(preset_id.lower())
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_id}' not found"
        )
    return {
        "id": preset_id.lower(),
        "name": preset["name"],
        "description": preset["description"],
        "traits": preset["traits"]
    }


@router.get("/quota", response_model=AgentQuotaResponse)
async def get_user_quota(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get the current user's agent creation quota."""
    quota = _get_or_create_quota(current_user.id, db)
    is_allowed, next_available = _check_rate_limit(quota)

    return AgentQuotaResponse(
        max_agents=quota.max_agents,
        agents_created=quota.agents_created,
        remaining=max(0, quota.max_agents - quota.agents_created),
        can_create=quota.agents_created < quota.max_agents and is_allowed,
        next_creation_available_at=next_available,
    )


@router.get("/my-agents", response_model=list[AgentResponse])
async def list_my_agents(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List all agents created by the current user."""
    agents = (
        db.query(Agent)
        .filter(Agent.creator_id == current_user.id)
        .all()
    )
    return [_agent_to_response(a) for a in agents]


@router.post("/preview", response_model=AgentPreviewResponse)
async def preview_agent(
    request: AgentPreviewRequest,
    current_user: User | None = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Preview an agent before creation. Available to all users (auth optional)."""
    # Get location name if provided
    location_name = None
    if request.location_id:
        location = db.query(Location).filter(Location.id == request.location_id).first()
        if location:
            location_name = location.name
        else:
            location_name = "Unknown location"
    else:
        location_name = "Town Square (default)"

    # Generate preview information
    trait_summary = generate_trait_summary(request.traits)
    archetype = identify_archetype(request.traits)
    compatibility_notes = _generate_compatibility_notes(request.traits, db)

    return AgentPreviewResponse(
        name=request.name,
        personality_prompt=request.personality_prompt,
        traits=request.traits.model_dump(),
        location_name=location_name,
        trait_summary=trait_summary,
        personality_archetype=archetype,
        compatibility_notes=compatibility_notes,
    )


@router.post("/create", response_model=AgentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: AgentCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new agent. Requires authentication."""
    # Check quota
    quota = _get_or_create_quota(current_user.id, db)

    if quota.agents_created >= quota.max_agents:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Agent quota exceeded. Maximum {quota.max_agents} agents allowed."
        )

    # Check rate limit
    is_allowed, next_available = _check_rate_limit(quota)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limited. Next creation available at {next_available}",
            headers={"Retry-After": str(int(next_available - time.time()))}
        )

    # Apply preset if specified
    traits = request.traits
    if request.preset:
        preset_traits = get_preset_traits(request.preset)
        if preset_traits:
            traits = preset_traits
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown preset: {request.preset}"
            )

    # Validate location
    location_id = request.location_id or "town_square"
    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Location '{location_id}' not found"
        )

    # Generate unique ID
    agent_id = _generate_agent_id(request.name, db)

    # Create the agent
    now = time.time()
    agent = Agent(
        id=agent_id,
        name=request.name,
        personality_prompt=request.personality_prompt,
        traits=json.dumps(traits.model_dump()),
        location_id=location_id,
        inventory=json.dumps([]),
        mood=json.dumps({"happiness": 5, "energy": 7}),
        state="idle",
        hunger=0.0,
        energy=10.0,
        social=5.0,
        creator_id=current_user.id,
        created_at=now,
        is_user_created=True,
    )

    db.add(agent)

    # Update quota
    quota.agents_created += 1
    quota.last_creation_at = now

    db.commit()
    db.refresh(agent)

    return AgentCreateResponse(
        id=agent.id,
        name=agent.name,
        personality_prompt=agent.personality_prompt,
        traits=agent.traits_dict,
        location_id=agent.location_id,
        mood=agent.mood_dict,
        state=agent.state,
        creator_id=agent.creator_id,
        created_at=agent.created_at,
        is_user_created=agent.is_user_created,
    )


# Dynamic routes (/{agent_id} pattern)


@router.get("", response_model=list[AgentResponse])
async def list_agents(db: Session = Depends(get_db)):
    """List all agents."""
    agents = db.query(Agent).all()
    return [_agent_to_response(a) for a in agents]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get a specific agent by ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    return _agent_to_response(agent)


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete an agent. Users can only delete agents they created."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' not found"
        )

    # Prevent deletion of system agents (check first)
    if not agent.is_user_created:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system agents"
        )

    # Check ownership (admins can delete any user-created agent)
    if agent.creator_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete agents you created"
        )

    # Update quota
    if agent.creator_id:
        quota = db.query(UserAgentQuota).filter(
            UserAgentQuota.user_id == agent.creator_id
        ).first()
        if quota and quota.agents_created > 0:
            quota.agents_created -= 1

    db.delete(agent)
    db.commit()


@router.get("/{agent_id}/memory")
async def get_agent_memory(agent_id: str, db: Session = Depends(get_db)):
    """Get an agent's memories."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    memories = get_all_memories(agent_id, db)

    return {
        "agent_id": agent_id,
        "working": [_memory_to_response(m) for m in memories.get("working", [])],
        "recent": [_memory_to_response(m) for m in memories.get("recent", [])],
        "longterm": [_memory_to_response(m) for m in memories.get("longterm", [])],
        "context": build_memory_context(agent_id, db),
    }


def _agent_to_response(agent: Agent) -> AgentResponse:
    """Convert Agent model to response schema."""
    return AgentResponse(
        id=agent.id,
        name=agent.name,
        personality_prompt=agent.personality_prompt,
        traits=agent.traits_dict,
        location_id=agent.location_id,
        inventory=agent.inventory_list,
        mood=agent.mood_dict,
        state=agent.state,
        hunger=agent.hunger,
        energy=agent.energy,
        social=agent.social,
    )


def _memory_to_response(memory: Memory) -> MemoryResponse:
    """Convert Memory model to response schema."""
    return MemoryResponse(
        id=memory.id,
        agent_id=memory.agent_id,
        timestamp=memory.timestamp,
        type=memory.type,
        content=memory.content,
        significance=memory.significance,
        compressed=memory.compressed,
    )
