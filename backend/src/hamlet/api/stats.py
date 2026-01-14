"""Stats API routes for dashboard aggregation.

Implements DASH-3 story tasks:
- DASH-9: /api/stats/agents - Count, state distribution, mood averages
- DASH-10: /api/stats/events - Counts by type and significance level
- DASH-11: /api/stats/relationships - Network metrics, clustering, density
- DASH-12: /api/stats/simulation - Tick rate, performance metrics, health
"""

import time

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from hamlet.api.deps import get_db
from hamlet.config import settings
from hamlet.db import Agent, Event, Relationship, WorldState
from hamlet.schemas.stats import (
    AgentStateDistribution,
    AgentStatsResponse,
    EventStatsResponse,
    EventTypeCount,
    MoodAverages,
    NeedsAverages,
    RelationshipStatsResponse,
    RelationshipTypeCount,
    SignificanceLevelCount,
    SimulationStatsResponse,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/agents", response_model=AgentStatsResponse)
async def get_agent_stats(db: Session = Depends(get_db)) -> AgentStatsResponse:
    """Get aggregated agent statistics.

    Returns:
        - Total agent count
        - Distribution by state (idle, busy, sleeping)
        - Average mood values (happiness, energy from mood JSON)
        - Average needs values (hunger, energy, social)
    """
    agents = db.query(Agent).all()
    total_count = len(agents)

    if total_count == 0:
        return AgentStatsResponse(
            total_count=0,
            state_distribution=AgentStateDistribution(),
            mood_averages=MoodAverages(),
            needs_averages=NeedsAverages(),
        )

    # Count states
    state_counts = {"idle": 0, "busy": 0, "sleeping": 0}
    for agent in agents:
        state = agent.state or "idle"
        if state in state_counts:
            state_counts[state] += 1
        else:
            # Unknown states counted as idle
            state_counts["idle"] += 1

    # Calculate mood averages
    total_happiness = 0.0
    total_mood_energy = 0.0
    for agent in agents:
        mood = agent.mood_dict
        total_happiness += mood.get("happiness", 0)
        total_mood_energy += mood.get("energy", 0)

    # Calculate needs averages
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
    """Get aggregated event statistics.

    Returns:
        - Total event count
        - Counts by event type
        - Counts by significance level (1, 2, 3)
        - Count of events in the last hour (simulation time)
    """
    # Total count
    total_count = db.query(func.count(Event.id)).scalar() or 0

    # Count by type
    type_counts = (
        db.query(Event.type, func.count(Event.id))
        .group_by(Event.type)
        .all()
    )
    by_type = [EventTypeCount(type=t, count=c) for t, c in type_counts]

    # Count by significance
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

    # Recent events (last hour = 3600 seconds)
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
    """Get aggregated relationship statistics.

    Returns:
        - Total relationship count
        - Counts by relationship type
        - Average relationship score
        - Counts of positive/negative/neutral relationships
        - Network density (actual edges / possible edges)
        - Average connections per agent
    """
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

    # Count by type
    type_counts: dict[str, int] = {}
    total_score = 0
    positive_count = 0
    negative_count = 0
    neutral_count = 0

    for rel in relationships:
        # Count by type
        rel_type = rel.type or "unknown"
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

        # Aggregate scores
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

    # Calculate network density
    # For a directed graph: density = edges / (n * (n-1))
    # where n is the number of nodes (agents)
    if agent_count > 1:
        max_possible_edges = agent_count * (agent_count - 1)
        network_density = total_count / max_possible_edges
    else:
        network_density = 0.0

    # Average connections per agent
    if agent_count > 0:
        avg_connections = total_count / agent_count
    else:
        avg_connections = 0.0

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


@router.get("/simulation", response_model=SimulationStatsResponse)
async def get_simulation_stats(
    db: Session = Depends(get_db),
) -> SimulationStatsResponse:
    """Get simulation status and performance metrics.

    Returns:
        - Current tick, day, hour, season, weather
        - Whether simulation is running
        - Configured tick interval
        - Average events per tick
        - Uptime in ticks
    """
    # Get world state
    world_state = db.query(WorldState).first()

    if not world_state:
        # Default values if no world state exists
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

    # Calculate events per tick
    total_events = db.query(func.count(Event.id)).scalar() or 0
    if current_tick > 0:
        events_per_tick = total_events / current_tick
    else:
        events_per_tick = 0.0

    # Check if simulation is running by looking at main module
    # This is a simple heuristic - the simulation is "running" if there's a world state
    is_running = world_state is not None

    return SimulationStatsResponse(
        current_tick=current_tick,
        current_day=current_day,
        current_hour=current_hour,
        season=season,
        weather=weather,
        is_running=is_running,
        tick_interval_seconds=settings.tick_interval_seconds,
        events_per_tick=round(events_per_tick, 2),
        uptime_ticks=current_tick,
    )
