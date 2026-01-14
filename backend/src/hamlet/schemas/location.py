"""Location schemas."""

from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None
    connections: list[str]
    objects: list[str]
    capacity: int
    agents_present: list[str] = []
