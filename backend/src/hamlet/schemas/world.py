"""World state schemas."""

from pydantic import BaseModel


class WorldStateResponse(BaseModel):
    """Schema for world state response."""

    current_tick: int
    current_day: int
    current_hour: float
    season: str
    weather: str
    agent_count: int
    location_count: int

    class Config:
        from_attributes = True
