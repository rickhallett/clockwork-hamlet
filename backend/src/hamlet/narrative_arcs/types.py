"""Narrative arc type definitions and constants."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ArcType(str, Enum):
    """Types of narrative arcs."""

    # Relationship arcs
    LOVE_STORY = "love_story"  # Romance from meeting to commitment
    RIVALRY = "rivalry"  # Competition and conflict
    MENTORSHIP = "mentorship"  # Teaching and growth
    FRIENDSHIP = "friendship"  # Bond formation

    # Personal journey arcs
    RISE_TO_POWER = "rise_to_power"  # Ambition and achievement
    FALL_FROM_GRACE = "fall_from_grace"  # Downfall narrative
    REDEMPTION = "redemption"  # Recovery from failure
    COMING_OF_AGE = "coming_of_age"  # Personal growth

    # Conflict arcs
    BETRAYAL = "betrayal"  # Trust broken and consequences
    FEUD = "feud"  # Extended conflict
    MYSTERY = "mystery"  # Investigation and discovery

    # Community arcs
    FACTION_RISE = "faction_rise"  # Group gaining power
    FACTION_WAR = "faction_war"  # Inter-faction conflict


class ArcStatus(str, Enum):
    """Status of a narrative arc."""

    FORMING = "forming"  # Just detected, gathering events
    RISING_ACTION = "rising_action"  # Building tension
    CLIMAX = "climax"  # Peak conflict/tension
    FALLING_ACTION = "falling_action"  # Resolution in progress
    RESOLUTION = "resolution"  # Concluded
    ABANDONED = "abandoned"  # Arc fizzled out


class ActStatus(str, Enum):
    """Status of an act within a narrative arc."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"


@dataclass
class Act:
    """An act within a narrative arc."""

    number: int  # 0-4: exposition, rising_action, climax, falling_action, resolution
    status: ActStatus
    events: list[int]  # Event IDs
    key_moments: list[str]  # Descriptions of important moments
    turning_point: Optional[str]  # Event that advances to next act

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage."""
        return {
            "number": self.number,
            "status": self.status.value,
            "events": self.events,
            "key_moments": self.key_moments,
            "turning_point": self.turning_point,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Act":
        """Create from dictionary."""
        return cls(
            number=data.get("number", 0),
            status=ActStatus(data.get("status", "not_started")),
            events=data.get("events", []),
            key_moments=data.get("key_moments", []),
            turning_point=data.get("turning_point"),
        )


# Act names for human-readable output
ACT_NAMES = {
    0: "Exposition",
    1: "Rising Action",
    2: "Climax",
    3: "Falling Action",
    4: "Resolution",
}

# Arc significance modifiers
ARC_BASE_SIGNIFICANCE: dict[ArcType, int] = {
    ArcType.LOVE_STORY: 8,
    ArcType.RIVALRY: 6,
    ArcType.MENTORSHIP: 5,
    ArcType.FRIENDSHIP: 4,
    ArcType.RISE_TO_POWER: 7,
    ArcType.FALL_FROM_GRACE: 8,
    ArcType.REDEMPTION: 9,
    ArcType.COMING_OF_AGE: 5,
    ArcType.BETRAYAL: 8,
    ArcType.FEUD: 7,
    ArcType.MYSTERY: 6,
    ArcType.FACTION_RISE: 6,
    ArcType.FACTION_WAR: 9,
}

# Arc themes and descriptions
ARC_THEMES: dict[ArcType, str] = {
    ArcType.LOVE_STORY: "A tale of hearts drawn together across the village",
    ArcType.RIVALRY: "Two souls locked in competition for supremacy",
    ArcType.MENTORSHIP: "The passing of wisdom from one generation to the next",
    ArcType.FRIENDSHIP: "The forging of an unbreakable bond",
    ArcType.RISE_TO_POWER: "An ambitious climb to the heights of influence",
    ArcType.FALL_FROM_GRACE: "The tragic descent from prosperity",
    ArcType.REDEMPTION: "A journey from darkness back to light",
    ArcType.COMING_OF_AGE: "The transformation from innocence to experience",
    ArcType.BETRAYAL: "When trust shatters and consequences unfold",
    ArcType.FEUD: "An ongoing battle that consumes all involved",
    ArcType.MYSTERY: "Secrets waiting to be uncovered",
    ArcType.FACTION_RISE: "A group's ascent to prominence",
    ArcType.FACTION_WAR: "Factions clash in a struggle for dominance",
}

# Life event to arc type mappings
LIFE_EVENT_ARC_MAPPINGS: dict[str, list[ArcType]] = {
    "marriage": [ArcType.LOVE_STORY],
    "friendship": [ArcType.FRIENDSHIP],
    "mentorship": [ArcType.MENTORSHIP, ArcType.COMING_OF_AGE],
    "rivalry": [ArcType.RIVALRY],
    "feud": [ArcType.FEUD],
    "betrayal": [ArcType.BETRAYAL, ArcType.FALL_FROM_GRACE],
    "reconciliation": [ArcType.REDEMPTION],
}

# Relationship score patterns for arc detection
ARC_RELATIONSHIP_PATTERNS: dict[ArcType, dict] = {
    ArcType.LOVE_STORY: {
        "min_score": 6,
        "score_trend": "increasing",
        "min_interactions": 8,
    },
    ArcType.RIVALRY: {
        "max_score": -3,
        "score_trend": "decreasing",
        "min_interactions": 5,
    },
    ArcType.FRIENDSHIP: {
        "min_score": 4,
        "score_trend": "increasing",
        "min_interactions": 5,
    },
}

# Goal patterns for arc detection
ARC_GOAL_PATTERNS: dict[ArcType, list[str]] = {
    ArcType.RISE_TO_POWER: ["gain_power", "gain_wealth"],
    ArcType.MENTORSHIP: ["gain_knowledge", "help_others"],
    ArcType.REDEMPTION: ["apologize", "help_others"],
}

# Arc progression requirements
ARC_ACT_REQUIREMENTS: dict[ArcType, dict[int, dict]] = {
    ArcType.LOVE_STORY: {
        0: {"min_interactions": 2, "description": "Initial meeting and attraction"},
        1: {"min_interactions": 5, "description": "Growing closeness"},
        2: {"event_type": "marriage", "description": "Declaration of love"},
        3: {"min_interactions": 2, "description": "Building a life together"},
        4: {"time_elapsed": True, "description": "Established partnership"},
    },
    ArcType.RIVALRY: {
        0: {"min_interactions": 1, "description": "First conflict"},
        1: {"min_interactions": 3, "description": "Escalating tensions"},
        2: {"event_type": "confrontation", "description": "Direct confrontation"},
        3: {"score_change": True, "description": "Aftermath"},
        4: {"event_type": "resolution", "description": "New equilibrium"},
    },
    ArcType.MENTORSHIP: {
        0: {"event_type": "mentorship", "description": "Taking on a student"},
        1: {"min_interactions": 5, "description": "Teaching and learning"},
        2: {"trait_improvement": True, "description": "Student's breakthrough"},
        3: {"min_interactions": 2, "description": "Growing independence"},
        4: {"event_type": "graduation", "description": "Student surpasses teacher"},
    },
}

# Templates for arc titles
ARC_TITLE_TEMPLATES: dict[ArcType, list[str]] = {
    ArcType.LOVE_STORY: [
        "The Romance of {agent1} and {agent2}",
        "{agent1}'s Heart",
        "A Village Love Story",
    ],
    ArcType.RIVALRY: [
        "The Rivalry Between {agent1} and {agent2}",
        "{agent1} vs {agent2}",
        "Clash of Wills",
    ],
    ArcType.MENTORSHIP: [
        "{agent1}'s Apprentice",
        "The Teachings of {agent1}",
        "Master and Student",
    ],
    ArcType.RISE_TO_POWER: [
        "The Rise of {agent1}",
        "{agent1}'s Ascent",
        "A Climb to Power",
    ],
    ArcType.BETRAYAL: [
        "The Betrayal",
        "Trust Broken",
        "When {agent1} Fell",
    ],
    ArcType.REDEMPTION: [
        "The Redemption of {agent1}",
        "{agent1}'s Second Chance",
        "Rising from the Ashes",
    ],
}
