"""Memory schemas."""

from pydantic import BaseModel, ConfigDict, Field


class MemoryBase(BaseModel):
    """Base memory schema."""

    content: str
    type: str = "working"
    significance: int = Field(default=5, ge=1, le=10)


class MemoryCreate(MemoryBase):
    """Schema for creating a memory."""

    agent_id: str
    timestamp: int


class MemoryResponse(BaseModel):
    """Schema for memory response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    agent_id: str
    timestamp: int
    type: str
    content: str
    significance: int
    compressed: bool
