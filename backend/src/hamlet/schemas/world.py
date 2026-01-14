"""World state schemas."""

from pydantic import BaseModel, ConfigDict


class WorldStateResponse(BaseModel):
    """Schema for world state response."""

    model_config = ConfigDict(from_attributes=True)

    current_tick: int
    current_day: int
    current_hour: float
    season: str
    weather: str
    agent_count: int
    location_count: int
