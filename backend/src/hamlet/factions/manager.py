"""Faction management system for creating and coordinating factions."""

import time
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db.models import Agent, Faction, FactionMembership, FactionRelationship
from hamlet.factions.types import (
    LOYALTY_MINIMUM,
    LOYALTY_THRESHOLD_LEADER,
    LOYALTY_THRESHOLD_OFFICER,
    MAX_MEMBERSHIPS,
    MIN_ACTIVE_MEMBERS,
    TRAIT_FACTION_PREFERENCES,
    FactionRelationType,
    FactionRole,
    FactionStatus,
    FactionType,
)


class FactionManager:
    """Manages faction creation, membership, and operations."""

    def __init__(self, db: Session):
        self.db = db

    def create_faction(
        self,
        name: str,
        founder_id: str,
        faction_type: FactionType = FactionType.SOCIAL,
        description: Optional[str] = None,
        beliefs: Optional[list[str]] = None,
        goals: Optional[list[str]] = None,
        location_id: Optional[str] = None,
    ) -> Faction:
        """Create a new faction with the given founder."""
        faction = Faction(
            name=name,
            description=description or f"A {faction_type.value} faction founded by {founder_id}",
            founder_id=founder_id,
            location_id=location_id,
            status=FactionStatus.FORMING.value,
            created_at=time.time(),
        )
        faction.beliefs_list = beliefs or []
        faction.goals_list = goals or []
        self.db.add(faction)
        self.db.flush()

        # Add founder as first member
        self.add_member(faction.id, founder_id, FactionRole.FOUNDER)

        return faction

    def add_member(
        self,
        faction_id: int,
        agent_id: str,
        role: FactionRole = FactionRole.RECRUIT,
        initial_loyalty: int = 50,
    ) -> Optional[FactionMembership]:
        """Add an agent to a faction."""
        # Check if agent is already in this faction
        existing = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.faction_id == faction_id,
                FactionMembership.agent_id == agent_id,
                FactionMembership.left_at.is_(None),
            )
            .first()
        )
        if existing:
            return None

        # Check max memberships
        current_memberships = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.agent_id == agent_id,
                FactionMembership.left_at.is_(None),
            )
            .count()
        )
        if current_memberships >= MAX_MEMBERSHIPS:
            return None

        membership = FactionMembership(
            faction_id=faction_id,
            agent_id=agent_id,
            role=role.value,
            loyalty=initial_loyalty,
            joined_at=time.time(),
        )
        self.db.add(membership)

        # Update faction status if reaching minimum members
        self._update_faction_status(faction_id)

        return membership

    def remove_member(
        self,
        faction_id: int,
        agent_id: str,
        expelled: bool = False,
    ) -> bool:
        """Remove an agent from a faction."""
        membership = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.faction_id == faction_id,
                FactionMembership.agent_id == agent_id,
                FactionMembership.left_at.is_(None),
            )
            .first()
        )
        if not membership:
            return False

        membership.left_at = time.time()
        if expelled:
            membership.role = FactionRole.OUTCAST.value

        self._update_faction_status(faction_id)
        return True

    def update_loyalty(
        self,
        faction_id: int,
        agent_id: str,
        change: int,
    ) -> Optional[int]:
        """Update an agent's loyalty to a faction."""
        membership = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.faction_id == faction_id,
                FactionMembership.agent_id == agent_id,
                FactionMembership.left_at.is_(None),
            )
            .first()
        )
        if not membership:
            return None

        membership.loyalty = max(0, min(100, membership.loyalty + change))

        # Check for automatic departure on very low loyalty
        if membership.loyalty < LOYALTY_MINIMUM:
            self.remove_member(faction_id, agent_id)
            return 0

        return membership.loyalty

    def promote_member(
        self,
        faction_id: int,
        agent_id: str,
    ) -> Optional[FactionRole]:
        """Promote a member to the next role level."""
        membership = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.faction_id == faction_id,
                FactionMembership.agent_id == agent_id,
                FactionMembership.left_at.is_(None),
            )
            .first()
        )
        if not membership:
            return None

        current_role = FactionRole(membership.role)
        new_role = None

        if current_role == FactionRole.RECRUIT:
            new_role = FactionRole.MEMBER
        elif current_role == FactionRole.MEMBER and membership.loyalty >= LOYALTY_THRESHOLD_OFFICER:
            new_role = FactionRole.OFFICER
        elif current_role == FactionRole.OFFICER and membership.loyalty >= LOYALTY_THRESHOLD_LEADER:
            # Can only become leader if no current leader
            has_leader = (
                self.db.query(FactionMembership)
                .filter(
                    FactionMembership.faction_id == faction_id,
                    FactionMembership.role == FactionRole.LEADER.value,
                    FactionMembership.left_at.is_(None),
                )
                .first()
            )
            if not has_leader:
                new_role = FactionRole.LEADER

        if new_role:
            membership.role = new_role.value
            return new_role
        return None

    def get_faction_members(
        self,
        faction_id: int,
        active_only: bool = True,
    ) -> list[FactionMembership]:
        """Get all members of a faction."""
        query = self.db.query(FactionMembership).filter(
            FactionMembership.faction_id == faction_id
        )
        if active_only:
            query = query.filter(FactionMembership.left_at.is_(None))
        return query.all()

    def get_agent_factions(
        self,
        agent_id: str,
        active_only: bool = True,
    ) -> list[FactionMembership]:
        """Get all factions an agent belongs to."""
        query = self.db.query(FactionMembership).filter(
            FactionMembership.agent_id == agent_id
        )
        if active_only:
            query = query.filter(FactionMembership.left_at.is_(None))
        return query.all()

    def set_faction_relationship(
        self,
        faction_1_id: int,
        faction_2_id: int,
        relation_type: FactionRelationType,
        score_change: int = 0,
        event_description: Optional[str] = None,
    ) -> FactionRelationship:
        """Set or update the relationship between two factions."""
        # Ensure consistent ordering
        if faction_1_id > faction_2_id:
            faction_1_id, faction_2_id = faction_2_id, faction_1_id

        relationship = (
            self.db.query(FactionRelationship)
            .filter(
                FactionRelationship.faction_1_id == faction_1_id,
                FactionRelationship.faction_2_id == faction_2_id,
            )
            .first()
        )

        if not relationship:
            relationship = FactionRelationship(
                faction_1_id=faction_1_id,
                faction_2_id=faction_2_id,
                type=relation_type.value,
                score=0,
            )
            self.db.add(relationship)

        relationship.type = relation_type.value
        relationship.score = max(-100, min(100, relationship.score + score_change))

        if event_description:
            history = relationship.history_list
            history.append(f"[{time.time()}] {event_description}")
            relationship.history_list = history[-20:]  # Keep last 20 events

        return relationship

    def get_faction_relationship(
        self,
        faction_1_id: int,
        faction_2_id: int,
    ) -> Optional[FactionRelationship]:
        """Get the relationship between two factions."""
        if faction_1_id > faction_2_id:
            faction_1_id, faction_2_id = faction_2_id, faction_1_id

        return (
            self.db.query(FactionRelationship)
            .filter(
                FactionRelationship.faction_1_id == faction_1_id,
                FactionRelationship.faction_2_id == faction_2_id,
            )
            .first()
        )

    def get_compatible_faction_type(
        self,
        agent: Agent,
    ) -> FactionType:
        """Determine the best faction type for an agent based on traits."""
        traits = agent.traits_dict
        type_scores: dict[FactionType, float] = {t: 0.0 for t in FactionType}

        for trait, value in traits.items():
            if trait in TRAIT_FACTION_PREFERENCES:
                for faction_type in TRAIT_FACTION_PREFERENCES[trait]:
                    type_scores[faction_type] += value * 0.1

        return max(type_scores, key=type_scores.get)

    def should_form_faction(
        self,
        agent: Agent,
    ) -> bool:
        """Determine if an agent should try to form a new faction."""
        # Check if agent is already in too many factions
        current = self.get_agent_factions(agent.id)
        if len(current) >= MAX_MEMBERSHIPS:
            return False

        # Ambitious and charismatic agents are more likely to form factions
        traits = agent.traits_dict
        ambition = traits.get("ambition", 5)
        charm = traits.get("charm", 5)

        # Base probability based on traits
        probability = (ambition + charm) / 20.0

        return probability > 0.6

    def should_join_faction(
        self,
        agent: Agent,
        faction: Faction,
    ) -> bool:
        """Determine if an agent should join a faction."""
        # Check if agent can join more factions
        current = self.get_agent_factions(agent.id)
        if len(current) >= MAX_MEMBERSHIPS:
            return False

        # Check if already a member
        for membership in current:
            if membership.faction_id == faction.id:
                return False

        # Check if beliefs align
        agent_traits = agent.traits_dict
        faction_beliefs = faction.beliefs_list

        # Simple alignment check - could be made more sophisticated
        score = 0.5  # Base probability

        # Empathetic agents more likely to join social factions
        if "community" in str(faction_beliefs).lower():
            score += agent_traits.get("empathy", 5) * 0.05

        # Ambitious agents more likely to join political factions
        if "power" in str(faction_beliefs).lower() or "influence" in str(faction_beliefs).lower():
            score += agent_traits.get("ambition", 5) * 0.05

        return score > 0.6

    def _update_faction_status(self, faction_id: int) -> None:
        """Update faction status based on member count."""
        faction = self.db.query(Faction).filter(Faction.id == faction_id).first()
        if not faction:
            return

        active_members = (
            self.db.query(FactionMembership)
            .filter(
                FactionMembership.faction_id == faction_id,
                FactionMembership.left_at.is_(None),
            )
            .count()
        )

        if active_members == 0:
            faction.status = FactionStatus.DISBANDED.value
        elif active_members < MIN_ACTIVE_MEMBERS:
            if faction.status == FactionStatus.ACTIVE.value:
                faction.status = FactionStatus.STRUGGLING.value
            else:
                faction.status = FactionStatus.FORMING.value
        elif active_members >= MIN_ACTIVE_MEMBERS:
            faction.status = FactionStatus.ACTIVE.value

    def get_all_factions(self, active_only: bool = True) -> list[Faction]:
        """Get all factions."""
        query = self.db.query(Faction)
        if active_only:
            query = query.filter(Faction.status != FactionStatus.DISBANDED.value)
        return query.all()

    def get_faction_context_for_agent(self, agent_id: str) -> str:
        """Get faction context string for LLM prompts."""
        memberships = self.get_agent_factions(agent_id)
        if not memberships:
            return "You are not a member of any faction or alliance."

        context_parts = []
        for membership in memberships:
            faction = self.db.query(Faction).filter(Faction.id == membership.faction_id).first()
            if faction:
                role = FactionRole(membership.role)
                context_parts.append(
                    f"- {faction.name} ({role.value}): {faction.description or 'A local faction'}. "
                    f"Loyalty: {membership.loyalty}%. Goals: {', '.join(faction.goals_list[:3]) or 'none specified'}."
                )

        return "Your faction memberships:\n" + "\n".join(context_parts)
