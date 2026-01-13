"""Goal management: prioritization, completion, and conflict handling."""

import time

from sqlalchemy.orm import Session

from hamlet.db import Agent, Goal
from hamlet.goals.generation import generate_goals, generate_reactive_goal
from hamlet.goals.types import GoalCategory, GoalType, get_category


def get_active_goals(agent_id: str, db: Session, limit: int = 10) -> list[Goal]:
    """Get active goals for an agent, sorted by priority."""
    return (
        db.query(Goal)
        .filter(Goal.agent_id == agent_id, Goal.status == "active")
        .order_by(Goal.priority.desc())
        .limit(limit)
        .all()
    )


def prioritize_goals(goals: list[Goal]) -> list[Goal]:
    """Sort and prioritize a list of goals.

    Considers:
    - Base priority value
    - Goal category (needs > reactive > desires)
    - Age of goal (older goals get slight boost)

    Returns:
        Sorted list with highest priority first
    """
    now = int(time.time())

    def score(goal: Goal) -> float:
        base = goal.priority * 10  # Base priority weighted heavily

        # Category bonus
        category = get_category(GoalType(goal.type))
        category_bonus = {
            GoalCategory.NEED: 30,
            GoalCategory.REACTIVE: 15,
            GoalCategory.DESIRE: 0,
        }.get(category, 0)

        # Age bonus (up to +5 for goals older than 1 hour)
        age_seconds = now - (goal.created_at or now)
        age_bonus = min(age_seconds / 720, 5)  # +1 per 12 minutes, max +5

        return base + category_bonus + age_bonus

    return sorted(goals, key=score, reverse=True)


def check_goal_completion(goal: Goal, agent: Agent) -> str:
    """Check if a goal should be marked complete or failed.

    Args:
        goal: The goal to check
        agent: The agent with the goal

    Returns:
        New status: "active", "completed", or "failed"
    """
    goal_type = GoalType(goal.type)

    # Check NEED goal completion
    if goal_type == GoalType.EAT:
        if agent.hunger <= 2:
            return "completed"
        # Fail if hunger is maxed out (10) - agent can't eat anymore
        if agent.hunger >= 10:
            return "failed"

    elif goal_type == GoalType.SLEEP:
        if agent.energy >= 8:
            return "completed"
        # Fail if agent has been unable to sleep for too long

    elif goal_type == GoalType.SOCIALIZE:
        if agent.social >= 7:
            return "completed"

    # Check goal age - abandon very old goals
    now = int(time.time())
    age_hours = (now - (goal.created_at or now)) / 3600

    # Reactive goals expire faster
    if get_category(goal_type) == GoalCategory.REACTIVE and age_hours > 2:
        return "failed"

    # Desire goals can persist longer but eventually expire
    if get_category(goal_type) == GoalCategory.DESIRE and age_hours > 24:
        return "failed"

    return "active"


def resolve_conflicts(goals: list[Goal]) -> list[Goal]:
    """Remove conflicting goals, keeping higher priority ones.

    Conflict rules:
    - Can't have both HELP_FRIEND and CONFRONT same target
    - Can't have both SEEK_REVENGE and APOLOGIZE same target
    - Only one of each NEED type at a time

    Returns:
        Filtered list with conflicts resolved
    """
    resolved = []
    seen_types: set[str] = set()
    seen_targets: dict[str, set[str]] = {}  # target_id -> set of goal types

    # Goals should already be sorted by priority
    for goal in goals:
        # Only one of each need type
        if goal.type in [GoalType.EAT.value, GoalType.SLEEP.value, GoalType.SOCIALIZE.value]:
            if goal.type in seen_types:
                continue
            seen_types.add(goal.type)

        # Check target-based conflicts
        if goal.target_id:
            target_goals = seen_targets.get(goal.target_id, set())

            # HELP_FRIEND vs CONFRONT conflict
            if goal.type == GoalType.HELP_FRIEND.value and GoalType.CONFRONT.value in target_goals:
                continue
            if goal.type == GoalType.CONFRONT.value and GoalType.HELP_FRIEND.value in target_goals:
                continue

            # SEEK_REVENGE vs APOLOGIZE conflict
            if (
                goal.type == GoalType.SEEK_REVENGE.value
                and GoalType.APOLOGIZE.value in target_goals
            ):
                continue
            if (
                goal.type == GoalType.APOLOGIZE.value
                and GoalType.SEEK_REVENGE.value in target_goals
            ):
                continue

            # Track this target's goals
            if goal.target_id not in seen_targets:
                seen_targets[goal.target_id] = set()
            seen_targets[goal.target_id].add(goal.type)

        resolved.append(goal)

    return resolved


class GoalManager:
    """Manages goals for an agent throughout simulation."""

    def __init__(self, db: Session):
        self.db = db

    def refresh_goals(self, agent: Agent) -> list[Goal]:
        """Refresh an agent's goals based on current state.

        1. Check existing goals for completion/failure
        2. Generate new need-based goals
        3. Optionally generate desire goals if few active
        4. Resolve conflicts
        5. Persist changes

        Returns:
            List of active goals after refresh
        """
        # Get existing active goals
        existing = get_active_goals(agent.id, self.db)

        # Check completion status of existing goals
        for goal in existing:
            new_status = check_goal_completion(goal, agent)
            if new_status != "active":
                goal.status = new_status

        # Filter to still-active goals
        active = [g for g in existing if g.status == "active"]

        # Generate new goals based on current state
        # Only include desires if we have few active desire goals
        active_desires = [
            g for g in active if get_category(GoalType(g.type)) == GoalCategory.DESIRE
        ]
        include_desires = len(active_desires) < 2

        new_goals = generate_goals(agent, include_desires=include_desires)

        # Merge: keep existing, add new ones that don't duplicate
        existing_types = {(g.type, g.target_id) for g in active}
        for new_goal in new_goals:
            key = (new_goal.type, new_goal.target_id)
            if key not in existing_types:
                active.append(new_goal)
                self.db.add(new_goal)

        # Prioritize and resolve conflicts
        active = prioritize_goals(active)
        active = resolve_conflicts(active)

        # Commit changes
        self.db.commit()

        return active

    def add_reactive_goal(
        self,
        agent: Agent,
        goal_type: GoalType,
        description: str,
        target_id: str | None = None,
        priority: int | None = None,
    ) -> Goal:
        """Add a reactive goal in response to an event.

        Returns:
            The created Goal
        """
        goal = generate_reactive_goal(agent, goal_type, description, target_id, priority)
        self.db.add(goal)
        self.db.commit()
        return goal

    def complete_goal(self, goal: Goal) -> None:
        """Mark a goal as completed."""
        goal.status = "completed"
        self.db.commit()

    def fail_goal(self, goal: Goal, reason: str | None = None) -> None:
        """Mark a goal as failed."""
        goal.status = "failed"
        if reason:
            goal.description = f"{goal.description} (Failed: {reason})"
        self.db.commit()

    def abandon_goal(self, goal: Goal) -> None:
        """Mark a goal as abandoned (gave up)."""
        goal.status = "abandoned"
        self.db.commit()

    def get_top_goal(self, agent: Agent) -> Goal | None:
        """Get the highest priority active goal for an agent."""
        goals = get_active_goals(agent.id, self.db, limit=1)
        return goals[0] if goals else None
