"""Poll API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Agent, Poll
from hamlet.schemas.poll import PollResponse
from hamlet.simulation.polls import (
    decide_vote,
    get_voting_summary,
    process_agent_votes,
)

router = APIRouter(prefix="/api/polls", tags=["polls"])


class VoteRequest(BaseModel):
    """Vote request body."""

    poll_id: int
    option: int  # Index of the option


@router.get("/active", response_model=PollResponse | None)
async def get_active_poll(db: Session = Depends(get_db)):
    """Get the currently active poll."""
    poll = db.query(Poll).filter(Poll.status == "active").first()

    if not poll:
        return None

    return _poll_to_response(poll)


@router.get("/{poll_id}", response_model=PollResponse)
async def get_poll(poll_id: int, db: Session = Depends(get_db)):
    """Get a specific poll by ID."""
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")
    return _poll_to_response(poll)


@router.post("/vote")
async def submit_vote(vote: VoteRequest, db: Session = Depends(get_db)):
    """Submit a vote for a poll option."""
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


@router.get("", response_model=list[PollResponse])
async def list_polls(
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
):
    """List all polls, optionally filtered by status and/or category."""
    query = db.query(Poll)
    if status:
        query = query.filter(Poll.status == status)
    if category:
        query = query.filter(Poll.category == category)
    polls = query.order_by(Poll.created_at.desc()).all()
    return [_poll_to_response(p) for p in polls]


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
    """
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
    db.commit()

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
    """
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail=f"Poll {poll_id} not found")

    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")

    # Process all agent votes
    decisions = process_agent_votes(db, poll)
    summary = get_voting_summary(decisions)

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
        closes_at=poll.closes_at,
        category=poll.category,
        tags=poll.tags_list,
    )
