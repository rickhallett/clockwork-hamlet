"""Goal type definitions and constants."""

from enum import Enum


class GoalCategory(str, Enum):
    """Categories of goals in the hierarchy."""

    NEED = "need"  # Basic survival needs - highest priority
    DESIRE = "desire"  # Personal wants driven by personality
    REACTIVE = "reactive"  # Goals created in response to events


class GoalType(str, Enum):
    """All possible goal types."""

    # NEEDS - Basic survival/comfort (always present)
    EAT = "eat"
    SLEEP = "sleep"
    SOCIALIZE = "socialize"

    # DESIRES - Personality-driven goals
    INVESTIGATE = "investigate"  # Curiosity-driven
    GAIN_WEALTH = "gain_wealth"  # Ambition-driven
    MAKE_FRIEND = "make_friend"  # Empathy/charm-driven
    FIND_ROMANCE = "find_romance"  # Social need + charm
    GAIN_KNOWLEDGE = "gain_knowledge"  # Curiosity-driven
    HELP_OTHERS = "help_others"  # Empathy-driven
    GAIN_POWER = "gain_power"  # Ambition-driven
    EXPLORE = "explore"  # Curiosity + courage-driven

    # REACTIVE - Event-triggered goals
    CONFRONT = "confront"  # Response to conflict/insult
    SHARE_GOSSIP = "share_gossip"  # Response to interesting info
    HELP_FRIEND = "help_friend"  # Response to friend in need
    AVOID_DANGER = "avoid_danger"  # Response to threat
    SEEK_REVENGE = "seek_revenge"  # Response to betrayal
    APOLOGIZE = "apologize"  # Response to hurting someone
    THANK = "thank"  # Response to receiving help
    INVESTIGATE_EVENT = "investigate_event"  # Response to mysterious event

    # POLL-RELATED REACTIVE - Response to poll results
    DISCUSS_POLL_RESULT = "discuss_poll_result"  # Discuss poll outcome with others
    CELEBRATE_POLL_WIN = "celebrate_poll_win"  # Celebrate when preferred option won
    ACCEPT_POLL_LOSS = "accept_poll_loss"  # Come to terms with losing vote
    IMPLEMENT_POLL_DECISION = "implement_poll_decision"  # Act on the poll's winning option


# Goal category mappings
NEEDS: list[GoalType] = [
    GoalType.EAT,
    GoalType.SLEEP,
    GoalType.SOCIALIZE,
]

DESIRES: list[GoalType] = [
    GoalType.INVESTIGATE,
    GoalType.GAIN_WEALTH,
    GoalType.MAKE_FRIEND,
    GoalType.FIND_ROMANCE,
    GoalType.GAIN_KNOWLEDGE,
    GoalType.HELP_OTHERS,
    GoalType.GAIN_POWER,
    GoalType.EXPLORE,
]

REACTIVE: list[GoalType] = [
    GoalType.CONFRONT,
    GoalType.SHARE_GOSSIP,
    GoalType.HELP_FRIEND,
    GoalType.AVOID_DANGER,
    GoalType.SEEK_REVENGE,
    GoalType.APOLOGIZE,
    GoalType.THANK,
    GoalType.INVESTIGATE_EVENT,
    # Poll-related reactive goals
    GoalType.DISCUSS_POLL_RESULT,
    GoalType.CELEBRATE_POLL_WIN,
    GoalType.ACCEPT_POLL_LOSS,
    GoalType.IMPLEMENT_POLL_DECISION,
]


def get_category(goal_type: GoalType) -> GoalCategory:
    """Get the category for a goal type."""
    if goal_type in NEEDS:
        return GoalCategory.NEED
    elif goal_type in DESIRES:
        return GoalCategory.DESIRE
    else:
        return GoalCategory.REACTIVE


# Base priority by category (can be modified by urgency)
CATEGORY_BASE_PRIORITY: dict[GoalCategory, int] = {
    GoalCategory.NEED: 7,  # High base priority
    GoalCategory.DESIRE: 4,  # Medium base priority
    GoalCategory.REACTIVE: 6,  # Higher than desires but context-dependent
}


# Trait to desire goal mappings
TRAIT_GOAL_MAPPINGS: dict[str, list[GoalType]] = {
    "curiosity": [GoalType.INVESTIGATE, GoalType.GAIN_KNOWLEDGE, GoalType.EXPLORE],
    "empathy": [GoalType.HELP_OTHERS, GoalType.MAKE_FRIEND],
    "ambition": [GoalType.GAIN_WEALTH, GoalType.GAIN_POWER],
    "charm": [GoalType.MAKE_FRIEND, GoalType.FIND_ROMANCE],
    "courage": [GoalType.EXPLORE, GoalType.CONFRONT],
    "perception": [GoalType.INVESTIGATE, GoalType.INVESTIGATE_EVENT],
}


# ============================================================================
# LONG-TERM GOAL PLANNING (LIFE-29)
# ============================================================================


class AmbitionType(str, Enum):
    """Types of long-term ambitions (multi-day goals)."""

    # Personal ambitions
    WEALTH = "wealth"  # Accumulate resources and prosperity
    POWER = "power"  # Gain influence and authority
    KNOWLEDGE = "knowledge"  # Master a skill or subject
    ROMANCE = "romance"  # Find and maintain love
    FAME = "fame"  # Become well-known and respected

    # Social ambitions
    LEADERSHIP = "leadership"  # Lead a faction or group
    COMMUNITY = "community"  # Improve village life
    MENTORSHIP = "mentorship"  # Guide others

    # Personal growth
    REDEMPTION = "redemption"  # Atone for past wrongs
    REVENGE = "revenge"  # Right a perceived wrong
    INDEPENDENCE = "independence"  # Break free from constraints


class PlanStatus(str, Enum):
    """Status of a long-term goal plan."""

    PLANNING = "planning"  # Still forming the plan
    ACTIVE = "active"  # Actively pursuing
    STALLED = "stalled"  # Blocked by something
    COMPLETED = "completed"  # Successfully achieved
    FAILED = "failed"  # Could not be achieved
    ABANDONED = "abandoned"  # Gave up


# Trait to ambition mappings
TRAIT_AMBITION_MAPPINGS: dict[str, list[AmbitionType]] = {
    "ambition": [AmbitionType.WEALTH, AmbitionType.POWER, AmbitionType.FAME],
    "curiosity": [AmbitionType.KNOWLEDGE],
    "charm": [AmbitionType.ROMANCE, AmbitionType.FAME, AmbitionType.LEADERSHIP],
    "empathy": [AmbitionType.COMMUNITY, AmbitionType.MENTORSHIP],
    "courage": [AmbitionType.LEADERSHIP, AmbitionType.INDEPENDENCE],
    "integrity": [AmbitionType.REDEMPTION, AmbitionType.COMMUNITY],
}

# Ambition priority (higher = more driving)
AMBITION_BASE_PRIORITY: dict[AmbitionType, int] = {
    AmbitionType.WEALTH: 6,
    AmbitionType.POWER: 7,
    AmbitionType.KNOWLEDGE: 5,
    AmbitionType.ROMANCE: 6,
    AmbitionType.FAME: 5,
    AmbitionType.LEADERSHIP: 7,
    AmbitionType.COMMUNITY: 5,
    AmbitionType.MENTORSHIP: 5,
    AmbitionType.REDEMPTION: 8,
    AmbitionType.REVENGE: 8,
    AmbitionType.INDEPENDENCE: 6,
}

# Milestone templates for each ambition type
AMBITION_MILESTONES: dict[AmbitionType, list[dict]] = {
    AmbitionType.WEALTH: [
        {"description": "Establish a reliable income source", "weight": 25},
        {"description": "Build savings and resources", "weight": 25},
        {"description": "Acquire valuable property or assets", "weight": 25},
        {"description": "Achieve financial security", "weight": 25},
    ],
    AmbitionType.POWER: [
        {"description": "Build a network of allies", "weight": 20},
        {"description": "Gain a position of responsibility", "weight": 30},
        {"description": "Expand influence over village decisions", "weight": 30},
        {"description": "Become a recognized authority", "weight": 20},
    ],
    AmbitionType.KNOWLEDGE: [
        {"description": "Find a mentor or learning source", "weight": 25},
        {"description": "Study and practice regularly", "weight": 25},
        {"description": "Apply knowledge in practical situations", "weight": 25},
        {"description": "Become an expert others consult", "weight": 25},
    ],
    AmbitionType.ROMANCE: [
        {"description": "Find someone compatible", "weight": 20},
        {"description": "Build a meaningful connection", "weight": 30},
        {"description": "Deepen the relationship", "weight": 30},
        {"description": "Commit to a lasting partnership", "weight": 20},
    ],
    AmbitionType.FAME: [
        {"description": "Perform noteworthy deeds", "weight": 25},
        {"description": "Gain recognition from villagers", "weight": 25},
        {"description": "Build a reputation across the village", "weight": 25},
        {"description": "Become a celebrated figure", "weight": 25},
    ],
    AmbitionType.LEADERSHIP: [
        {"description": "Gather like-minded individuals", "weight": 25},
        {"description": "Establish group purpose and goals", "weight": 25},
        {"description": "Prove leadership through action", "weight": 25},
        {"description": "Solidify position as leader", "weight": 25},
    ],
    AmbitionType.COMMUNITY: [
        {"description": "Identify village needs", "weight": 25},
        {"description": "Organize community efforts", "weight": 25},
        {"description": "Complete a project for the common good", "weight": 25},
        {"description": "Establish lasting improvements", "weight": 25},
    ],
    AmbitionType.MENTORSHIP: [
        {"description": "Find a worthy student", "weight": 25},
        {"description": "Share knowledge and experience", "weight": 25},
        {"description": "Guide them through challenges", "weight": 25},
        {"description": "See them succeed independently", "weight": 25},
    ],
    AmbitionType.REDEMPTION: [
        {"description": "Acknowledge past wrongs", "weight": 20},
        {"description": "Make amends to those harmed", "weight": 30},
        {"description": "Demonstrate genuine change", "weight": 30},
        {"description": "Earn forgiveness and trust", "weight": 20},
    ],
    AmbitionType.REVENGE: [
        {"description": "Gather information about the target", "weight": 20},
        {"description": "Build allies against the target", "weight": 25},
        {"description": "Undermine the target's reputation", "weight": 25},
        {"description": "Confront and defeat the target", "weight": 30},
    ],
    AmbitionType.INDEPENDENCE: [
        {"description": "Assess current constraints", "weight": 20},
        {"description": "Build self-sufficiency", "weight": 30},
        {"description": "Create distance from dependencies", "weight": 25},
        {"description": "Achieve true autonomy", "weight": 25},
    ],
}

# Sub-goals that support each ambition
AMBITION_SUBGOALS: dict[AmbitionType, list[GoalType]] = {
    AmbitionType.WEALTH: [GoalType.GAIN_WEALTH],
    AmbitionType.POWER: [GoalType.GAIN_POWER],
    AmbitionType.KNOWLEDGE: [GoalType.GAIN_KNOWLEDGE, GoalType.INVESTIGATE],
    AmbitionType.ROMANCE: [GoalType.FIND_ROMANCE, GoalType.MAKE_FRIEND],
    AmbitionType.FAME: [GoalType.GAIN_POWER, GoalType.HELP_OTHERS],
    AmbitionType.LEADERSHIP: [GoalType.GAIN_POWER, GoalType.MAKE_FRIEND],
    AmbitionType.COMMUNITY: [GoalType.HELP_OTHERS],
    AmbitionType.MENTORSHIP: [GoalType.HELP_OTHERS, GoalType.GAIN_KNOWLEDGE],
    AmbitionType.REDEMPTION: [GoalType.APOLOGIZE, GoalType.HELP_OTHERS],
    AmbitionType.REVENGE: [GoalType.SEEK_REVENGE, GoalType.CONFRONT],
    AmbitionType.INDEPENDENCE: [GoalType.EXPLORE, GoalType.GAIN_WEALTH],
}
