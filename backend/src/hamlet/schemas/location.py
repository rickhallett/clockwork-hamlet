"""Location schemas."""

from pydantic import BaseModel


class LocationBase(BaseModel):
    """Base location schema."""

    name: str
    description: str | None = None
    connections: list[str] = []
    objects: list[str] = []
    capacity: int = 10


class LocationCreate(LocationBase):
    """Schema for creating a location."""

    id: str


class LocationResponse(BaseModel):
    """Schema for location response."""

    id: str
    name: str
    description: str | None
    connections: list[str]
    objects: list[str]
    capacity: int
    agent_count: int = 0

    class Config:
        from_attributes = True
