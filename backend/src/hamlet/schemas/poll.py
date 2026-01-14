"""Poll schemas."""

from pydantic import BaseModel, ConfigDict


class PollBase(BaseModel):
    """Base poll schema."""

    question: str
    options: list[str]


class PollCreate(PollBase):
    """Schema for creating a poll."""

    closes_at: int | None = None


class PollResponse(BaseModel):
    """Schema for poll response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    question: str
    options: list[str]
    votes: dict[str, int]
    status: str
    created_at: int
    closes_at: int | None


class VoteRequest(BaseModel):
    """Schema for submitting a vote."""

    poll_id: int
    option_index: int
