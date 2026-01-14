"""Stats schemas for dashboard aggregation endpoints."""

from pydantic import BaseModel, Field


class AgentStateDistribution(BaseModel):
    """Distribution of agents by state."""

    idle: int = 0
    busy: int = 0
    sleeping: int = 0


class MoodAverages(BaseModel):
    """Average mood values across all agents."""

    happiness: float = Field(default=0.0, description="Average happiness (0-10)")
    energy: float = Field(default=0.0, description="Average energy (0-10)")


class NeedsAverages(BaseModel):
    """Average needs values across all agents."""

    hunger: float = Field(default=0.0, description="Average hunger (0-10)")
    energy: float = Field(default=0.0, description="Average energy (0-10)")
    social: float = Field(default=0.0, description="Average social need (0-10)")


class AgentStatsResponse(BaseModel):
    """Response for /api/stats/agents endpoint.

    Implements DASH-9: Count, state distribution, mood averages.
    """

    total_count: int = Field(description="Total number of agents")
    state_distribution: AgentStateDistribution = Field(
        description="Distribution of agents by state"
    )
    mood_averages: MoodAverages = Field(description="Average mood across all agents")
    needs_averages: NeedsAverages = Field(description="Average needs across all agents")


class EventTypeCount(BaseModel):
    """Count of events by type."""

    type: str
    count: int


class SignificanceLevelCount(BaseModel):
    """Count of events by significance level."""

    level: int = Field(ge=1, le=3)
    count: int


class EventStatsResponse(BaseModel):
    """Response for /api/stats/events endpoint.

    Implements DASH-10: Counts by type and significance level.
    """

    total_count: int = Field(description="Total number of events")
    by_type: list[EventTypeCount] = Field(description="Event counts by type")
    by_significance: list[SignificanceLevelCount] = Field(
        description="Event counts by significance level"
    )
    recent_count: int = Field(
        description="Number of events in the last hour (simulation time)"
    )


class RelationshipTypeCount(BaseModel):
    """Count of relationships by type."""

    type: str
    count: int


class RelationshipStatsResponse(BaseModel):
    """Response for /api/stats/relationships endpoint.

    Implements DASH-11: Network metrics, clustering, density.
    """

    total_count: int = Field(description="Total number of relationships")
    by_type: list[RelationshipTypeCount] = Field(description="Relationship counts by type")
    average_score: float = Field(description="Average relationship score (-10 to +10)")
    positive_count: int = Field(description="Number of positive relationships (score > 0)")
    negative_count: int = Field(description="Number of negative relationships (score < 0)")
    neutral_count: int = Field(description="Number of neutral relationships (score = 0)")
    network_density: float = Field(
        description="Network density: actual edges / possible edges (0-1)"
    )
    average_connections_per_agent: float = Field(
        description="Average number of relationships per agent"
    )


class SimulationStatsResponse(BaseModel):
    """Response for /api/stats/simulation endpoint.

    Implements DASH-12: Tick rate, performance metrics, health.
    """

    current_tick: int = Field(description="Current simulation tick")
    current_day: int = Field(description="Current simulation day")
    current_hour: float = Field(description="Current simulation hour (0-24)")
    season: str = Field(description="Current season")
    weather: str = Field(description="Current weather")
    is_running: bool = Field(description="Whether simulation is currently running")
    tick_interval_seconds: float = Field(description="Configured tick interval")
    events_per_tick: float = Field(
        description="Average number of events generated per tick"
    )
    uptime_ticks: int = Field(
        description="Total ticks since simulation started (same as current_tick)"
    )
