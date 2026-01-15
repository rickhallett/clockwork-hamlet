"""Faction schemas."""

from pydantic import BaseModel, ConfigDict, Field


class FactionBase(BaseModel):
    """Base faction schema."""

    name: str
    description: str | None = None


class FactionCreate(FactionBase):
    """Schema for creating a faction."""

    founder_id: str
    location_id: str | None = None
    beliefs: list[str] = []
    goals: list[str] = []


class FactionResponse(BaseModel):
    """Schema for faction response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    founder_id: str | None
    founder_name: str | None = None
    location_id: str | None
    location_name: str | None = None
    beliefs: list[str]
    goals: list[str]
    treasury: float
    reputation: int
    status: str
    member_count: int = 0
    created_at: float


class FactionMemberResponse(BaseModel):
    """Schema for faction member response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    faction_id: int
    agent_id: str
    agent_name: str | None = None
    role: str
    loyalty: int
    contributions: float
    joined_at: float
    left_at: float | None


class FactionRelationshipResponse(BaseModel):
    """Schema for faction relationship response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    faction_1_id: int
    faction_1_name: str | None = None
    faction_2_id: int
    faction_2_name: str | None = None
    type: str
    score: int
    history: list[str]


class FactionSummaryResponse(BaseModel):
    """Summary of all factions."""

    total_factions: int
    active_factions: int
    total_members: int
    factions: list[FactionResponse]
