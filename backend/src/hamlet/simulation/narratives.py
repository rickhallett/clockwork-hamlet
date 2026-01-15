"""Emergent narratives integration for simulation engine."""

import logging
import time

from sqlalchemy.orm import Session

from hamlet.db.models import Agent
from hamlet.factions import FactionManager
from hamlet.goals import GoalPlanner
from hamlet.life_events import LifeEventConsequences, LifeEventGenerator
from hamlet.narrative_arcs import NarrativeAnalyzer, NarrativeArcDetector
from hamlet.simulation.events import EventType, SimulationEvent, event_bus

logger = logging.getLogger(__name__)


class EmergentNarratives:
    """Manages emergent narrative systems during simulation."""

    def __init__(self, db: Session):
        self.db = db
        self.faction_manager = FactionManager(db)
        self.life_event_generator = LifeEventGenerator(db)
        self.life_event_consequences = LifeEventConsequences(db)
        self.arc_detector = NarrativeArcDetector(db)
        self.arc_analyzer = NarrativeAnalyzer(db)
        self.goal_planner = GoalPlanner(db)

        # Track last check times to avoid running every tick
        # Initialize to current time so we don't trigger everything on the first tick
        now = time.time()
        self._last_life_event_check = now
        self._last_arc_check = now
        self._last_faction_check = now
        self._last_plan_check = now

        # Check intervals (in seconds)
        self.life_event_interval = 300  # Every 5 minutes
        self.arc_interval = 600  # Every 10 minutes
        self.faction_interval = 900  # Every 15 minutes
        self.plan_interval = 600  # Every 10 minutes

    async def process_tick(self, tick: int, day: int, hour: float) -> None:
        """Process emergent narrative systems each tick.

        This is called from the main simulation engine tick loop.
        """
        now = time.time()

        # Check for life events periodically
        if now - self._last_life_event_check >= self.life_event_interval:
            await self._check_life_events()
            self._last_life_event_check = now

        # Check for narrative arcs periodically
        if now - self._last_arc_check >= self.arc_interval:
            await self._detect_narrative_arcs()
            self._last_arc_check = now

        # Check faction dynamics periodically
        if now - self._last_faction_check >= self.faction_interval:
            await self._process_faction_dynamics()
            self._last_faction_check = now

        # Check long-term plan progress periodically
        if now - self._last_plan_check >= self.plan_interval:
            await self._check_plan_progress()
            self._last_plan_check = now

        # Check for event resolutions
        await self._check_event_resolutions()

    async def _check_life_events(self) -> None:
        """Check for and process new life events."""
        try:
            new_events = self.life_event_generator.check_for_life_events()

            for event in new_events:
                logger.info(f"Life event detected: {event.type} - {event.description}")

                # Apply consequences
                changes = self.life_event_consequences.apply_event_consequences(event)

                # Publish to event bus
                await event_bus.publish(
                    SimulationEvent(
                        type=EventType.RELATIONSHIP,
                        summary=event.description,
                        timestamp=int(time.time()),
                        actors=[event.primary_agent_id]
                        + ([event.secondary_agent_id] if event.secondary_agent_id else []),
                        significance=event.significance,
                        data={"life_event_type": event.type},
                    )
                )

                logger.debug(f"Life event consequences: {changes}")

            self.db.commit()

        except Exception as e:
            logger.error(f"Error checking life events: {e}")
            self.db.rollback()

    async def _detect_narrative_arcs(self) -> None:
        """Detect new narrative arcs from events and relationships."""
        try:
            new_arcs = self.arc_detector.detect_arcs()

            for arc in new_arcs:
                logger.info(f"Narrative arc detected: {arc.title} ({arc.type})")

                # Publish arc detection as a discovery event
                await event_bus.publish(
                    SimulationEvent(
                        type=EventType.DISCOVERY,
                        summary=f"A new story unfolds: {arc.title}",
                        timestamp=int(time.time()),
                        actors=[arc.primary_agent_id]
                        + ([arc.secondary_agent_id] if arc.secondary_agent_id else []),
                        significance=arc.significance,
                        data={"arc_type": arc.type, "arc_id": arc.id},
                    )
                )

            self.db.commit()

        except Exception as e:
            logger.error(f"Error detecting narrative arcs: {e}")
            self.db.rollback()

    async def _process_faction_dynamics(self) -> None:
        """Process faction formation and dynamics."""
        try:
            agents = self.db.query(Agent).all()

            for agent in agents:
                # Check if agent should form a new faction
                if self.faction_manager.should_form_faction(agent):
                    faction_type = self.faction_manager.get_compatible_faction_type(agent)
                    faction = self.faction_manager.create_faction(
                        name=f"{agent.name}'s {faction_type.value.title()}",
                        founder_id=agent.id,
                        faction_type=faction_type,
                        location_id=agent.location_id,
                    )

                    if faction:
                        logger.info(f"Faction formed: {faction.name} by {agent.name}")

                        await event_bus.publish(
                            SimulationEvent(
                                type=EventType.SYSTEM,
                                summary=f"{agent.name} has founded {faction.name}",
                                timestamp=int(time.time()),
                                actors=[agent.id],
                                location_id=agent.location_id,
                                significance=3,
                                data={"faction_id": faction.id},
                            )
                        )

                # Check if agent should join existing factions
                factions = self.faction_manager.get_all_factions()
                for faction in factions:
                    if self.faction_manager.should_join_faction(agent, faction):
                        membership = self.faction_manager.add_member(faction.id, agent.id)
                        if membership:
                            logger.info(f"{agent.name} joined {faction.name}")

                            await event_bus.publish(
                                SimulationEvent(
                                    type=EventType.RELATIONSHIP,
                                    summary=f"{agent.name} has joined {faction.name}",
                                    timestamp=int(time.time()),
                                    actors=[agent.id],
                                    significance=2,
                                    data={"faction_id": faction.id},
                                )
                            )
                            break  # Only join one faction per check

            self.db.commit()

        except Exception as e:
            logger.error(f"Error processing faction dynamics: {e}")
            self.db.rollback()

    async def _check_plan_progress(self) -> None:
        """Check and update long-term goal plan progress."""
        try:
            agents = self.db.query(Agent).all()

            for agent in agents:
                # Generate ambitions for agents without plans
                plan = self.goal_planner.generate_ambition(agent)
                if plan:
                    logger.info(f"Ambition generated for {agent.name}: {plan.description}")

                    await event_bus.publish(
                        SimulationEvent(
                            type=EventType.SYSTEM,
                            summary=f"{agent.name} has developed a new ambition: {plan.type}",
                            timestamp=int(time.time()),
                            actors=[agent.id],
                            significance=2,
                            data={"plan_type": plan.type},
                        )
                    )

                # Check progress on existing plans
                milestone_msg = self.goal_planner.check_plan_progress(agent)
                if milestone_msg:
                    logger.info(f"Plan progress for {agent.name}: {milestone_msg}")

                    await event_bus.publish(
                        SimulationEvent(
                            type=EventType.ACTION,
                            summary=f"{agent.name}: {milestone_msg}",
                            timestamp=int(time.time()),
                            actors=[agent.id],
                            significance=3,
                        )
                    )

            self.db.commit()

        except Exception as e:
            logger.error(f"Error checking plan progress: {e}")
            self.db.rollback()

    async def _check_event_resolutions(self) -> None:
        """Check for life events that should be auto-resolved."""
        try:
            resolved = self.life_event_consequences.check_event_resolutions()

            for event in resolved:
                logger.info(f"Life event resolved: {event.type} - {event.description}")

                await event_bus.publish(
                    SimulationEvent(
                        type=EventType.RELATIONSHIP,
                        summary=event.description,
                        timestamp=int(time.time()),
                        actors=[event.primary_agent_id]
                        + ([event.secondary_agent_id] if event.secondary_agent_id else []),
                        significance=event.significance,
                        data={"life_event_type": event.type, "resolved": True},
                    )
                )

            self.db.commit()

        except Exception as e:
            logger.error(f"Error checking event resolutions: {e}")
            self.db.rollback()

    def get_agent_narrative_context(self, agent_id: str) -> str:
        """Get full narrative context for an agent (for LLM prompts)."""
        context_parts = []

        # Faction context
        faction_ctx = self.faction_manager.get_faction_context_for_agent(agent_id)
        if faction_ctx:
            context_parts.append(faction_ctx)

        # Life event context
        life_ctx = self.life_event_generator.get_life_event_context(agent_id)
        if life_ctx:
            context_parts.append(life_ctx)

        # Narrative arc context
        arc_ctx = self.arc_detector.get_arc_context_for_agent(agent_id)
        if arc_ctx:
            context_parts.append(arc_ctx)

        # Long-term plan context
        plan_ctx = self.goal_planner.get_plan_context(agent_id)
        if plan_ctx:
            context_parts.append(plan_ctx)

        return "\n\n".join(context_parts) if context_parts else ""

    def generate_story_digest(self) -> dict:
        """Generate a story digest for the current state of narratives."""
        digest = self.arc_analyzer.generate_daily_digest()

        return {
            "title": digest.title,
            "summary": digest.summary,
            "active_arcs": digest.active_arcs,
            "completed_arcs": digest.completed_arcs,
            "notable_moments": digest.notable_moments,
            "suggested_focus": digest.suggested_focus,
            "village_state": self.arc_analyzer.get_village_story_state(),
        }
