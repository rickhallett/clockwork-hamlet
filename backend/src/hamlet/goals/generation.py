"""Goal generation based on agent state and personality."""

import random
import time

from hamlet.db import Agent, Goal
from hamlet.goals.types import (
    CATEGORY_BASE_PRIORITY,
    TRAIT_GOAL_MAPPINGS,
    GoalCategory,
    GoalType,
)


def generate_need_goals(agent: Agent) -> list[Goal]:
    """Generate goals based on agent's basic needs.

    Needs are always checked and generate goals when thresholds are crossed.
    """
    goals = []
    now = int(time.time())

    # Hunger -> Eat goal
    if agent.hunger >= 6:
        # Urgent hunger
        priority = 9 if agent.hunger >= 8 else 7
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.EAT.value,
                description="Find something to eat"
                if agent.hunger < 8
                else "Desperately need food!",
                priority=priority,
                status="active",
                created_at=now,
            )
        )
    elif agent.hunger >= 4:
        # Moderate hunger
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.EAT.value,
                description="Getting hungry, should eat soon",
                priority=5,
                status="active",
                created_at=now,
            )
        )

    # Energy -> Sleep goal
    if agent.energy <= 3:
        # Urgent tiredness
        priority = 9 if agent.energy <= 1 else 7
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.SLEEP.value,
                description="Need to rest" if agent.energy > 1 else "Exhausted, must sleep!",
                priority=priority,
                status="active",
                created_at=now,
            )
        )
    elif agent.energy <= 5:
        # Moderate tiredness
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.SLEEP.value,
                description="Feeling tired",
                priority=4,
                status="active",
                created_at=now,
            )
        )

    # Social -> Socialize goal
    if agent.social <= 3:
        # Lonely
        priority = 7 if agent.social <= 1 else 5
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.SOCIALIZE.value,
                description="Need some company" if agent.social > 1 else "Feeling very lonely",
                priority=priority,
                status="active",
                created_at=now,
            )
        )
    elif agent.social <= 5:
        # Could use conversation
        goals.append(
            Goal(
                agent_id=agent.id,
                type=GoalType.SOCIALIZE.value,
                description="Would like to chat with someone",
                priority=3,
                status="active",
                created_at=now,
            )
        )

    return goals


def generate_desire_goals(agent: Agent, max_desires: int = 2) -> list[Goal]:
    """Generate desire goals based on agent's personality traits.

    Higher trait values increase likelihood and priority of related goals.
    """
    goals = []
    now = int(time.time())
    traits = agent.traits_dict

    # Collect potential desire goals weighted by traits
    weighted_goals: list[tuple[GoalType, float, str]] = []

    for trait_name, goal_types in TRAIT_GOAL_MAPPINGS.items():
        trait_value = traits.get(trait_name, 5)

        # Only consider if trait is above average (5)
        if trait_value >= 5:
            weight = (trait_value - 4) / 6  # 0.17 to 1.0 for values 5-10
            for goal_type in goal_types:
                if goal_type.value in [g.type for g in goals]:
                    continue  # Skip duplicates

                description = _get_desire_description(goal_type, trait_name)
                weighted_goals.append((goal_type, weight, description))

    # Select up to max_desires based on weights
    selected = []
    for goal_type, weight, description in weighted_goals:
        if len(selected) >= max_desires:
            break
        if random.random() < weight:
            # Priority based on trait strength
            priority = CATEGORY_BASE_PRIORITY[GoalCategory.DESIRE] + int(weight * 3)
            selected.append(
                Goal(
                    agent_id=agent.id,
                    type=goal_type.value,
                    description=description,
                    priority=min(priority, 8),  # Cap at 8 for desires
                    status="active",
                    created_at=now,
                )
            )

    return selected


def _get_desire_description(goal_type: GoalType, driving_trait: str) -> str:
    """Get a description for a desire goal."""
    descriptions = {
        GoalType.INVESTIGATE: "Look into something interesting",
        GoalType.GAIN_WEALTH: "Find a way to earn more coin",
        GoalType.MAKE_FRIEND: "Try to befriend someone new",
        GoalType.FIND_ROMANCE: "Perhaps find a romantic connection",
        GoalType.GAIN_KNOWLEDGE: "Learn something new",
        GoalType.HELP_OTHERS: "Help someone in need",
        GoalType.GAIN_POWER: "Increase influence in the village",
        GoalType.EXPLORE: "Explore new places",
    }
    return descriptions.get(goal_type, f"Pursue {goal_type.value}")


def generate_reactive_goal(
    agent: Agent,
    goal_type: GoalType,
    description: str,
    target_id: str | None = None,
    priority: int | None = None,
) -> Goal:
    """Generate a reactive goal in response to an event.

    Args:
        agent: The agent getting the goal
        goal_type: Type of reactive goal
        description: Description of what happened
        target_id: Optional target agent/object ID
        priority: Optional override priority (defaults to category base + 2)

    Returns:
        New Goal object
    """
    now = int(time.time())

    if priority is None:
        priority = CATEGORY_BASE_PRIORITY[GoalCategory.REACTIVE] + 2

    return Goal(
        agent_id=agent.id,
        type=goal_type.value,
        description=description,
        priority=min(priority, 10),
        target_id=target_id,
        status="active",
        created_at=now,
    )


def generate_goals(agent: Agent, include_desires: bool = True) -> list[Goal]:
    """Generate all appropriate goals for an agent.

    Returns goals sorted by priority (highest first).

    Args:
        agent: The agent to generate goals for
        include_desires: Whether to include personality-driven desires

    Returns:
        List of Goal objects sorted by priority
    """
    goals = []

    # Always generate need-based goals
    goals.extend(generate_need_goals(agent))

    # Optionally add desire goals
    if include_desires:
        goals.extend(generate_desire_goals(agent))

    # Sort by priority (highest first)
    goals.sort(key=lambda g: g.priority, reverse=True)

    return goals
