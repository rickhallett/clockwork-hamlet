"""Dramatic events system for village life simulation.

Implements:
- LIFE-26: Conflict escalation system
- LIFE-27: Secret revelation mechanics
- LIFE-28: Romantic subplot progression
- LIFE-29: Village-wide event triggers
"""

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from sqlalchemy.orm import Session

from hamlet.db import Agent, Event, Memory, Relationship


class ConflictStage(str, Enum):
    """Stages of conflict escalation."""

    TENSION = "tension"  # Score -1 to -3: Mild disagreement
    DISPUTE = "dispute"  # Score -4 to -6: Open conflict
    FEUD = "feud"  # Score -7 to -9: Serious enmity
    VENDETTA = "vendetta"  # Score -10: All-out war


class SecretType(str, Enum):
    """Types of secrets that can be revealed."""

    PERSONAL = "personal"  # Embarrassing personal info
    ROMANTIC = "romantic"  # Secret crushes/affairs
    SCANDAL = "scandal"  # Professional/social misconduct
    CONSPIRACY = "conspiracy"  # Hidden plots or schemes
    IDENTITY = "identity"  # Hidden past or true nature


class RomanceStage(str, Enum):
    """Stages of romantic progression."""

    STRANGERS = "strangers"  # No romantic interest
    CURIOUS = "curious"  # Slight interest, watching
    ATTRACTION = "attraction"  # Clear interest, nervous around them
    COURTSHIP = "courtship"  # Active pursuit
    CONFESSION = "confession"  # Feelings declared
    RELATIONSHIP = "relationship"  # Together
    COMPLICATED = "complicated"  # Issues/jealousy


@dataclass
class ConflictEvent:
    """A conflict escalation event."""

    aggressor_id: str
    target_id: str
    trigger: str
    old_stage: ConflictStage
    new_stage: ConflictStage
    witnesses: list[str] = field(default_factory=list)


@dataclass
class SecretRevelation:
    """A secret being revealed."""

    secret_holder_id: str
    revealer_id: str
    secret_type: SecretType
    secret_content: str
    audience_ids: list[str] = field(default_factory=list)
    was_intentional: bool = False


@dataclass
class RomanceEvent:
    """A romantic subplot event."""

    suitor_id: str
    beloved_id: str
    old_stage: RomanceStage
    new_stage: RomanceStage
    event_type: str  # "glance", "conversation", "gift", "confession", etc.
    reciprocated: bool = False


@dataclass
class VillageEvent:
    """A village-wide dramatic event."""

    event_type: str
    description: str
    affected_agents: list[str] = field(default_factory=list)
    location_id: Optional[str] = None
    significance: int = 3


# =============================================================================
# LIFE-26: Conflict Escalation System
# =============================================================================

def get_conflict_stage(score: int) -> ConflictStage:
    """Determine conflict stage from relationship score."""
    if score >= -3:
        return ConflictStage.TENSION
    elif score >= -6:
        return ConflictStage.DISPUTE
    elif score >= -9:
        return ConflictStage.FEUD
    else:
        return ConflictStage.VENDETTA


def check_conflict_escalation(
    agent: Agent,
    target: Agent,
    relationship: Relationship,
    trigger_event: str,
    db: Session,
) -> Optional[ConflictEvent]:
    """Check if a conflict should escalate based on recent interactions.

    Escalation factors:
    - Frequency of negative interactions
    - Severity of the trigger event
    - Agent's courage and temperament
    - Witness presence (public humiliation escalates faster)
    """
    current_score = relationship.score
    old_stage = get_conflict_stage(current_score)

    # Get agent traits
    traits = agent.traits_dict
    courage = traits.get("courage", 5)
    discretion = traits.get("discretion", 5)
    empathy = traits.get("empathy", 5)

    # Base escalation chance
    escalation_chance = 0.0

    # Trigger severity affects escalation
    severe_triggers = ["confronted", "accused", "insulted", "betrayed", "humiliated"]
    moderate_triggers = ["argued", "disagreed", "complained", "criticized"]

    trigger_lower = trigger_event.lower()
    if any(t in trigger_lower for t in severe_triggers):
        escalation_chance += 0.4
    elif any(t in trigger_lower for t in moderate_triggers):
        escalation_chance += 0.2

    # Personality modifiers
    escalation_chance += (courage - 5) * 0.05  # Brave agents escalate more
    escalation_chance -= (discretion - 5) * 0.03  # Discreet agents hold back
    escalation_chance -= (empathy - 5) * 0.04  # Empathetic agents de-escalate

    # Already hostile relationships escalate faster
    if current_score < -3:
        escalation_chance += 0.15
    if current_score < -6:
        escalation_chance += 0.15

    # Check recent conflict history
    history = relationship.history_list
    recent_conflicts = sum(1 for h in history[-5:] if any(
        word in h.lower() for word in ["confront", "argue", "insult", "accuse"]
    ))
    escalation_chance += recent_conflicts * 0.1

    # Roll for escalation
    if random.random() < min(escalation_chance, 0.8):  # Cap at 80%
        # Calculate score decrease
        decrease = random.randint(1, 3)
        new_score = max(-10, current_score - decrease)
        new_stage = get_conflict_stage(new_score)

        if new_stage != old_stage:
            # Update relationship
            relationship.score = new_score

            # Add to history
            history = relationship.history_list
            history.append(f"conflict escalated to {new_stage.value}")
            relationship.history_list = history

            return ConflictEvent(
                aggressor_id=agent.id,
                target_id=target.id,
                trigger=trigger_event,
                old_stage=old_stage,
                new_stage=new_stage,
            )

    return None


def generate_conflict_escalation_dialogue(
    agent: Agent,
    target: Agent,
    event: ConflictEvent,
) -> str:
    """Generate dramatic dialogue for a conflict escalation."""
    agent_name = agent.name.split()[0]  # First name
    target_name = target.name.split()[0]

    escalation_lines = {
        ConflictStage.DISPUTE: [
            f'"{target_name}, we need to talk about this. I won\'t let it slide anymore."',
            f'"I\'ve had enough of your behavior, {target_name}. This ends now."',
            f'"Don\'t think I haven\'t noticed what you\'ve been doing, {target_name}."',
        ],
        ConflictStage.FEUD: [
            f'"This isn\'t over between us, {target_name}. Mark my words."',
            f'"You\'ve made an enemy today, {target_name}. I won\'t forget this."',
            f'"The whole village will know what kind of person you really are."',
        ],
        ConflictStage.VENDETTA: [
            f'"I will not rest until you answer for what you\'ve done."',
            f'"You\'ve crossed a line, {target_name}. There\'s no going back now."',
            f'"One of us will have to leave this village before this is over."',
        ],
    }

    lines = escalation_lines.get(event.new_stage, escalation_lines[ConflictStage.DISPUTE])
    return random.choice(lines)


def process_conflict_aftermath(
    event: ConflictEvent,
    db: Session,
    agents: dict[str, Agent],
) -> list[Memory]:
    """Process the aftermath of a conflict escalation.

    Creates memories for:
    - The aggressor
    - The target
    - Any witnesses
    """
    memories = []
    timestamp = int(time.time())

    aggressor = agents.get(event.aggressor_id)
    target = agents.get(event.target_id)

    if not aggressor or not target:
        return memories

    # Aggressor memory
    aggressor_memory = Memory(
        agent_id=event.aggressor_id,
        timestamp=timestamp,
        type="working",
        content=f"My conflict with {target.name} has escalated. "
                f"This is now a {event.new_stage.value}.",
        significance=7 if event.new_stage in [ConflictStage.FEUD, ConflictStage.VENDETTA] else 6,
    )
    memories.append(aggressor_memory)
    db.add(aggressor_memory)

    # Target memory
    target_memory = Memory(
        agent_id=event.target_id,
        timestamp=timestamp,
        type="working",
        content=f"{aggressor.name} has made their hostility clear. "
                f"This has become a {event.new_stage.value}.",
        significance=8,  # Higher for the target - they're under attack
    )
    memories.append(target_memory)
    db.add(target_memory)

    # Witness memories
    for witness_id in event.witnesses:
        witness = agents.get(witness_id)
        if witness:
            witness_memory = Memory(
                agent_id=witness_id,
                timestamp=timestamp,
                type="working",
                content=f"I witnessed a serious confrontation between {aggressor.name} "
                        f"and {target.name}. Things are getting ugly.",
                significance=5,
            )
            memories.append(witness_memory)
            db.add(witness_memory)

    return memories


# =============================================================================
# LIFE-27: Secret Revelation Mechanics
# =============================================================================

# Pre-defined secrets for seeded characters (can be extended)
CHARACTER_SECRETS = {
    "theodore": {
        "type": SecretType.SCANDAL,
        "content": "The prize cheese from last year's festival was store-bought from the city",
        "holders": ["theodore"],  # Who knows this secret
    },
    "edmund": {
        "type": SecretType.IDENTITY,
        "content": "Edmund is secretly forging something mysterious at night",
        "holders": ["edmund", "rosalind"],  # Rosalind noticed from the inn
    },
    "thomas": {
        "type": SecretType.ROMANTIC,
        "content": "Thomas has been in love with Agnes for years but never confessed",
        "holders": ["thomas", "william"],  # Old Will noticed
    },
    "rosalind": {
        "type": SecretType.ROMANTIC,
        "content": "Rosalind has a secret crush on Edmund the blacksmith",
        "holders": ["rosalind"],
    },
    "father_cornelius": {
        "type": SecretType.CONSPIRACY,
        "content": "Father Cornelius has been secretly investigating the forest lights",
        "holders": ["father_cornelius", "william"],
    },
}


def check_secret_discovery(
    agent: Agent,
    target: Agent,
    interaction_type: str,
    db: Session,
) -> Optional[SecretRevelation]:
    """Check if an agent discovers a secret during an interaction.

    Discovery factors:
    - Agent's perception and curiosity traits
    - Type of interaction (investigation, gossip, observation)
    - Whether agent is already suspicious
    """
    traits = agent.traits_dict
    perception = traits.get("perception", 5)
    curiosity = traits.get("curiosity", 5)
    discretion = traits.get("discretion", 5)

    # Base discovery chance
    discovery_chance = 0.0

    # Interaction type affects discovery
    if interaction_type in ["investigate", "observe"]:
        discovery_chance += 0.25
    elif interaction_type in ["gossip", "talk"]:
        discovery_chance += 0.15
    elif interaction_type == "confront":
        discovery_chance += 0.20

    # Personality modifiers
    discovery_chance += (perception - 5) * 0.04
    discovery_chance += (curiosity - 5) * 0.03

    # Check if target has a secret
    target_secret = CHARACTER_SECRETS.get(target.id)
    if not target_secret:
        return None

    # Check if agent already knows the secret
    if agent.id in target_secret.get("holders", []):
        return None

    # Roll for discovery
    if random.random() < min(discovery_chance, 0.4):  # Cap at 40%
        # Agent discovers the secret
        return SecretRevelation(
            secret_holder_id=target.id,
            revealer_id=target.id,  # Discovered, not told
            secret_type=target_secret["type"],
            secret_content=target_secret["content"],
            audience_ids=[agent.id],
            was_intentional=False,
        )

    return None


def spread_secret(
    revealer: Agent,
    secret: SecretRevelation,
    audience: list[Agent],
    db: Session,
) -> list[Memory]:
    """Spread a secret to an audience, creating memories and updating knowledge."""
    memories = []
    timestamp = int(time.time())

    # Revealer's discretion affects how they tell it
    traits = revealer.traits_dict
    discretion = traits.get("discretion", 5)

    # Create memories for audience
    for listener in audience:
        # Check if listener already knows
        secret_data = CHARACTER_SECRETS.get(secret.secret_holder_id)
        if secret_data and listener.id in secret_data.get("holders", []):
            continue

        # Significance based on secret type
        significance_map = {
            SecretType.PERSONAL: 5,
            SecretType.ROMANTIC: 6,
            SecretType.SCANDAL: 8,
            SecretType.CONSPIRACY: 7,
            SecretType.IDENTITY: 9,
        }
        significance = significance_map.get(secret.secret_type, 6)

        memory = Memory(
            agent_id=listener.id,
            timestamp=timestamp,
            type="working",
            content=f"{revealer.name} told me a secret: {secret.secret_content}",
            significance=significance,
        )
        memories.append(memory)
        db.add(memory)

        # Update who knows the secret
        if secret_data:
            secret_data["holders"].append(listener.id)

    # Create memory for revealer
    listener_names = [a.name for a in audience[:3]]
    if len(audience) > 3:
        listener_names.append(f"and {len(audience) - 3} others")

    revealer_memory = Memory(
        agent_id=revealer.id,
        timestamp=timestamp,
        type="working",
        content=f"I shared a secret about {secret.secret_holder_id} with {', '.join(listener_names)}",
        significance=4 if discretion < 5 else 5,  # Low discretion = less memorable (they do it often)
    )
    memories.append(revealer_memory)
    db.add(revealer_memory)

    return memories


def check_secret_spread_impulse(
    agent: Agent,
    secret_holder_id: str,
) -> bool:
    """Check if an agent feels compelled to spread a secret they know.

    Based on:
    - Discretion trait (low = more likely to gossip)
    - Relationship with secret holder
    - How juicy the secret is
    """
    traits = agent.traits_dict
    discretion = traits.get("discretion", 5)

    # Low discretion means high gossip tendency
    gossip_chance = (10 - discretion) * 0.08

    # Check relationship - enemies' secrets spread faster
    # This would need relationship lookup in full implementation

    return random.random() < gossip_chance


def generate_secret_reaction(
    agent: Agent,
    secret: SecretRevelation,
) -> str:
    """Generate reaction dialogue when someone learns a secret."""
    traits = agent.traits_dict
    discretion = traits.get("discretion", 5)
    empathy = traits.get("empathy", 5)

    if secret.secret_type == SecretType.SCANDAL:
        if discretion < 4:
            return '"I KNEW something was off! Everyone needs to hear about this!"'
        elif empathy > 6:
            return '"Oh my... that\'s terrible. Should we really be talking about this?"'
        else:
            return '"Well, well, well. That explains a lot, doesn\'t it?"'

    elif secret.secret_type == SecretType.ROMANTIC:
        if empathy > 6:
            return '"Oh, how romantic... and tragic. I hope it works out."'
        else:
            return '"Really? I never would have guessed. How... interesting."'

    elif secret.secret_type == SecretType.IDENTITY:
        return '"Wait, what? I had no idea... Who else knows about this?"'

    return '"I don\'t know what to say to that."'


# =============================================================================
# LIFE-28: Romantic Subplot Progression
# =============================================================================

def get_romance_stage(
    suitor: Agent,
    beloved: Agent,
    relationship: Optional[Relationship],
) -> RomanceStage:
    """Determine the current romance stage between two agents."""
    if not relationship:
        return RomanceStage.STRANGERS

    score = relationship.score
    rel_type = relationship.type
    history = relationship.history_list

    # Check for relationship markers
    if rel_type == "spouse":
        return RomanceStage.RELATIONSHIP

    # Check history for romantic indicators
    romantic_history = [h for h in history if any(
        word in h.lower() for word in ["romantic", "love", "confess", "crush", "attracted"]
    )]

    if any("complicated" in h.lower() for h in history):
        return RomanceStage.COMPLICATED

    if any("confess" in h.lower() for h in history) and score >= 5:
        return RomanceStage.RELATIONSHIP

    if any("confess" in h.lower() for h in history):
        return RomanceStage.CONFESSION

    if score >= 6 and romantic_history:
        return RomanceStage.COURTSHIP

    if score >= 4 and romantic_history:
        return RomanceStage.ATTRACTION

    if score >= 2 and len(romantic_history) > 0:
        return RomanceStage.CURIOUS

    return RomanceStage.STRANGERS


def check_romantic_progression(
    suitor: Agent,
    beloved: Agent,
    relationship: Relationship,
    interaction_type: str,
    db: Session,
) -> Optional[RomanceEvent]:
    """Check if a romantic subplot should progress.

    Progression factors:
    - Charm and empathy traits
    - Current relationship stage
    - Type of interaction
    - Whether beloved is receptive
    """
    current_stage = get_romance_stage(suitor, beloved, relationship)

    # Can't progress from relationship (that's the end goal) or strangers (need some connection)
    if current_stage in [RomanceStage.RELATIONSHIP, RomanceStage.STRANGERS]:
        return None

    traits = suitor.traits_dict
    charm = traits.get("charm", 5)
    courage = traits.get("courage", 5)

    beloved_traits = beloved.traits_dict
    beloved_empathy = beloved_traits.get("empathy", 5)

    # Base progression chance
    progression_chance = 0.0

    # Interaction type matters
    romantic_interactions = ["talk", "help", "give", "confess"]
    if interaction_type in romantic_interactions:
        progression_chance += 0.15

    # Personality modifiers
    progression_chance += (charm - 5) * 0.04
    progression_chance += (courage - 5) * 0.02  # Courage to make a move

    # Higher stages are harder to progress
    stage_difficulty = {
        RomanceStage.CURIOUS: 0.0,
        RomanceStage.ATTRACTION: 0.05,
        RomanceStage.COURTSHIP: 0.10,
        RomanceStage.CONFESSION: 0.15,
        RomanceStage.COMPLICATED: 0.20,
    }
    progression_chance -= stage_difficulty.get(current_stage, 0)

    # Roll for progression
    if random.random() < min(progression_chance, 0.25):  # Cap at 25%
        # Determine next stage
        stage_order = [
            RomanceStage.STRANGERS,
            RomanceStage.CURIOUS,
            RomanceStage.ATTRACTION,
            RomanceStage.COURTSHIP,
            RomanceStage.CONFESSION,
            RomanceStage.RELATIONSHIP,
        ]

        current_index = stage_order.index(current_stage)
        if current_index < len(stage_order) - 1:
            new_stage = stage_order[current_index + 1]

            # Check if reciprocated (beloved's feelings)
            beloved_feelings = relationship.score + (beloved_empathy - 5)
            reciprocated = beloved_feelings >= 4 or random.random() < 0.3

            # Update relationship history
            history = relationship.history_list
            history.append(f"romantic interest: {new_stage.value}")
            relationship.history_list = history

            # Determine event type based on stage
            event_types = {
                RomanceStage.CURIOUS: "lingering glance",
                RomanceStage.ATTRACTION: "nervous conversation",
                RomanceStage.COURTSHIP: "romantic gesture",
                RomanceStage.CONFESSION: "declaration of feelings",
                RomanceStage.RELATIONSHIP: "mutual commitment",
            }

            return RomanceEvent(
                suitor_id=suitor.id,
                beloved_id=beloved.id,
                old_stage=current_stage,
                new_stage=new_stage,
                event_type=event_types.get(new_stage, "romantic moment"),
                reciprocated=reciprocated,
            )

    return None


def generate_romance_dialogue(
    suitor: Agent,
    beloved: Agent,
    event: RomanceEvent,
) -> str:
    """Generate romantic dialogue for a subplot progression."""
    suitor_name = suitor.name.split()[0]
    beloved_name = beloved.name.split()[0]

    if event.new_stage == RomanceStage.CURIOUS:
        return f'{suitor_name}\'s eyes linger on {beloved_name} a moment longer than necessary.'

    elif event.new_stage == RomanceStage.ATTRACTION:
        return f'"{beloved_name}, I... I was wondering if you might..." {suitor_name} trails off, suddenly finding their shoes fascinating.'

    elif event.new_stage == RomanceStage.COURTSHIP:
        return f'"I brought you something, {beloved_name}. I thought of you when I saw it."'

    elif event.new_stage == RomanceStage.CONFESSION:
        if event.reciprocated:
            return f'"{beloved_name}, I can\'t keep this inside anymore. I... I have feelings for you."'
        else:
            return f'"{beloved_name}, I need to tell you something, even if it changes everything between us."'

    elif event.new_stage == RomanceStage.RELATIONSHIP:
        return f'{suitor_name} and {beloved_name} share a look that speaks volumes. The village will be talking.'

    return f'{suitor_name} and {beloved_name} share a meaningful moment.'


def process_romance_aftermath(
    event: RomanceEvent,
    db: Session,
    agents: dict[str, Agent],
) -> list[Memory]:
    """Process the aftermath of a romantic progression."""
    memories = []
    timestamp = int(time.time())

    suitor = agents.get(event.suitor_id)
    beloved = agents.get(event.beloved_id)

    if not suitor or not beloved:
        return memories

    # Significance increases with stage
    stage_significance = {
        RomanceStage.CURIOUS: 4,
        RomanceStage.ATTRACTION: 5,
        RomanceStage.COURTSHIP: 6,
        RomanceStage.CONFESSION: 8,
        RomanceStage.RELATIONSHIP: 9,
    }
    significance = stage_significance.get(event.new_stage, 5)

    # Suitor memory
    if event.reciprocated:
        suitor_content = f"Something special is developing between me and {beloved.name}. They seem to feel the same way."
    else:
        suitor_content = f"I'm drawn to {beloved.name}, but I'm not sure if they feel the same."

    suitor_memory = Memory(
        agent_id=event.suitor_id,
        timestamp=timestamp,
        type="working",
        content=suitor_content,
        significance=significance,
    )
    memories.append(suitor_memory)
    db.add(suitor_memory)

    # Beloved memory (if they noticed)
    if event.new_stage in [RomanceStage.ATTRACTION, RomanceStage.COURTSHIP,
                           RomanceStage.CONFESSION, RomanceStage.RELATIONSHIP]:
        if event.reciprocated:
            beloved_content = f"I think there's something between me and {suitor.name}. My heart races when they're near."
        else:
            beloved_content = f"{suitor.name} seems interested in me. I'm not sure how I feel about that."

        beloved_memory = Memory(
            agent_id=event.beloved_id,
            timestamp=timestamp,
            type="working",
            content=beloved_content,
            significance=significance - 1,  # Slightly less significant for beloved
        )
        memories.append(beloved_memory)
        db.add(beloved_memory)

    return memories


# =============================================================================
# LIFE-29: Village-Wide Event Triggers
# =============================================================================

class VillageEventType(str, Enum):
    """Types of village-wide events."""

    FESTIVAL = "festival"
    STORM = "storm"
    STRANGER_ARRIVAL = "stranger_arrival"
    ACCIDENT = "accident"
    DISCOVERY = "discovery"
    SCANDAL_PUBLIC = "scandal_public"
    WEDDING = "wedding"
    FUNERAL = "funeral"
    TOWN_MEETING = "town_meeting"
    MYSTERIOUS_OCCURRENCE = "mysterious_occurrence"


# Village-wide event templates
VILLAGE_EVENT_TEMPLATES = {
    VillageEventType.STORM: [
        {
            "description": "A fierce storm descends on the village, forcing everyone to seek shelter.",
            "location": "town_square",
            "significance": 2,
            "mood_effect": {"happiness": -1, "energy": -1},
        },
        {
            "description": "Thunder rolls across the hamlet as lightning illuminates the sky.",
            "location": None,  # Affects all locations
            "significance": 2,
            "mood_effect": {"energy": -1},
        },
    ],
    VillageEventType.STRANGER_ARRIVAL: [
        {
            "description": "A mysterious stranger has been spotted at the village edge.",
            "location": "forest_edge",
            "significance": 3,
            "mood_effect": {"happiness": 0},  # Depends on curiosity
        },
        {
            "description": "A traveling merchant arrives with exotic wares and stranger tales.",
            "location": "town_square",
            "significance": 2,
            "mood_effect": {"happiness": 1},
        },
    ],
    VillageEventType.DISCOVERY: [
        {
            "description": "Strange lights have been seen in the forest again.",
            "location": "forest_edge",
            "significance": 3,
            "mood_effect": {"happiness": -1},
        },
        {
            "description": "Something unusual has been found near the old cemetery.",
            "location": "cemetery",
            "significance": 3,
            "mood_effect": {},
        },
    ],
    VillageEventType.SCANDAL_PUBLIC: [
        {
            "description": "A shocking revelation has set tongues wagging throughout the village!",
            "location": "town_square",
            "significance": 3,
            "mood_effect": {"happiness": 1},  # Drama is entertaining
        },
    ],
    VillageEventType.TOWN_MEETING: [
        {
            "description": "The mayor has called an emergency town meeting.",
            "location": "town_square",
            "significance": 2,
            "mood_effect": {},
        },
        {
            "description": "The villagers gather to discuss an important matter.",
            "location": "church",
            "significance": 2,
            "mood_effect": {},
        },
    ],
    VillageEventType.MYSTERIOUS_OCCURRENCE: [
        {
            "description": "Something inexplicable has happened in the village.",
            "location": None,
            "significance": 3,
            "mood_effect": {"happiness": -1},
        },
        {
            "description": "Old Will swears he saw something in the shadows last night.",
            "location": "tavern",
            "significance": 2,
            "mood_effect": {},
        },
    ],
}


def trigger_village_event(
    event_type: VillageEventType,
    db: Session,
    agents: list[Agent],
    custom_description: str = None,
) -> VillageEvent:
    """Trigger a village-wide event affecting multiple agents.

    Args:
        event_type: Type of village event
        db: Database session
        agents: List of all agents to potentially affect
        custom_description: Optional custom description override
    """
    # Get event template
    templates = VILLAGE_EVENT_TEMPLATES.get(event_type, [])
    if not templates:
        template = {
            "description": custom_description or f"A {event_type.value} occurs in the village.",
            "location": "town_square",
            "significance": 2,
            "mood_effect": {},
        }
    else:
        template = random.choice(templates)

    description = custom_description or template["description"]
    location_id = template.get("location")
    significance = template.get("significance", 2)
    mood_effect = template.get("mood_effect", {})

    # Determine affected agents
    affected_ids = []

    if location_id:
        # Only agents at or near the location
        affected_agents = [a for a in agents if a.location_id == location_id]
        # Also include some random agents who "heard about it"
        other_agents = [a for a in agents if a.location_id != location_id]
        heard_count = min(len(other_agents), random.randint(1, 3))
        affected_agents.extend(random.sample(other_agents, heard_count))
    else:
        # Village-wide event affects everyone
        affected_agents = agents

    affected_ids = [a.id for a in affected_agents]

    # Apply mood effects
    for agent in affected_agents:
        mood = agent.mood_dict
        for key, delta in mood_effect.items():
            if key in mood:
                mood[key] = max(1, min(10, mood[key] + delta))
        agent.mood_dict = mood

    # Create memories for affected agents
    timestamp = int(time.time())
    for agent in affected_agents:
        # Significance varies by perception
        traits = agent.traits_dict
        perception = traits.get("perception", 5)
        agent_significance = significance + (1 if perception >= 7 else 0)

        memory = Memory(
            agent_id=agent.id,
            timestamp=timestamp,
            type="working",
            content=f"Village event: {description}",
            significance=agent_significance,
        )
        db.add(memory)

    # Record the event
    event_record = Event(
        timestamp=timestamp,
        type="system",
        actors="[]",  # Village-wide, no specific actors
        location_id=location_id,
        summary=description,
        detail=f"Village-wide event ({event_type.value}): {description}",
        significance=significance,
    )
    db.add(event_record)

    return VillageEvent(
        event_type=event_type.value,
        description=description,
        affected_agents=affected_ids,
        location_id=location_id,
        significance=significance,
    )


def check_random_village_event(
    db: Session,
    agents: list[Agent],
    current_hour: float,
    current_day: int,
) -> Optional[VillageEvent]:
    """Check if a random village event should occur.

    Events are more likely:
    - During certain hours (morning announcements, evening gatherings)
    - On certain days (weekly markets, etc.)
    - When drama has been building (conflicts, secrets)
    """
    # Base chance per tick
    event_chance = 0.02  # 2% per tick

    # Time-based modifiers
    if 8 <= current_hour <= 10:  # Morning - announcements
        event_chance += 0.02
    elif 18 <= current_hour <= 21:  # Evening - gatherings
        event_chance += 0.03

    # Day-based modifiers (e.g., market day)
    if current_day % 7 == 0:  # Weekly event
        event_chance += 0.05

    if random.random() < event_chance:
        # Weighted random event type
        event_weights = {
            VillageEventType.MYSTERIOUS_OCCURRENCE: 3,
            VillageEventType.DISCOVERY: 2,
            VillageEventType.TOWN_MEETING: 2,
            VillageEventType.STORM: 1,
            VillageEventType.STRANGER_ARRIVAL: 1,
        }

        total_weight = sum(event_weights.values())
        roll = random.random() * total_weight
        cumulative = 0

        for event_type, weight in event_weights.items():
            cumulative += weight
            if roll < cumulative:
                return trigger_village_event(event_type, db, agents)

        # Fallback
        return trigger_village_event(VillageEventType.MYSTERIOUS_OCCURRENCE, db, agents)

    return None


def cascade_village_event_effects(
    event: VillageEvent,
    db: Session,
    agents: dict[str, Agent],
) -> list[tuple[str, str]]:
    """Process cascading effects from a village event.

    Returns a list of (agent_id, reaction) tuples.
    """
    reactions = []

    for agent_id in event.affected_agents:
        agent = agents.get(agent_id)
        if not agent:
            continue

        traits = agent.traits_dict
        curiosity = traits.get("curiosity", 5)
        courage = traits.get("courage", 5)

        # High curiosity agents want to investigate
        if curiosity >= 7 and "mysterious" in event.description.lower():
            reactions.append((agent_id, "investigate"))

        # Low courage agents may hide
        if courage <= 3 and event.significance >= 3:
            reactions.append((agent_id, "hide"))

        # High charm agents spread the news
        charm = traits.get("charm", 5)
        discretion = traits.get("discretion", 5)
        if charm >= 7 and discretion <= 5:
            reactions.append((agent_id, "gossip"))

    return reactions
