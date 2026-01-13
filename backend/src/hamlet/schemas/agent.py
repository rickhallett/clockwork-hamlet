"""Agent schemas."""

from pydantic import BaseModel, Field


class TraitsSchema(BaseModel):
    """Agent personality traits."""

    curiosity: int = Field(default=5, ge=1, le=10)
    empathy: int = Field(default=5, ge=1, le=10)
    ambition: int = Field(default=5, ge=1, le=10)
    discretion: int = Field(default=5, ge=1, le=10)
    energy: int = Field(default=5, ge=1, le=10)
    courage: int = Field(default=5, ge=1, le=10)
    charm: int = Field(default=5, ge=1, le=10)
    perception: int = Field(default=5, ge=1, le=10)


class MoodSchema(BaseModel):
    """Agent mood state."""

    happiness: int = Field(default=5, ge=0, le=10)
    energy: int = Field(default=7, ge=0, le=10)


class AgentBase(BaseModel):
    """Base agent schema."""

    name: str
    personality_prompt: str | None = None
    traits: TraitsSchema = Field(default_factory=TraitsSchema)


class AgentCreate(AgentBase):
    """Schema for creating an agent."""

    id: str
    location_id: str | None = None


class AgentResponse(BaseModel):
    """Schema for agent list response."""

    id: str
    name: str
    location_id: str | None
    state: str
    mood: MoodSchema

    class Config:
        from_attributes = True


class AgentDetail(BaseModel):
    """Schema for detailed agent response."""

    id: str
    name: str
    personality_prompt: str | None
    traits: TraitsSchema
    location_id: str | None
    inventory: list[str]
    mood: MoodSchema
    state: str
    hunger: float
    energy: float
    social: float

    class Config:
        from_attributes = True
