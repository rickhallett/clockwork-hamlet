"""Stats API routes for dashboard aggregation.

Implements DASH-3 story tasks:
- DASH-9: /api/stats/agents - Count, state distribution, mood averages
- DASH-10: /api/stats/events - Counts by type and significance level
- DASH-11: /api/stats/relationships - Network metrics, clustering, density
- DASH-12: /api/stats/simulation - Tick rate, performance metrics, health
- DASH-15: Enhanced simulation health with queue depth, tick rate, error count
"""

import time

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.config import settings
from hamlet.db import Agent, Event, Relationship, WorldState
from hamlet.simulation.events import event_bus

router = APIRouter(prefix="/api/stats", tags=["stats"])


# Response schemas
class AgentStateDistribution(BaseModel):
    idle: int = 0
    busy: int = 0
    sleeping: int = 0


class MoodAverages(BaseModel):
    happiness: float = 0.0
    energy: float = 0.0


class NeedsAverages(BaseModel):
    hunger: float = 0.0
    energy: float = 0.0
    social: float = 0.0


class AgentStatsResponse(BaseModel):
    total_count: int
    state_distribution: AgentStateDistribution
    mood_averages: MoodAverages
    needs_averages: NeedsAverages


class EventTypeCount(BaseModel):
    type: str
    count: int


class SignificanceLevelCount(BaseModel):
    level: int
    count: int


class EventStatsResponse(BaseModel):
    total_count: int
    by_type: list[EventTypeCount]
    by_significance: list[SignificanceLevelCount]
    recent_count: int


class RelationshipTypeCount(BaseModel):
    type: str
    count: int


class RelationshipStatsResponse(BaseModel):
    total_count: int
    by_type: list[RelationshipTypeCount]
    average_score: float
    positive_count: int
    negative_count: int
    neutral_count: int
    network_density: float
    average_connections_per_agent: float


class SimulationHealthResponse(BaseModel):
    """Enhanced simulation health metrics for DASH-15."""

    # Basic state
    current_tick: int = Field(description="Current simulation tick")
    current_day: int = Field(description="Current simulation day")
    current_hour: float = Field(description="Current simulation hour (0-24)")
    season: str = Field(description="Current season")
    weather: str = Field(description="Current weather")

    # Health indicators (DASH-15)
    is_running: bool = Field(description="Whether simulation is currently running")
    queue_depth: int = Field(description="Number of subscribers to event bus")
    tick_rate: float = Field(description="Configured ticks per minute")
    events_per_tick: float = Field(description="Average events generated per tick")
    uptime_ticks: int = Field(description="Total ticks since simulation started")

    # Performance
    tick_interval_seconds: float = Field(description="Configured tick interval")


@router.get("/agents", response_model=AgentStatsResponse)
async def get_agent_stats(db: Session = Depends(get_db)) -> AgentStatsResponse:
    """Get aggregated agent statistics (DASH-9)."""
    agents = db.query(Agent).all()
    total_count = len(agents)

    if total_count == 0:
        return AgentStatsResponse(
            total_count=0,
            state_distribution=AgentStateDistribution(),
            mood_averages=MoodAverages(),
            needs_averages=NeedsAverages(),
        )

    state_counts = {"idle": 0, "busy": 0, "sleeping": 0}
    for agent in agents:
        state = agent.state or "idle"
        if state in state_counts:
            state_counts[state] += 1
        else:
            state_counts["idle"] += 1

    total_happiness = 0.0
    total_mood_energy = 0.0
    for agent in agents:
        mood = agent.mood_dict
        total_happiness += mood.get("happiness", 0)
        total_mood_energy += mood.get("energy", 0)

    total_hunger = sum(agent.hunger or 0 for agent in agents)
    total_energy = sum(agent.energy or 0 for agent in agents)
    total_social = sum(agent.social or 0 for agent in agents)

    return AgentStatsResponse(
        total_count=total_count,
        state_distribution=AgentStateDistribution(
            idle=state_counts["idle"],
            busy=state_counts["busy"],
            sleeping=state_counts["sleeping"],
        ),
        mood_averages=MoodAverages(
            happiness=round(total_happiness / total_count, 2),
            energy=round(total_mood_energy / total_count, 2),
        ),
        needs_averages=NeedsAverages(
            hunger=round(total_hunger / total_count, 2),
            energy=round(total_energy / total_count, 2),
            social=round(total_social / total_count, 2),
        ),
    )


@router.get("/events", response_model=EventStatsResponse)
async def get_event_stats(db: Session = Depends(get_db)) -> EventStatsResponse:
    """Get aggregated event statistics (DASH-10)."""
    total_count = db.query(func.count(Event.id)).scalar() or 0

    type_counts = (
        db.query(Event.type, func.count(Event.id)).group_by(Event.type).all()
    )
    by_type = [EventTypeCount(type=t, count=c) for t, c in type_counts]

    sig_counts = (
        db.query(Event.significance, func.count(Event.id))
        .group_by(Event.significance)
        .all()
    )
    by_significance = [
        SignificanceLevelCount(level=s, count=c)
        for s, c in sig_counts
        if s is not None
    ]

    current_time = int(time.time())
    one_hour_ago = current_time - 3600
    recent_count = (
        db.query(func.count(Event.id))
        .filter(Event.timestamp >= one_hour_ago)
        .scalar()
        or 0
    )

    return EventStatsResponse(
        total_count=total_count,
        by_type=by_type,
        by_significance=by_significance,
        recent_count=recent_count,
    )


@router.get("/relationships", response_model=RelationshipStatsResponse)
async def get_relationship_stats(
    db: Session = Depends(get_db),
) -> RelationshipStatsResponse:
    """Get aggregated relationship statistics (DASH-11)."""
    relationships = db.query(Relationship).all()
    total_count = len(relationships)
    agent_count = db.query(func.count(Agent.id)).scalar() or 0

    if total_count == 0:
        return RelationshipStatsResponse(
            total_count=0,
            by_type=[],
            average_score=0.0,
            positive_count=0,
            negative_count=0,
            neutral_count=0,
            network_density=0.0,
            average_connections_per_agent=0.0,
        )

    type_counts: dict[str, int] = {}
    total_score = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for rel in relationships:
        rel_type = rel.type or "unknown"
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1
        score = rel.score or 0
        total_score += score
        if score > 0:
            positive_count += 1
        elif score < 0:
            negative_count += 1
        else:
            neutral_count += 1

    by_type = [
        RelationshipTypeCount(type=t, count=c) for t, c in type_counts.items()
    ]

    if agent_count > 1:
        max_possible_edges = agent_count * (agent_count - 1)
        network_density = total_count / max_possible_edges
    else:
        network_density = 0.0

    avg_connections = total_count / agent_count if agent_count > 0 else 0.0

    return RelationshipStatsResponse(
        total_count=total_count,
        by_type=by_type,
        average_score=round(total_score / total_count, 2),
        positive_count=positive_count,
        negative_count=negative_count,
        neutral_count=neutral_count,
        network_density=round(network_density, 4),
        average_connections_per_agent=round(avg_connections, 2),
    )


@router.get("/simulation", response_model=SimulationHealthResponse)
async def get_simulation_stats(
    db: Session = Depends(get_db),
) -> SimulationHealthResponse:
    """Get simulation status and health metrics (DASH-12 + DASH-15)."""
    world_state = db.query(WorldState).first()

    if not world_state:
        current_tick = 0
        current_day = 1
        current_hour = 6.0
        season = "spring"
        weather = "clear"
    else:
        current_tick = world_state.current_tick
        current_day = world_state.current_day
        current_hour = world_state.current_hour
        season = world_state.season
        weather = world_state.weather

    total_events = db.query(func.count(Event.id)).scalar() or 0
    events_per_tick = total_events / current_tick if current_tick > 0 else 0.0

    # Queue depth is the number of active SSE subscribers
    queue_depth = len(event_bus._subscribers)

    # Tick rate in ticks per minute
    tick_rate = 60.0 / settings.tick_interval_seconds if settings.tick_interval_seconds > 0 else 0.0

    is_running = world_state is not None

    return SimulationHealthResponse(
        current_tick=current_tick,
        current_day=current_day,
        current_hour=current_hour,
        season=season,
        weather=weather,
        is_running=is_running,
        queue_depth=queue_depth,
        tick_rate=round(tick_rate, 2),
        events_per_tick=round(events_per_tick, 2),
        uptime_ticks=current_tick,
        tick_interval_seconds=settings.tick_interval_seconds,
    )
