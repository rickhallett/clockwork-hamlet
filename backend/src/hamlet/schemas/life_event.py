"""Life event schemas."""

from pydantic import BaseModel, ConfigDict


class LifeEventResponse(BaseModel):
    """Schema for life event response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    primary_agent_id: str
    primary_agent_name: str | None = None
    secondary_agent_id: str | None
    secondary_agent_name: str | None = None
    description: str
    significance: int
    status: str
    related_agents: list[str]
    effects: dict
    timestamp: float
    resolved_at: float | None


class LifeEventCreate(BaseModel):
    """Schema for creating a life event manually."""

    type: str
    primary_agent_id: str
    secondary_agent_id: str | None = None
    description: str | None = None
    significance: int = 7


class LifeEventSummaryResponse(BaseModel):
    """Summary of life events."""

    total_events: int
    active_events: int
    events_by_type: dict[str, int]
    recent_events: list[LifeEventResponse]
