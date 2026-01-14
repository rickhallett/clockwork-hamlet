"""Event schemas."""

from pydantic import BaseModel, ConfigDict, Field


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

    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: int
    type: str
    actors: list[str]
    location_id: str | None
    summary: str
    detail: str | None
    significance: int


class EventPage(BaseModel):
    """Paginated event response with cursor-based pagination.

    Cursor-based pagination is more efficient than offset-based for large datasets:
    - Consistent results even when new events are added
    - O(1) query performance regardless of page depth
    - Suitable for infinite scroll implementations
    """

    events: list[EventResponse]
    next_cursor: int | None = Field(
        default=None,
        description="Cursor for fetching the next page. None if no more results.",
    )
    has_more: bool = Field(
        default=False,
        description="Whether there are more events after this page.",
    )
    total_count: int | None = Field(
        default=None,
        description="Total count of events matching filters (optional, may be omitted for performance).",
    )
