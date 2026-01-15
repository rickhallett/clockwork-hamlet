"""Narrative arc schemas."""

from pydantic import BaseModel, ConfigDict


class ActResponse(BaseModel):
    """Schema for an act within a narrative arc."""

    number: int
    name: str
    status: str
    events: list[int]
    key_moments: list[str]
    turning_point: str | None


class NarrativeArcResponse(BaseModel):
    """Schema for narrative arc response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str | None
    primary_agent_id: str
    primary_agent_name: str | None = None
    secondary_agent_id: str | None
    secondary_agent_name: str | None = None
    theme: str | None
    acts: list[ActResponse]
    current_act: int
    current_act_name: str | None = None
    status: str
    significance: int
    discovered_at: float
    completed_at: float | None


class ArcEventResponse(BaseModel):
    """Schema for an event within an arc."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    arc_id: int
    event_id: int
    act_number: int
    is_turning_point: bool
    notes: str | None
    event_summary: str | None = None
    event_timestamp: float | None = None


class ArcTimelineResponse(BaseModel):
    """Timeline of events in an arc."""

    arc_id: int
    arc_title: str | None
    timeline: list[dict]


class NarrativeArcSummaryResponse(BaseModel):
    """Summary of narrative arcs."""

    total_arcs: int
    active_arcs: int
    completed_arcs: int
    abandoned_arcs: int
    arcs_by_type: dict[str, int]
    most_dramatic: NarrativeArcResponse | None
    narrative_intensity: str


class StoryDigestResponse(BaseModel):
    """Story digest response."""

    title: str
    summary: str
    active_arcs: list[dict]
    completed_arcs: list[dict]
    notable_moments: list[str]
    suggested_focus: str | None
    village_state: dict
