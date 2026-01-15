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
