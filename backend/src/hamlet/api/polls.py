"""Poll API routes.

POLL-8: Poll results trigger reactive goals (via poll_integration)
POLL-10: Memory creation for votes (via poll_integration)
"""

import asyncio
import logging
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Poll
from hamlet.schemas.poll import MultiVoteRequest, PollCreate, PollResponse
from hamlet.simulation.poll_integration import on_poll_closed
from hamlet.simulation.polls import (
    decide_vote,
    get_voting_summary,
    process_agent_votes,
)

router = APIRouter(prefix="/api/polls", tags=["polls"])
logger = logging.getLogger(__name__)

# Store agent votes for recently closed polls to enable poll integration
# In production, this would be stored in the database
_recent_poll_votes: dict[int, dict[str, int]] = {}


class VoteRequest(BaseModel):
    """Vote request body."""

    poll_id: int
    option: int  # Index of the option


async def process_poll_schedules_async(db: Session) -> dict:
    """Process poll schedules - open scheduled polls and close expired ones.

    POLL-8/POLL-10: When polls close, triggers integration to create
    memories and reactive goals for agents.

    Returns a summary of changes made.
    """
    now = int(time.time())
    opened = []
    closed = []
    closed_polls = []

    # Open scheduled polls whose opens_at time has passed
    scheduled_polls = db.query(Poll).filter(Poll.status == "scheduled").all()
    for poll in scheduled_polls:
        if poll.opens_at and poll.opens_at <= now:
            poll.status = "active"
            opened.append(poll.id)

    # Close active polls whose closes_at time has passed
    active_polls = db.query(Poll).filter(Poll.status == "active").all()
    for poll in active_polls:
        if poll.closes_at and poll.closes_at <= now:
            poll.status = "closed"
            closed.append(poll.id)
            closed_polls.append(poll)

    if opened or closed:
        db.commit()

    # POLL-8/POLL-10: Process poll closures
    for poll in closed_polls:
        try:
            # Get cached agent votes if available
            agent_votes = _recent_poll_votes.pop(poll.id, {})
            await on_poll_closed(poll, db, agent_votes)
            logger.info(f"Processed poll closure integration for poll {poll.id}")
        except Exception as e:
            logger.error(f"Failed to process poll closure for {poll.id}: {e}")

    return {"opened": opened, "closed": closed}


def process_poll_schedules(db: Session) -> dict:
    """Synchronous wrapper for process_poll_schedules_async.

    For use in contexts where async is not available.
    """
    try:
        loop = asyncio.get_running_loop()
        # We're in an async context, create a task
        # This won't work directly - need to return and let caller await
        # For sync contexts, we'll use asyncio.run
    except RuntimeError:
        # No running loop - use asyncio.run
        return asyncio.run(process_poll_schedules_async(db))

    # If we're here, there's a running loop but we're called synchronously
    # This shouldn't happen in FastAPI async endpoints
    # Fall back to basic sync processing without integration
    now = int(time.time())
    opened = []
    closed = []

    scheduled_polls = db.query(Poll).filter(Poll.status == "scheduled").all()
    for poll in scheduled_polls:
        if poll.opens_at and poll.opens_at <= now:
            poll.status = "active"
            opened.append(poll.id)

    active_polls = db.query(Poll).filter(Poll.status == "active").all()
    for poll in active_polls:
        if poll.closes_at and poll.closes_at <= now:
            poll.status = "closed"
            closed.append(poll.id)

    if opened or closed:
        db.commit()

    return {"opened": opened, "closed": closed}


@router.get("/active", response_model=PollResponse | None)
async def get_active_poll(db: Session = Depends(get_db)):
    """Get the currently active poll.

    Automatically processes scheduled polls before returning.
    POLL-8/POLL-10: Poll closure triggers memories and goals.
    """
    # Process any pending schedule changes (async for full integration)
    await process_poll_schedules_async(db)

    poll = db.query(Poll).filter(Poll.status == "active").first()

    if not poll:
        return None

    return _poll_to_response(poll)


@router.post("/process-schedules")
async def trigger_schedule_processing(db: Session = Depends(get_db)):
    """Manually trigger poll schedule processing.

    Opens scheduled polls whose opens_at time has passed.
    Closes active polls whose closes_at time has passed.
    POLL-8/POLL-10: Poll closure triggers memories and goals.
    """
    result = await process_poll_schedules_async(db)
    return {
        "success": True,
        "polls_opened": result["opened"],
        "polls_closed": result["closed"],
    }


@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(poll_id: int, db: Session = Depends(get_db)):
    """Get a specific poll by ID."""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")
    return _poll_to_response(poll)


@router.post("/vote")
async def submit_vote(vote: VoteRequest, db: Session = Depends(get_db)):
    """Submit a vote for a poll option (single choice)."""
    poll = db.query(Poll).filter(Poll.id == vote.poll_id).first()

    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {vote.poll_id} not found")

    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")

    options = poll.options_list
    if vote.option < 0 or vote.option >= len(options):
        raise HTTPException(status_code=400, detail=f"Invalid option. Must be 0-{len(options) - 1}")

    # Update vote count
    votes = poll.votes_dict
    option_key = str(vote.option)
    votes[option_key] = votes.get(option_key, 0) + 1
    poll.votes_dict = votes

    db.commit()

    return {
        "success": True,
        "poll_id": poll.id,
        "option": vote.option,
        "option_text": options[vote.option],
        "new_count": votes[option_key],
    }


@router.post("/vote-multiple")
async def submit_multiple_votes(vote: MultiVoteRequest, db: Session = Depends(get_db)):
    """Submit votes for multiple poll options.

    Only works for polls with allow_multiple=True.
    """
    poll = db.query(Poll).filter(Poll.id == vote.poll_id).first()

    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {vote.poll_id} not found")

    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")

    if not poll.allow_multiple:
        raise HTTPException(
            status_code=400,
            detail="This poll does not allow multiple selections. Use /vote endpoint instead.",
        )

    if not vote.option_indices:
        raise HTTPException(status_code=400, detail="Must select at least one option")

    options = poll.options_list
    # Validate all option indices
    for idx in vote.option_indices:
        if idx < 0 or idx >= len(options):
            raise HTTPException(status_code=400, detail=f"Invalid option {idx}. Must be 0-{len(options) - 1}")

    # Check for duplicates
    if len(vote.option_indices) != len(set(vote.option_indices)):
        raise HTTPException(status_code=400, detail="Duplicate options not allowed")

    # Update vote counts for all selected options
    votes = poll.votes_dict
    updated = []
    for idx in vote.option_indices:
        option_key = str(idx)
        votes[option_key] = votes.get(option_key, 0) + 1
        updated.append({
            "option": idx,
            "option_text": options[idx],
            "new_count": votes[option_key],
        })
    poll.votes_dict = votes

    db.commit()

    return {
        "success": True,
        "poll_id": poll.id,
        "votes_cast": len(vote.option_indices),
        "options": updated,
    }


@router.get("", response_model=list[PollResponse])
async def list_polls(
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """List all polls, optionally filtered by status and/or category.

    POLL-8/POLL-10: Poll closure triggers memories and goals.
    """
    # Process schedules to ensure accurate status (async for full integration)
    await process_poll_schedules_async(db)

    query = db.query(Poll)
    if status:
        query = query.filter(Poll.status == status)
    if category:
        query = query.filter(Poll.category == category)
    polls = query.order_by(Poll.created_at.desc()).all()
    return [_poll_to_response(p) for p in polls]


@router.post("", response_model=PollResponse, status_code=201)
async def create_poll(poll_data: PollCreate, db: Session = Depends(get_db)):
    """Create a new poll (admin endpoint).

    If opens_at is provided and in the future, poll starts as 'scheduled'.
    Otherwise, poll starts as 'active'.
    """
    if len(poll_data.options) < 2:
        raise HTTPException(status_code=400, detail="Poll must have at least 2 options")

    if len(poll_data.options) > 10:
        raise HTTPException(status_code=400, detail="Poll cannot have more than 10 options")

    now = int(time.time())

    # Determine initial status based on opens_at
    if poll_data.opens_at and poll_data.opens_at > now:
        status = "scheduled"
    else:
        status = "active"

    poll = Poll(
        question=poll_data.question,
        created_at=now,
        opens_at=poll_data.opens_at,
        closes_at=poll_data.closes_at,
        allow_multiple=poll_data.allow_multiple,
        category=poll_data.category,
        status=status,
    )
    poll.options_list = poll_data.options
    poll.votes_dict = {}
    poll.tags_list = poll_data.tags

    db.add(poll)
    db.commit()
    db.refresh(poll)

    return _poll_to_response(poll)


class AgentVoteRequest(BaseModel):
    """Request for a specific agent to vote."""

    agent_id: str


class AgentVoteResponse(BaseModel):
    """Response for an agent's vote."""

    agent_id: str
    poll_id: int
    option_index: int
    option_text: str
    confidence: float


class AgentVotingResponse(BaseModel):
    """Response for bulk agent voting."""

    poll_id: int
    total_votes: int
    votes: list[AgentVoteResponse]
    summary: dict


@router.post("/{poll_id}/agent-vote", response_model=AgentVoteResponse)
async def agent_vote(
    poll_id: int,
    request: AgentVoteRequest,
    db: Session = Depends(get_db),
):
    """Have a specific agent vote on a poll based on their personality traits.

    The agent's vote is determined probabilistically based on their personality
    traits and the poll options. Different traits influence voting differently
    depending on the poll category and option keywords.

    POLL-10: Creates a memory for the agent about their vote.
    """
    from hamlet.simulation.poll_integration import on_agent_vote

    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")

    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")

    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {request.agent_id} not found")

    # Get the agent's vote decision
    decision = decide_vote(agent, poll)

    # Record the vote
    votes = poll.votes_dict
    option_key = str(decision.option_index)
    votes[option_key] = votes.get(option_key, 0) + 1
    poll.votes_dict = votes

    # Cache vote for poll closure integration
    if poll_id not in _recent_poll_votes:
        _recent_poll_votes[poll_id] = {}
    _recent_poll_votes[poll_id][agent.id] = decision.option_index

    db.commit()

    # POLL-10: Create memory and publish event
    await on_agent_vote(agent, decision, poll, db)

    return AgentVoteResponse(
        agent_id=decision.agent_id,
        poll_id=decision.poll_id,
        option_index=decision.option_index,
        option_text=decision.option_text,
        confidence=decision.confidence,
    )


@router.post("/{poll_id}/agent-voting", response_model=AgentVotingResponse)
async def bulk_agent_voting(
    poll_id: int,
    db: Session = Depends(get_db),
):
    """Have all agents vote on a poll based on their personality traits.

    Each agent's vote is determined probabilistically based on their personality
    traits and the poll options. This endpoint processes all agents at once
    and returns a summary of voting patterns.

    POLL-10: Creates memories for each agent about their vote.
    """
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")

    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")

    # Process all agent votes (POLL-10: creates memories via create_memories=True)
    decisions, agent_votes = process_agent_votes(db, poll, create_memories=True)
    summary = get_voting_summary(decisions)

    # Cache votes for poll closure integration
    _recent_poll_votes[poll_id] = agent_votes

    return AgentVotingResponse(
        poll_id=poll_id,
        total_votes=len(decisions),
        votes=[
            AgentVoteResponse(
                agent_id=d.agent_id,
                poll_id=d.poll_id,
                option_index=d.option_index,
                option_text=d.option_text,
                confidence=d.confidence,
            )
            for d in decisions
        ],
        summary=summary,
    )


def _poll_to_response(poll: Poll) -> PollResponse:
    """Convert Poll model to response schema."""
    return PollResponse(
        id=poll.id,
        question=poll.question,
        options=poll.options_list,
        votes=poll.votes_dict,
        status=poll.status,
        created_at=poll.created_at,
        opens_at=poll.opens_at,
        closes_at=poll.closes_at,
        category=poll.category,
        tags=poll.tags_list,
        allow_multiple=poll.allow_multiple,
    )
