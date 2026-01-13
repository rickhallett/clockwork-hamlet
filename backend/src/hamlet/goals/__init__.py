"""Goal system for agent motivation and behavior."""

from hamlet.goals.generation import generate_goals, generate_reactive_goal
from hamlet.goals.manager import (
    GoalManager,
    check_goal_completion,
    get_active_goals,
    prioritize_goals,
)
from hamlet.goals.types import (
    DESIRES,
    NEEDS,
    REACTIVE,
    GoalCategory,
    GoalType,
)

__all__ = [
    # Types
    "GoalType",
    "GoalCategory",
    "NEEDS",
    "DESIRES",
    "REACTIVE",
    # Generation
    "generate_goals",
    "generate_reactive_goal",
    # Management
    "GoalManager",
    "get_active_goals",
    "prioritize_goals",
    "check_goal_completion",
]
