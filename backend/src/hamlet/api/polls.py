"""Poll API routes."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.db import Poll
from hamlet.schemas.poll import PollResponse

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
    db: Session = Depends(get_db),
):
    """List all polls, optionally filtered by status."""
    query = db.query(Poll)
    if status:
        query = query.filter(Poll.status == status)
    polls = query.order_by(Poll.created_at.desc()).all()
    return [_poll_to_response(p) for p in polls]


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
    )
