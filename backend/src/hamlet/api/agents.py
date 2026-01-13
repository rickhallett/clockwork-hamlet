"""Agent API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Memory
from hamlet.memory import build_memory_context, get_all_memories
from hamlet.schemas.agent import AgentResponse
from hamlet.schemas.memory import MemoryResponse

router = APIRouter(prefix="/api/agents", tags=["agents"])


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
