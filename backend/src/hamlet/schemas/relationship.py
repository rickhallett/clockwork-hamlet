"""Relationship schemas."""

from pydantic import BaseModel, Field


class RelationshipBase(BaseModel):
    """Base relationship schema."""

    type: str = "stranger"
    score: int = Field(default=0, ge=-10, le=10)


class RelationshipCreate(RelationshipBase):
    """Schema for creating a relationship."""

    agent_id: str
    target_id: str


class RelationshipResponse(BaseModel):
    """Schema for relationship response."""

    id: int
    agent_id: str
    agent_name: str | None = None
    target_id: str
    target_name: str | None = None
    type: str
    score: int
    history: list[str]

    class Config:
        from_attributes = True


class RelationshipGraphNode(BaseModel):
    """Node in the relationship graph."""

    id: str
    name: str


class RelationshipGraphEdge(BaseModel):
    """Edge in the relationship graph."""

    source: str
    target: str
    type: str
    score: int


class RelationshipGraphResponse(BaseModel):
    """Full relationship graph response."""

    nodes: list[RelationshipGraphNode]
    edges: list[RelationshipGraphEdge]
