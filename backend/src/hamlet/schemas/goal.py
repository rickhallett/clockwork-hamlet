"""Goal schemas."""

from pydantic import BaseModel, Field


class GoalBase(BaseModel):
    """Base goal schema."""

    type: str
    description: str | None = None
    priority: int = Field(default=5, ge=1, le=10)
    target_id: str | None = None


class GoalCreate(GoalBase):
    """Schema for creating a goal."""

    agent_id: str
    created_at: int


class GoalResponse(BaseModel):
    """Schema for goal response."""

    id: int
    agent_id: str
    type: str
    description: str | None
    priority: int
    target_id: str | None
    status: str
    created_at: int

    class Config:
        from_attributes = True
