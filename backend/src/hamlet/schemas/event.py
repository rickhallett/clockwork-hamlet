"""Event schemas."""

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    """Base event schema."""

    type: str
    summary: str
    detail: str | None = None
    significance: int = Field(default=1, ge=1, le=3)


class EventCreate(EventBase):
    """Schema for creating an event."""

    timestamp: int
    actors: list[str] = []
    location_id: str | None = None


class EventResponse(BaseModel):
    """Schema for event response."""

    id: int
    timestamp: int
    type: str
    actors: list[str]
    location_id: str | None
    summary: str
    detail: str | None
    significance: int

    class Config:
        from_attributes = True
