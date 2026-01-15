"""Life event detection and generation system."""

import time
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, LifeEvent, Memory, Relationship
from hamlet.life_events.types import (
    EVENT_DESCRIPTIONS,
    EVENT_SIGNIFICANCE,
    FEUD_THRESHOLD,
    FRIENDSHIP_THRESHOLD,
    MARRIAGE_THRESHOLD,
    MENTORSHIP_TRAIT_GAP,
    MIN_INTERACTIONS_FRIENDSHIP,
    MIN_INTERACTIONS_MARRIAGE,
    MIN_INTERACTIONS_MENTORSHIP,
    RIVALRY_THRESHOLD,
    LifeEventStatus,
    LifeEventType,
)


class LifeEventGenerator:
    """Detects and generates life events based on agent relationships and interactions."""

    def __init__(self, db: Session):
        self.db = db

    def check_for_life_events(self) -> list[LifeEvent]:
        """Check all agents for potential life events. Returns list of new events."""
        new_events = []

        # Get all relationships
        relationships = self.db.query(Relationship).all()

        for relationship in relationships:
            # Check for positive events
            if relationship.score >= MARRIAGE_THRESHOLD:
                event = self._check_for_marriage(relationship)
                if event:
                    new_events.append(event)
            elif relationship.score >= FRIENDSHIP_THRESHOLD:
                event = self._check_for_friendship(relationship)
                if event:
                    new_events.append(event)

            # Check for negative events
            if relationship.score <= FEUD_THRESHOLD:
                event = self._check_for_feud(relationship)
                if event:
                    new_events.append(event)
            elif relationship.score <= RIVALRY_THRESHOLD:
                event = self._check_for_rivalry(relationship)
                if event:
                    new_events.append(event)

        # Check for mentorship opportunities
        agents = self.db.query(Agent).all()
        for agent in agents:
            for other in agents:
                if agent.id != other.id:
                    event = self._check_for_mentorship(agent, other)
                    if event:
                        new_events.append(event)

        return new_events

    def _check_for_marriage(self, relationship: Relationship) -> Optional[LifeEvent]:
        """Check if a relationship qualifies for marriage."""
        # Check if marriage already exists
        existing = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.MARRIAGE.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (
                    (LifeEvent.primary_agent_id == relationship.agent_id)
                    & (LifeEvent.secondary_agent_id == relationship.target_id)
                )
                | (
                    (LifeEvent.primary_agent_id == relationship.target_id)
                    & (LifeEvent.secondary_agent_id == relationship.agent_id)
                ),
            )
            .first()
        )
        if existing:
            return None

        # Check interaction count
        history = relationship.history_list
        if len(history) < MIN_INTERACTIONS_MARRIAGE:
            return None

        # Check for romantic interest in traits/memories
        agent = self.db.query(Agent).filter(Agent.id == relationship.agent_id).first()
        target = self.db.query(Agent).filter(Agent.id == relationship.target_id).first()

        if not agent or not target:
            return None

        # Simple romance check - high charm on both sides
        agent_charm = agent.traits_dict.get("charm", 5)
        target_charm = target.traits_dict.get("charm", 5)

        if agent_charm < 6 or target_charm < 6:
            return None

        # Create marriage event
        return self._create_event(
            LifeEventType.MARRIAGE,
            agent.id,
            target.id,
        )

    def _check_for_friendship(self, relationship: Relationship) -> Optional[LifeEvent]:
        """Check if a relationship qualifies for deep friendship."""
        # Check if friendship already exists
        existing = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.FRIENDSHIP.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (
                    (LifeEvent.primary_agent_id == relationship.agent_id)
                    & (LifeEvent.secondary_agent_id == relationship.target_id)
                )
                | (
                    (LifeEvent.primary_agent_id == relationship.target_id)
                    & (LifeEvent.secondary_agent_id == relationship.agent_id)
                ),
            )
            .first()
        )
        if existing:
            return None

        # Check interaction count
        history = relationship.history_list
        if len(history) < MIN_INTERACTIONS_FRIENDSHIP:
            return None

        return self._create_event(
            LifeEventType.FRIENDSHIP,
            relationship.agent_id,
            relationship.target_id,
        )

    def _check_for_rivalry(self, relationship: Relationship) -> Optional[LifeEvent]:
        """Check if a relationship qualifies for rivalry."""
        # Check if rivalry already exists
        existing = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.RIVALRY.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (
                    (LifeEvent.primary_agent_id == relationship.agent_id)
                    & (LifeEvent.secondary_agent_id == relationship.target_id)
                )
                | (
                    (LifeEvent.primary_agent_id == relationship.target_id)
                    & (LifeEvent.secondary_agent_id == relationship.agent_id)
                ),
            )
            .first()
        )
        if existing:
            return None

        return self._create_event(
            LifeEventType.RIVALRY,
            relationship.agent_id,
            relationship.target_id,
        )

    def _check_for_feud(self, relationship: Relationship) -> Optional[LifeEvent]:
        """Check if a relationship qualifies for a feud."""
        # Check if feud already exists
        existing = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.FEUD.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (
                    (LifeEvent.primary_agent_id == relationship.agent_id)
                    & (LifeEvent.secondary_agent_id == relationship.target_id)
                )
                | (
                    (LifeEvent.primary_agent_id == relationship.target_id)
                    & (LifeEvent.secondary_agent_id == relationship.agent_id)
                ),
            )
            .first()
        )
        if existing:
            return None

        # Feuds require an existing rivalry
        rivalry_exists = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.RIVALRY.value,
                (
                    (LifeEvent.primary_agent_id == relationship.agent_id)
                    & (LifeEvent.secondary_agent_id == relationship.target_id)
                )
                | (
                    (LifeEvent.primary_agent_id == relationship.target_id)
                    & (LifeEvent.secondary_agent_id == relationship.agent_id)
                ),
            )
            .first()
        )
        if not rivalry_exists:
            return None

        return self._create_event(
            LifeEventType.FEUD,
            relationship.agent_id,
            relationship.target_id,
        )

    def _check_for_mentorship(
        self,
        mentor_candidate: Agent,
        student_candidate: Agent,
    ) -> Optional[LifeEvent]:
        """Check if two agents qualify for a mentorship relationship."""
        # Check if mentorship already exists
        existing = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.MENTORSHIP.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                LifeEvent.primary_agent_id == mentor_candidate.id,
                LifeEvent.secondary_agent_id == student_candidate.id,
            )
            .first()
        )
        if existing:
            return None

        # Check for trait gap (mentor should be significantly more skilled)
        mentor_traits = mentor_candidate.traits_dict
        student_traits = student_candidate.traits_dict

        # Find a trait where mentor excels and student is lower
        mentorship_trait = None
        for trait in ["curiosity", "perception", "integrity", "empathy"]:
            mentor_val = mentor_traits.get(trait, 5)
            student_val = student_traits.get(trait, 5)
            if mentor_val - student_val >= MENTORSHIP_TRAIT_GAP:
                mentorship_trait = trait
                break

        if not mentorship_trait:
            return None

        # Check relationship - they should at least know each other
        relationship = (
            self.db.query(Relationship)
            .filter(
                Relationship.agent_id == mentor_candidate.id,
                Relationship.target_id == student_candidate.id,
            )
            .first()
        )
        if not relationship or len(relationship.history_list) < MIN_INTERACTIONS_MENTORSHIP:
            return None

        if relationship.score < 0:  # Can't mentor someone you dislike
            return None

        return self._create_event(
            LifeEventType.MENTORSHIP,
            mentor_candidate.id,
            student_candidate.id,
            effects={"mentorship_trait": mentorship_trait},
        )

    def _create_event(
        self,
        event_type: LifeEventType,
        primary_agent_id: str,
        secondary_agent_id: Optional[str] = None,
        related_agents: Optional[list[str]] = None,
        effects: Optional[dict] = None,
    ) -> LifeEvent:
        """Create and persist a new life event."""
        # Get agent names for description
        primary = self.db.query(Agent).filter(Agent.id == primary_agent_id).first()
        secondary = (
            self.db.query(Agent).filter(Agent.id == secondary_agent_id).first()
            if secondary_agent_id
            else None
        )

        description = EVENT_DESCRIPTIONS.get(event_type, "{agent1} experienced {event_type}").format(
            agent1=primary.name if primary else primary_agent_id,
            agent2=secondary.name if secondary else secondary_agent_id or "another",
            event_type=event_type.value,
        )

        event = LifeEvent(
            type=event_type.value,
            primary_agent_id=primary_agent_id,
            secondary_agent_id=secondary_agent_id,
            description=description,
            significance=EVENT_SIGNIFICANCE.get(event_type, 5),
            status=LifeEventStatus.ACTIVE.value,
            timestamp=time.time(),
        )
        event.related_agents_list = related_agents or []
        event.effects_dict = effects or {}

        self.db.add(event)
        return event

    def create_betrayal(
        self,
        betrayer_id: str,
        victim_id: str,
        context: str = "",
    ) -> LifeEvent:
        """Create a betrayal event (typically triggered by specific actions)."""
        effects = {"context": context, "trust_broken": True}
        return self._create_event(
            LifeEventType.BETRAYAL,
            betrayer_id,
            victim_id,
            effects=effects,
        )

    def create_reconciliation(
        self,
        agent1_id: str,
        agent2_id: str,
    ) -> Optional[LifeEvent]:
        """Create a reconciliation event if there's a prior conflict to resolve."""
        # Check for existing rivalry or feud
        conflict = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type.in_([LifeEventType.RIVALRY.value, LifeEventType.FEUD.value]),
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (
                    (LifeEvent.primary_agent_id == agent1_id)
                    & (LifeEvent.secondary_agent_id == agent2_id)
                )
                | (
                    (LifeEvent.primary_agent_id == agent2_id)
                    & (LifeEvent.secondary_agent_id == agent1_id)
                ),
            )
            .first()
        )

        if not conflict:
            return None

        # Mark the conflict as resolved
        conflict.status = LifeEventStatus.RESOLVED.value
        conflict.resolved_at = time.time()

        return self._create_event(
            LifeEventType.RECONCILIATION,
            agent1_id,
            agent2_id,
        )

    def get_active_events_for_agent(self, agent_id: str) -> list[LifeEvent]:
        """Get all active life events involving an agent."""
        return (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
                (LifeEvent.primary_agent_id == agent_id)
                | (LifeEvent.secondary_agent_id == agent_id),
            )
            .all()
        )

    def get_life_event_context(self, agent_id: str) -> str:
        """Get life event context string for LLM prompts."""
        events = self.get_active_events_for_agent(agent_id)
        if not events:
            return ""

        context_parts = ["Your significant life situations:"]
        for event in events:
            other_agent = None
            if event.primary_agent_id == agent_id and event.secondary_agent_id:
                other = self.db.query(Agent).filter(Agent.id == event.secondary_agent_id).first()
                other_agent = other.name if other else event.secondary_agent_id
            elif event.secondary_agent_id == agent_id:
                other = self.db.query(Agent).filter(Agent.id == event.primary_agent_id).first()
                other_agent = other.name if other else event.primary_agent_id

            event_desc = event.description
            if event.type == LifeEventType.MARRIAGE.value and other_agent:
                context_parts.append(f"- You are married to {other_agent}")
            elif event.type == LifeEventType.MENTORSHIP.value:
                if event.primary_agent_id == agent_id:
                    context_parts.append(f"- You are mentoring {other_agent}")
                else:
                    context_parts.append(f"- You are being mentored by {other_agent}")
            elif event.type == LifeEventType.RIVALRY.value and other_agent:
                context_parts.append(f"- You have an ongoing rivalry with {other_agent}")
            elif event.type == LifeEventType.FEUD.value and other_agent:
                context_parts.append(f"- You are in a bitter feud with {other_agent}")
            else:
                context_parts.append(f"- {event_desc}")

        return "\n".join(context_parts)
