"""Narrative arc detection from events and agent relationships."""

import random
import time
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, ArcEvent, Event, LifeEvent, NarrativeArc, Relationship
from hamlet.life_events.types import LifeEventType
from hamlet.narrative_arcs.types import (
    ACT_NAMES,
    ARC_BASE_SIGNIFICANCE,
    ARC_RELATIONSHIP_PATTERNS,
    ARC_THEMES,
    ARC_TITLE_TEMPLATES,
    LIFE_EVENT_ARC_MAPPINGS,
    Act,
    ActStatus,
    ArcStatus,
    ArcType,
)


class NarrativeArcDetector:
    """Detects and creates narrative arcs from simulation events."""

    def __init__(self, db: Session):
        self.db = db

    def detect_arcs(self) -> list[NarrativeArc]:
        """Scan for new narrative arcs. Returns list of newly detected arcs."""
        new_arcs = []

        # Detect arcs from life events
        life_event_arcs = self._detect_from_life_events()
        new_arcs.extend(life_event_arcs)

        # Detect arcs from relationship patterns
        relationship_arcs = self._detect_from_relationships()
        new_arcs.extend(relationship_arcs)

        # Detect arcs from goal patterns
        goal_arcs = self._detect_from_goals()
        new_arcs.extend(goal_arcs)

        return new_arcs

    def _detect_from_life_events(self) -> list[NarrativeArc]:
        """Detect arcs from recent life events."""
        arcs = []

        # Get recent life events that haven't been assigned to arcs
        recent_events = (
            self.db.query(LifeEvent)
            .filter(LifeEvent.timestamp > time.time() - 86400 * 7)  # Last 7 days
            .all()
        )

        for event in recent_events:
            event_type = event.type.lower()
            if event_type not in LIFE_EVENT_ARC_MAPPINGS:
                continue

            # Check if arc already exists for this event pair
            existing = self._find_existing_arc(
                event.primary_agent_id,
                event.secondary_agent_id,
                LIFE_EVENT_ARC_MAPPINGS[event_type],
            )
            if existing:
                # Add event to existing arc
                self._add_event_to_arc(existing, event)
                continue

            # Create new arc
            arc_type = LIFE_EVENT_ARC_MAPPINGS[event_type][0]
            arc = self._create_arc(
                arc_type,
                event.primary_agent_id,
                event.secondary_agent_id,
            )
            if arc:
                arcs.append(arc)

        return arcs

    def _detect_from_relationships(self) -> list[NarrativeArc]:
        """Detect arcs from relationship patterns."""
        arcs = []

        relationships = self.db.query(Relationship).all()

        for relationship in relationships:
            # Check for love story potential
            if relationship.score >= 6 and len(relationship.history_list) >= 8:
                if not self._find_existing_arc(
                    relationship.agent_id,
                    relationship.target_id,
                    [ArcType.LOVE_STORY],
                ):
                    arc = self._create_arc(
                        ArcType.LOVE_STORY,
                        relationship.agent_id,
                        relationship.target_id,
                    )
                    if arc:
                        arcs.append(arc)

            # Check for rivalry arc
            elif relationship.score <= -3 and len(relationship.history_list) >= 5:
                if not self._find_existing_arc(
                    relationship.agent_id,
                    relationship.target_id,
                    [ArcType.RIVALRY],
                ):
                    arc = self._create_arc(
                        ArcType.RIVALRY,
                        relationship.agent_id,
                        relationship.target_id,
                    )
                    if arc:
                        arcs.append(arc)

            # Check for friendship arc
            elif relationship.score >= 4 and len(relationship.history_list) >= 5:
                if not self._find_existing_arc(
                    relationship.agent_id,
                    relationship.target_id,
                    [ArcType.FRIENDSHIP],
                ):
                    arc = self._create_arc(
                        ArcType.FRIENDSHIP,
                        relationship.agent_id,
                        relationship.target_id,
                    )
                    if arc:
                        arcs.append(arc)

        return arcs

    def _detect_from_goals(self) -> list[NarrativeArc]:
        """Detect arcs from agent goal patterns."""
        arcs = []

        # Rise to power arc - agents with power/wealth goals
        from hamlet.db.models import Goal

        power_seekers = (
            self.db.query(Goal)
            .filter(Goal.type.in_(["gain_power", "gain_wealth"]), Goal.status == "active")
            .all()
        )

        seen_agents = set()
        for goal in power_seekers:
            if goal.agent_id in seen_agents:
                continue
            seen_agents.add(goal.agent_id)

            if not self._find_existing_arc(goal.agent_id, None, [ArcType.RISE_TO_POWER]):
                arc = self._create_arc(ArcType.RISE_TO_POWER, goal.agent_id)
                if arc:
                    arcs.append(arc)

        return arcs

    def _find_existing_arc(
        self,
        primary_id: str,
        secondary_id: Optional[str],
        arc_types: list[ArcType],
    ) -> Optional[NarrativeArc]:
        """Find an existing arc matching the criteria."""
        query = self.db.query(NarrativeArc).filter(
            NarrativeArc.type.in_([t.value for t in arc_types]),
            NarrativeArc.status.notin_([ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]),
        )

        if secondary_id:
            # Check both directions
            query = query.filter(
                (
                    (NarrativeArc.primary_agent_id == primary_id)
                    & (NarrativeArc.secondary_agent_id == secondary_id)
                )
                | (
                    (NarrativeArc.primary_agent_id == secondary_id)
                    & (NarrativeArc.secondary_agent_id == primary_id)
                )
            )
        else:
            query = query.filter(NarrativeArc.primary_agent_id == primary_id)

        return query.first()

    def _create_arc(
        self,
        arc_type: ArcType,
        primary_agent_id: str,
        secondary_agent_id: Optional[str] = None,
    ) -> Optional[NarrativeArc]:
        """Create a new narrative arc."""
        # Get agent names for title
        primary = self.db.query(Agent).filter(Agent.id == primary_agent_id).first()
        secondary = (
            self.db.query(Agent).filter(Agent.id == secondary_agent_id).first()
            if secondary_agent_id
            else None
        )

        if not primary:
            return None

        # Generate title
        templates = ARC_TITLE_TEMPLATES.get(arc_type, ["{agent1}'s Story"])
        title_template = random.choice(templates)
        title = title_template.format(
            agent1=primary.name,
            agent2=secondary.name if secondary else "",
        )

        # Initialize acts
        initial_acts = [
            Act(
                number=0,
                status=ActStatus.IN_PROGRESS,
                events=[],
                key_moments=[],
                turning_point=None,
            ).to_dict()
        ]

        arc = NarrativeArc(
            type=arc_type.value,
            title=title,
            primary_agent_id=primary_agent_id,
            secondary_agent_id=secondary_agent_id,
            theme=ARC_THEMES.get(arc_type, "A story unfolding in the village"),
            current_act=0,
            status=ArcStatus.FORMING.value,
            significance=ARC_BASE_SIGNIFICANCE.get(arc_type, 5),
            discovered_at=time.time(),
        )
        arc.acts_list = initial_acts

        self.db.add(arc)
        return arc

    def _add_event_to_arc(
        self,
        arc: NarrativeArc,
        life_event: LifeEvent,
    ) -> None:
        """Add a life event to an existing arc."""
        # Find the corresponding simulation event
        sim_event = (
            self.db.query(Event)
            .filter(
                Event.timestamp >= life_event.timestamp - 60,
                Event.timestamp <= life_event.timestamp + 60,
            )
            .first()
        )

        if sim_event:
            arc_event = ArcEvent(
                arc_id=arc.id,
                event_id=sim_event.id,
                act_number=arc.current_act,
                is_turning_point=life_event.significance >= 8,
            )
            self.db.add(arc_event)

            # Update arc acts
            acts = arc.acts_list
            if arc.current_act < len(acts):
                act = Act.from_dict(acts[arc.current_act])
                act.events.append(sim_event.id)
                if life_event.significance >= 7:
                    act.key_moments.append(life_event.description)
                acts[arc.current_act] = act.to_dict()
                arc.acts_list = acts

    def advance_arc(self, arc: NarrativeArc, turning_point: str) -> bool:
        """Advance an arc to the next act."""
        if arc.current_act >= 4:
            return False

        acts = arc.acts_list

        # Complete current act
        if arc.current_act < len(acts):
            current = Act.from_dict(acts[arc.current_act])
            current.status = ActStatus.COMPLETE
            current.turning_point = turning_point
            acts[arc.current_act] = current.to_dict()

        # Start next act
        arc.current_act += 1
        new_act = Act(
            number=arc.current_act,
            status=ActStatus.IN_PROGRESS,
            events=[],
            key_moments=[],
            turning_point=None,
        )
        acts.append(new_act.to_dict())
        arc.acts_list = acts

        # Update arc status based on act
        if arc.current_act == 1:
            arc.status = ArcStatus.RISING_ACTION.value
        elif arc.current_act == 2:
            arc.status = ArcStatus.CLIMAX.value
        elif arc.current_act == 3:
            arc.status = ArcStatus.FALLING_ACTION.value
        elif arc.current_act == 4:
            arc.status = ArcStatus.RESOLUTION.value
            arc.completed_at = time.time()

        return True

    def complete_arc(self, arc: NarrativeArc, resolution: str) -> None:
        """Mark an arc as complete with resolution."""
        arc.status = ArcStatus.RESOLUTION.value
        arc.completed_at = time.time()

        acts = arc.acts_list
        if arc.current_act < len(acts):
            current = Act.from_dict(acts[arc.current_act])
            current.status = ActStatus.COMPLETE
            current.turning_point = resolution
            acts[arc.current_act] = current.to_dict()
            arc.acts_list = acts

    def abandon_arc(self, arc: NarrativeArc, reason: str = "No further developments") -> None:
        """Mark an arc as abandoned."""
        arc.status = ArcStatus.ABANDONED.value

        acts = arc.acts_list
        if arc.current_act < len(acts):
            current = Act.from_dict(acts[arc.current_act])
            current.turning_point = f"Abandoned: {reason}"
            acts[arc.current_act] = current.to_dict()
            arc.acts_list = acts

    def get_active_arcs(self) -> list[NarrativeArc]:
        """Get all active (non-completed, non-abandoned) arcs."""
        return (
            self.db.query(NarrativeArc)
            .filter(
                NarrativeArc.status.notin_(
                    [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]
                )
            )
            .order_by(NarrativeArc.significance.desc())
            .all()
        )

    def get_arcs_for_agent(self, agent_id: str) -> list[NarrativeArc]:
        """Get all arcs involving an agent."""
        return (
            self.db.query(NarrativeArc)
            .filter(
                (NarrativeArc.primary_agent_id == agent_id)
                | (NarrativeArc.secondary_agent_id == agent_id)
            )
            .order_by(NarrativeArc.discovered_at.desc())
            .all()
        )

    def get_arc_context_for_agent(self, agent_id: str) -> str:
        """Get arc context string for LLM prompts."""
        arcs = self.get_arcs_for_agent(agent_id)
        active_arcs = [a for a in arcs if a.status not in [ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]]

        if not active_arcs:
            return ""

        context_parts = ["You are part of ongoing narratives:"]

        for arc in active_arcs[:3]:  # Top 3 arcs
            arc_type = ArcType(arc.type)
            act_name = ACT_NAMES.get(arc.current_act, "Unknown")

            # Determine role
            if arc.primary_agent_id == agent_id:
                role = "protagonist"
            else:
                role = "co-protagonist"

            context_parts.append(
                f"- {arc.title} ({arc_type.value}): You are the {role}. "
                f"Currently in {act_name}. {arc.theme}"
            )

        return "\n".join(context_parts)
