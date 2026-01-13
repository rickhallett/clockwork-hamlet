"""World state management."""

import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from hamlet.db import Agent, Location, SessionLocal, WorldState
from hamlet.simulation.events import EventBus, EventType, SimulationEvent
from hamlet.simulation.events import event_bus as default_event_bus


@dataclass
class AgentPerception:
    """What an agent perceives in their current location."""

    location_name: str
    nearby_agents: list[str]
    nearby_objects: list[str]


@dataclass
class WorldSnapshot:
    """A snapshot of the current world state."""

    tick: int
    day: int
    hour: float
    season: str
    weather: str
    agents: dict[str, dict]
    locations: dict[str, dict]


class World:
    """Manages the simulation world state."""

    def __init__(self, event_bus: EventBus | None = None):
        self.event_bus = event_bus or default_event_bus
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        """Get or create database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def close(self) -> None:
        """Close the database session."""
        if self._db is not None:
            self._db.close()
            self._db = None

    def get_world_state(self) -> WorldState:
        """Get the current world state from database."""
        state = self.db.query(WorldState).first()
        if state is None:
            state = WorldState(id=1, current_tick=0, current_day=1, current_hour=6.0)
            self.db.add(state)
            self.db.commit()
        return state

    def get_agents(self) -> list[Agent]:
        """Get all agents."""
        return self.db.query(Agent).all()

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID."""
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def get_locations(self) -> list[Location]:
        """Get all locations."""
        return self.db.query(Location).all()

    def get_location(self, location_id: str) -> Location | None:
        """Get a location by ID."""
        return self.db.query(Location).filter(Location.id == location_id).first()

    def get_agents_at_location(self, location_id: str) -> list[Agent]:
        """Get all agents at a specific location."""
        return self.db.query(Agent).filter(Agent.location_id == location_id).all()

    def get_agent_perception(self, agent: Agent) -> AgentPerception:
        """Get what an agent can perceive."""
        location = self.get_location(agent.location_id) if agent.location_id else None
        nearby_agents = []
        nearby_objects = []

        if location:
            agents_here = self.get_agents_at_location(location.id)
            nearby_agents = [a.name for a in agents_here if a.id != agent.id]
            nearby_objects = location.objects_list

        return AgentPerception(
            location_name=location.name if location else "Unknown",
            nearby_agents=nearby_agents,
            nearby_objects=nearby_objects,
        )

    def advance_time(self, minutes: int = 30) -> tuple[int, int, float]:
        """Advance world time by specified minutes. Returns (tick, day, hour)."""
        state = self.get_world_state()

        state.current_tick += 1
        state.current_hour += minutes / 60.0

        # Handle day rollover
        if state.current_hour >= 24.0:
            state.current_hour -= 24.0
            state.current_day += 1

            # Handle season changes (every 30 days)
            seasons = ["spring", "summer", "autumn", "winter"]
            season_index = (state.current_day // 30) % 4
            state.season = seasons[season_index]

        self.db.commit()
        return state.current_tick, state.current_day, state.current_hour

    def update_agent_needs(self, agent: Agent, hours_passed: float = 0.5) -> None:
        """Update an agent's needs based on time passed."""
        # Hunger increases over time
        agent.hunger = min(10.0, agent.hunger + hours_passed * 0.5)

        # Energy decreases during day, restored during sleep
        if agent.state == "sleeping":
            agent.energy = min(10.0, agent.energy + hours_passed * 2.0)
        else:
            agent.energy = max(0.0, agent.energy - hours_passed * 0.3)

        # Social need increases when alone, decreases when with others
        if agent.location_id:
            others = self.get_agents_at_location(agent.location_id)
            if len(others) > 1:  # Someone else is here
                agent.social = min(10.0, agent.social + hours_passed * 0.5)
            else:
                agent.social = max(0.0, agent.social - hours_passed * 0.2)

    def is_daytime(self) -> bool:
        """Check if it's currently daytime."""
        state = self.get_world_state()
        return 6.0 <= state.current_hour < 22.0

    def wake_sleeping_agents(self) -> list[Agent]:
        """Wake up sleeping agents if it's morning."""
        woken = []
        state = self.get_world_state()

        # Wake agents at 6am
        if 6.0 <= state.current_hour < 6.5:
            sleeping_agents = self.db.query(Agent).filter(Agent.state == "sleeping").all()
            for agent in sleeping_agents:
                agent.state = "idle"
                woken.append(agent)

        return woken

    def put_agents_to_sleep(self) -> list[Agent]:
        """Put agents to sleep if it's late night."""
        sleeping = []
        state = self.get_world_state()

        # Agents sleep at 10pm
        if state.current_hour >= 22.0 or state.current_hour < 6.0:
            awake_agents = self.db.query(Agent).filter(Agent.state != "sleeping").all()
            for agent in awake_agents:
                agent.state = "sleeping"
                sleeping.append(agent)

        return sleeping

    def get_snapshot(self) -> WorldSnapshot:
        """Get a complete snapshot of the world state."""
        state = self.get_world_state()
        agents = self.get_agents()
        locations = self.get_locations()

        return WorldSnapshot(
            tick=state.current_tick,
            day=state.current_day,
            hour=state.current_hour,
            season=state.season,
            weather=state.weather,
            agents={
                a.id: {"name": a.name, "location": a.location_id, "state": a.state} for a in agents
            },
            locations={
                loc.id: {"name": loc.name, "agent_count": len(self.get_agents_at_location(loc.id))}
                for loc in locations
            },
        )

    def commit(self) -> None:
        """Commit any pending changes to the database."""
        self.db.commit()

    async def publish_event(
        self,
        event_type: EventType,
        summary: str,
        actors: list[str] | None = None,
        location_id: str | None = None,
        detail: str | None = None,
        significance: int = 1,
    ) -> None:
        """Publish a simulation event."""
        state = self.get_world_state()
        event = SimulationEvent(
            type=event_type,
            summary=summary,
            timestamp=int(time.time()),
            actors=actors or [],
            location_id=location_id,
            detail=detail,
            significance=significance,
            data={"tick": state.current_tick, "day": state.current_day, "hour": state.current_hour},
        )
        await self.event_bus.publish(event)
