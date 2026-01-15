"""Life event consequences and effects application."""

import time
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, Goal, LifeEvent, Memory, Relationship
from hamlet.life_events.types import (
    EVENT_RELATIONSHIP_EFFECTS,
    LifeEventStatus,
    LifeEventType,
)


class LifeEventConsequences:
    """Applies consequences of life events to agents and relationships."""

    def __init__(self, db: Session):
        self.db = db

    def apply_event_consequences(self, event: LifeEvent) -> dict:
        """Apply all consequences of a life event. Returns summary of changes."""
        changes = {
            "relationship_changes": [],
            "memories_created": [],
            "goals_created": [],
            "trait_changes": [],
        }

        # Apply relationship effects
        rel_changes = self._apply_relationship_effects(event)
        changes["relationship_changes"].extend(rel_changes)

        # Create memories for involved agents
        memories = self._create_event_memories(event)
        changes["memories_created"].extend(memories)

        # Generate reactive goals
        goals = self._generate_reactive_goals(event)
        changes["goals_created"].extend(goals)

        # Apply trait modifications for certain events
        if event.type == LifeEventType.TRANSFORMATION.value:
            trait_changes = self._apply_trait_changes(event)
            changes["trait_changes"].extend(trait_changes)

        return changes

    def _apply_relationship_effects(self, event: LifeEvent) -> list[dict]:
        """Apply relationship score changes from event."""
        changes = []
        event_type = LifeEventType(event.type)
        effects = EVENT_RELATIONSHIP_EFFECTS.get(event_type, {})

        if not effects:
            return changes

        primary_secondary_change = effects.get("primary_secondary", 0)

        if primary_secondary_change and event.secondary_agent_id:
            # Update relationship from primary to secondary
            relationship = self._get_or_create_relationship(
                event.primary_agent_id,
                event.secondary_agent_id,
            )
            old_score = relationship.score
            relationship.score = max(-10, min(10, relationship.score + primary_secondary_change))

            # Update relationship type based on new score and event
            self._update_relationship_type(relationship, event_type)

            # Add to history
            history = relationship.history_list
            history.append(f"[{event.type}] Score changed from {old_score} to {relationship.score}")
            relationship.history_list = history[-20:]

            changes.append({
                "agent_id": event.primary_agent_id,
                "target_id": event.secondary_agent_id,
                "old_score": old_score,
                "new_score": relationship.score,
                "reason": event.type,
            })

            # Also update reverse relationship
            reverse = self._get_or_create_relationship(
                event.secondary_agent_id,
                event.primary_agent_id,
            )
            old_reverse = reverse.score
            reverse.score = max(-10, min(10, reverse.score + primary_secondary_change))
            self._update_relationship_type(reverse, event_type)

            history = reverse.history_list
            history.append(f"[{event.type}] Score changed from {old_reverse} to {reverse.score}")
            reverse.history_list = history[-20:]

            changes.append({
                "agent_id": event.secondary_agent_id,
                "target_id": event.primary_agent_id,
                "old_score": old_reverse,
                "new_score": reverse.score,
                "reason": event.type,
            })

        return changes

    def _get_or_create_relationship(
        self,
        agent_id: str,
        target_id: str,
    ) -> Relationship:
        """Get existing relationship or create a new one."""
        relationship = (
            self.db.query(Relationship)
            .filter(
                Relationship.agent_id == agent_id,
                Relationship.target_id == target_id,
            )
            .first()
        )

        if not relationship:
            relationship = Relationship(
                agent_id=agent_id,
                target_id=target_id,
                type="acquaintance",
                score=0,
            )
            self.db.add(relationship)

        return relationship

    def _update_relationship_type(
        self,
        relationship: Relationship,
        event_type: LifeEventType,
    ) -> None:
        """Update relationship type based on event and score."""
        if event_type == LifeEventType.MARRIAGE:
            relationship.type = "spouse"
        elif event_type == LifeEventType.DIVORCE:
            relationship.type = "ex-spouse"
        elif event_type == LifeEventType.FRIENDSHIP:
            relationship.type = "close_friend"
        elif event_type == LifeEventType.MENTORSHIP:
            relationship.type = "mentor" if relationship.score > 0 else "student"
        elif event_type == LifeEventType.RIVALRY:
            relationship.type = "rival"
        elif event_type == LifeEventType.FEUD:
            relationship.type = "enemy"
        elif event_type == LifeEventType.RECONCILIATION:
            if relationship.score >= 5:
                relationship.type = "friend"
            elif relationship.score >= 0:
                relationship.type = "acquaintance"
            else:
                relationship.type = "uneasy_acquaintance"
        elif event_type == LifeEventType.BETRAYAL:
            relationship.type = "betrayer" if relationship.score < 0 else "uneasy_acquaintance"

    def _create_event_memories(self, event: LifeEvent) -> list[str]:
        """Create memories for agents involved in the event."""
        memories = []
        timestamp = int(event.timestamp)

        # Primary agent memory
        primary_memory = Memory(
            agent_id=event.primary_agent_id,
            timestamp=timestamp,
            type="longterm",  # Life events are significant
            content=event.description,
            significance=event.significance,
            compressed=False,
        )
        self.db.add(primary_memory)
        memories.append(f"Created longterm memory for {event.primary_agent_id}: {event.description}")

        # Secondary agent memory (if exists)
        if event.secondary_agent_id:
            secondary_memory = Memory(
                agent_id=event.secondary_agent_id,
                timestamp=timestamp,
                type="longterm",
                content=event.description,
                significance=event.significance,
                compressed=False,
            )
            self.db.add(secondary_memory)
            memories.append(f"Created longterm memory for {event.secondary_agent_id}: {event.description}")

        # Related agents get less significant memories
        for related_id in event.related_agents_list:
            related_memory = Memory(
                agent_id=related_id,
                timestamp=timestamp,
                type="recent",  # Witnesses remember less intensely
                content=f"Witnessed: {event.description}",
                significance=max(1, event.significance - 3),
                compressed=False,
            )
            self.db.add(related_memory)
            memories.append(f"Created witness memory for {related_id}")

        return memories

    def _generate_reactive_goals(self, event: LifeEvent) -> list[str]:
        """Generate reactive goals based on the event type."""
        goals = []
        timestamp = int(time.time())
        event_type = LifeEventType(event.type)

        # Marriage generates "support spouse" goals
        if event_type == LifeEventType.MARRIAGE:
            for agent_id in [event.primary_agent_id, event.secondary_agent_id]:
                if agent_id:
                    other_id = (
                        event.secondary_agent_id
                        if agent_id == event.primary_agent_id
                        else event.primary_agent_id
                    )
                    goal = Goal(
                        agent_id=agent_id,
                        type="help_others",
                        description=f"Support and spend time with spouse",
                        priority=6,
                        target_id=other_id,
                        status="active",
                        created_at=timestamp,
                    )
                    self.db.add(goal)
                    goals.append(f"Created spouse-support goal for {agent_id}")

        # Rivalry generates "confront" or "prove superiority" goals
        elif event_type == LifeEventType.RIVALRY:
            goal = Goal(
                agent_id=event.primary_agent_id,
                type="confront",
                description=f"Prove superiority over rival",
                priority=5,
                target_id=event.secondary_agent_id,
                status="active",
                created_at=timestamp,
            )
            self.db.add(goal)
            goals.append(f"Created rivalry goal for {event.primary_agent_id}")

        # Mentorship generates learning goals for student
        elif event_type == LifeEventType.MENTORSHIP:
            if event.secondary_agent_id:
                effects = event.effects_dict
                trait = effects.get("mentorship_trait", "wisdom")
                goal = Goal(
                    agent_id=event.secondary_agent_id,
                    type="gain_knowledge",
                    description=f"Learn {trait} from mentor",
                    priority=6,
                    target_id=event.primary_agent_id,
                    status="active",
                    created_at=timestamp,
                )
                self.db.add(goal)
                goals.append(f"Created learning goal for {event.secondary_agent_id}")

        # Betrayal generates revenge or avoidance goals
        elif event_type == LifeEventType.BETRAYAL:
            agent = self.db.query(Agent).filter(Agent.id == event.secondary_agent_id).first()
            if agent:
                traits = agent.traits_dict
                # Courageous agents seek revenge, others avoid
                if traits.get("courage", 5) >= 7:
                    goal = Goal(
                        agent_id=event.secondary_agent_id,
                        type="seek_revenge",
                        description=f"Get revenge for betrayal",
                        priority=7,
                        target_id=event.primary_agent_id,
                        status="active",
                        created_at=timestamp,
                    )
                else:
                    goal = Goal(
                        agent_id=event.secondary_agent_id,
                        type="avoid_danger",
                        description=f"Avoid the one who betrayed me",
                        priority=6,
                        target_id=event.primary_agent_id,
                        status="active",
                        created_at=timestamp,
                    )
                self.db.add(goal)
                goals.append(f"Created reaction goal for {event.secondary_agent_id}")

        return goals

    def _apply_trait_changes(self, event: LifeEvent) -> list[dict]:
        """Apply trait modifications for transformation events."""
        changes = []
        effects = event.effects_dict

        agent = self.db.query(Agent).filter(Agent.id == event.primary_agent_id).first()
        if not agent:
            return changes

        trait_changes = effects.get("trait_changes", {})
        if not trait_changes:
            return changes

        traits = agent.traits_dict
        for trait, change in trait_changes.items():
            if trait in traits:
                old_val = traits[trait]
                new_val = max(1, min(10, old_val + change))
                traits[trait] = new_val
                changes.append({
                    "agent_id": agent.id,
                    "trait": trait,
                    "old_value": old_val,
                    "new_value": new_val,
                })

        agent.traits_dict = traits
        return changes

    def resolve_event(
        self,
        event: LifeEvent,
        outcome: str = "success",
    ) -> None:
        """Resolve an active life event."""
        event.status = LifeEventStatus.RESOLVED.value
        event.resolved_at = time.time()

        effects = event.effects_dict
        effects["outcome"] = outcome
        event.effects_dict = effects

    def check_event_resolutions(self) -> list[LifeEvent]:
        """Check for events that should be auto-resolved."""
        resolved = []

        # Mentorships resolve when student trait improves
        mentorships = (
            self.db.query(LifeEvent)
            .filter(
                LifeEvent.type == LifeEventType.MENTORSHIP.value,
                LifeEvent.status == LifeEventStatus.ACTIVE.value,
            )
            .all()
        )

        for mentorship in mentorships:
            effects = mentorship.effects_dict
            trait = effects.get("mentorship_trait")
            if not trait or not mentorship.secondary_agent_id:
                continue

            student = self.db.query(Agent).filter(Agent.id == mentorship.secondary_agent_id).first()
            mentor = self.db.query(Agent).filter(Agent.id == mentorship.primary_agent_id).first()

            if student and mentor:
                student_val = student.traits_dict.get(trait, 5)
                mentor_val = mentor.traits_dict.get(trait, 5)

                # Student has caught up to mentor
                if student_val >= mentor_val - 1:
                    self.resolve_event(mentorship, "graduated")
                    # Create graduation event
                    from hamlet.life_events.generator import LifeEventGenerator

                    generator = LifeEventGenerator(self.db)
                    graduation = generator._create_event(
                        LifeEventType.GRADUATION,
                        mentor.id,
                        student.id,
                    )
                    resolved.append(graduation)

        return resolved
