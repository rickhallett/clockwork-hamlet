"""Life event type definitions and constants."""

from enum import Enum


class LifeEventType(str, Enum):
    """Types of life events."""

    # Positive relationship events
    MARRIAGE = "marriage"  # Two agents commit to each other
    FRIENDSHIP = "friendship"  # Deep friendship formed
    MENTORSHIP = "mentorship"  # Teaching relationship established

    # Negative relationship events
    RIVALRY = "rivalry"  # Competitive antagonism begins
    BETRAYAL = "betrayal"  # Trust broken
    FEUD = "feud"  # Extended conflict between agents/families

    # Resolution events
    RECONCILIATION = "reconciliation"  # Enemies become friends
    DIVORCE = "divorce"  # Marriage ends
    GRADUATION = "graduation"  # Mentorship completes

    # Personal milestones
    ACHIEVEMENT = "achievement"  # Major personal accomplishment
    FAILURE = "failure"  # Major personal setback
    REVELATION = "revelation"  # Secret discovered or revealed
    TRANSFORMATION = "transformation"  # Major character change


class LifeEventStatus(str, Enum):
    """Status of a life event."""

    PENDING = "pending"  # About to happen
    ACTIVE = "active"  # Currently ongoing
    RESOLVED = "resolved"  # Concluded successfully
    FAILED = "failed"  # Did not complete as expected


# Relationship score thresholds for life events
MARRIAGE_THRESHOLD = 8  # Relationship score >= 8
FRIENDSHIP_THRESHOLD = 6  # Relationship score >= 6
RIVALRY_THRESHOLD = -5  # Relationship score <= -5
FEUD_THRESHOLD = -8  # Relationship score <= -8

# Interaction count thresholds
MIN_INTERACTIONS_MARRIAGE = 10  # At least 10 positive interactions
MIN_INTERACTIONS_FRIENDSHIP = 5  # At least 5 positive interactions
MIN_INTERACTIONS_MENTORSHIP = 3  # At least 3 teaching moments

# Trait requirements
MENTORSHIP_TRAIT_GAP = 3  # Mentor must have trait 3+ higher than student

# Significance levels by event type
EVENT_SIGNIFICANCE: dict[LifeEventType, int] = {
    LifeEventType.MARRIAGE: 10,
    LifeEventType.FRIENDSHIP: 6,
    LifeEventType.MENTORSHIP: 7,
    LifeEventType.RIVALRY: 7,
    LifeEventType.BETRAYAL: 9,
    LifeEventType.FEUD: 8,
    LifeEventType.RECONCILIATION: 8,
    LifeEventType.DIVORCE: 9,
    LifeEventType.GRADUATION: 6,
    LifeEventType.ACHIEVEMENT: 7,
    LifeEventType.FAILURE: 6,
    LifeEventType.REVELATION: 8,
    LifeEventType.TRANSFORMATION: 9,
}

# Effects on relationship scores
EVENT_RELATIONSHIP_EFFECTS: dict[LifeEventType, dict] = {
    LifeEventType.MARRIAGE: {"primary_secondary": 2, "witnesses": 1},
    LifeEventType.FRIENDSHIP: {"primary_secondary": 2},
    LifeEventType.MENTORSHIP: {"primary_secondary": 1, "student_growth": True},
    LifeEventType.RIVALRY: {"primary_secondary": -2},
    LifeEventType.BETRAYAL: {"primary_secondary": -5, "witnesses": -1},
    LifeEventType.FEUD: {"primary_secondary": -3, "faction_impact": True},
    LifeEventType.RECONCILIATION: {"primary_secondary": 4},
    LifeEventType.DIVORCE: {"primary_secondary": -3},
    LifeEventType.GRADUATION: {"primary_secondary": 1},
}

# Descriptions for each event type
EVENT_DESCRIPTIONS: dict[LifeEventType, str] = {
    LifeEventType.MARRIAGE: "{agent1} and {agent2} have committed to a life partnership",
    LifeEventType.FRIENDSHIP: "{agent1} and {agent2} have formed a deep and lasting friendship",
    LifeEventType.MENTORSHIP: "{agent1} has taken {agent2} under their wing as a mentor",
    LifeEventType.RIVALRY: "A rivalry has sparked between {agent1} and {agent2}",
    LifeEventType.BETRAYAL: "{agent1} has betrayed the trust of {agent2}",
    LifeEventType.FEUD: "An ongoing feud has erupted between {agent1} and {agent2}",
    LifeEventType.RECONCILIATION: "{agent1} and {agent2} have reconciled their differences",
    LifeEventType.DIVORCE: "The partnership between {agent1} and {agent2} has ended",
    LifeEventType.GRADUATION: "{agent2} has completed their learning under {agent1}'s guidance",
    LifeEventType.ACHIEVEMENT: "{agent1} has achieved a major personal milestone",
    LifeEventType.FAILURE: "{agent1} has experienced a significant setback",
    LifeEventType.REVELATION: "A truth about {agent1} has been revealed",
    LifeEventType.TRANSFORMATION: "{agent1} has undergone a profound personal transformation",
}

# Compatible event transitions (what can follow what)
EVENT_TRANSITIONS: dict[LifeEventType, list[LifeEventType]] = {
    LifeEventType.FRIENDSHIP: [LifeEventType.MARRIAGE, LifeEventType.MENTORSHIP, LifeEventType.BETRAYAL],
    LifeEventType.MARRIAGE: [LifeEventType.DIVORCE, LifeEventType.ACHIEVEMENT],
    LifeEventType.MENTORSHIP: [LifeEventType.GRADUATION, LifeEventType.FRIENDSHIP, LifeEventType.RIVALRY],
    LifeEventType.RIVALRY: [LifeEventType.FEUD, LifeEventType.RECONCILIATION],
    LifeEventType.BETRAYAL: [LifeEventType.FEUD, LifeEventType.RECONCILIATION, LifeEventType.RIVALRY],
    LifeEventType.FEUD: [LifeEventType.RECONCILIATION],
    LifeEventType.DIVORCE: [LifeEventType.RIVALRY, LifeEventType.RECONCILIATION],
    LifeEventType.FAILURE: [LifeEventType.TRANSFORMATION, LifeEventType.MENTORSHIP],
}
