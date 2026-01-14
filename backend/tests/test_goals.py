"""Tests for the goal system."""

import pytest

from hamlet.db import Agent, Goal
from hamlet.goals import (
    DESIRES,
    NEEDS,
    REACTIVE,
    GoalCategory,
    GoalType,
    check_goal_completion,
    generate_goals,
    generate_reactive_goal,
    prioritize_goals,
)
from hamlet.goals.manager import resolve_conflicts
from hamlet.goals.types import get_category


# Note: The 'world' and 'agent' fixtures are provided by conftest.py


@pytest.mark.unit
class TestGoalTypes:
    """Test goal type definitions."""

    def test_needs_are_defined(self):
        """NEEDS list contains basic survival goals."""
        assert GoalType.EAT in NEEDS
        assert GoalType.SLEEP in NEEDS
        assert GoalType.SOCIALIZE in NEEDS
        assert len(NEEDS) == 3

    def test_desires_are_defined(self):
        """DESIRES list contains personality-driven goals."""
        assert GoalType.INVESTIGATE in DESIRES
        assert GoalType.MAKE_FRIEND in DESIRES
        assert GoalType.GAIN_WEALTH in DESIRES
        assert len(DESIRES) >= 5

    def test_reactive_are_defined(self):
        """REACTIVE list contains event-triggered goals."""
        assert GoalType.CONFRONT in REACTIVE
        assert GoalType.SHARE_GOSSIP in REACTIVE
        assert GoalType.HELP_FRIEND in REACTIVE
        assert len(REACTIVE) >= 5

    def test_get_category(self):
        """get_category returns correct category for each type."""
        assert get_category(GoalType.EAT) == GoalCategory.NEED
        assert get_category(GoalType.SLEEP) == GoalCategory.NEED
        assert get_category(GoalType.INVESTIGATE) == GoalCategory.DESIRE
        assert get_category(GoalType.CONFRONT) == GoalCategory.REACTIVE


@pytest.mark.integration
class TestGoalGeneration:
    """Test goal generation from agent state."""

    def test_hungry_agent_generates_eat_goal(self, agent, world):
        """Hungry agent should prioritize eating."""
        agent.hunger = 8  # Very hungry
        world.commit()

        goals = generate_goals(agent, include_desires=False)

        assert len(goals) >= 1
        assert goals[0].type == GoalType.EAT.value
        assert goals[0].priority >= 7  # High priority for urgent hunger

    def test_tired_agent_generates_sleep_goal(self, agent, world):
        """Tired agent should want to sleep."""
        agent.energy = 2  # Very tired
        world.commit()

        goals = generate_goals(agent, include_desires=False)

        assert len(goals) >= 1
        eat_goals = [g for g in goals if g.type == GoalType.SLEEP.value]
        assert len(eat_goals) >= 1
        assert eat_goals[0].priority >= 7

    def test_lonely_agent_generates_socialize_goal(self, agent, world):
        """Lonely agent should seek company."""
        agent.social = 1  # Very lonely
        world.commit()

        goals = generate_goals(agent, include_desires=False)

        social_goals = [g for g in goals if g.type == GoalType.SOCIALIZE.value]
        assert len(social_goals) >= 1
        assert social_goals[0].priority >= 5

    def test_satisfied_agent_has_no_urgent_needs(self, agent, world):
        """Agent with satisfied needs generates no need goals."""
        agent.hunger = 0
        agent.energy = 10
        agent.social = 10
        world.commit()

        goals = generate_goals(agent, include_desires=False)

        # Should have no goals when all needs are satisfied
        assert len(goals) == 0

    def test_hungry_takes_priority(self, agent, world):
        """When very hungry and tired, eating should be top priority."""
        agent.hunger = 9  # Starving
        agent.energy = 3  # Also tired
        world.commit()

        goals = generate_goals(agent, include_desires=False)

        # Eating should be first (hunger 9 = priority 9)
        assert goals[0].type == GoalType.EAT.value

    def test_desire_generation_based_on_traits(self, agent, world):
        """High trait values should generate related desire goals."""
        agent.hunger = 0
        agent.energy = 10
        agent.social = 10
        agent.traits = '{"curiosity": 10, "empathy": 3, "ambition": 3}'
        world.commit()

        # Generate multiple times to account for randomness
        all_goals = []
        for _ in range(10):
            goals = generate_goals(agent, include_desires=True)
            all_goals.extend(goals)

        # With high curiosity, should eventually see investigation goals
        goal_types = {g.type for g in all_goals}
        curiosity_goals = {
            GoalType.INVESTIGATE.value,
            GoalType.GAIN_KNOWLEDGE.value,
            GoalType.EXPLORE.value,
        }
        assert len(goal_types & curiosity_goals) > 0


@pytest.mark.integration
class TestReactiveGoals:
    """Test reactive goal generation."""

    def test_generate_reactive_goal(self, agent):
        """Can generate a reactive goal with target."""
        goal = generate_reactive_goal(
            agent,
            GoalType.CONFRONT,
            "Bob insulted me!",
            target_id="bob",
            priority=8,
        )

        assert goal.type == GoalType.CONFRONT.value
        assert goal.target_id == "bob"
        assert goal.priority == 8
        assert goal.status == "active"
        assert "insulted" in goal.description

    def test_reactive_goal_default_priority(self, agent):
        """Reactive goals have reasonable default priority."""
        goal = generate_reactive_goal(
            agent,
            GoalType.HELP_FRIEND,
            "Martha needs help",
        )

        # Should be higher than base desire priority (4)
        assert goal.priority >= 6


@pytest.mark.integration
class TestGoalPrioritization:
    """Test goal prioritization logic."""

    def test_higher_priority_first(self, agent):
        """Goals sorted by priority value within same category."""
        # Use all desire goals to test pure priority sorting without category bonus
        goals = [
            Goal(agent_id=agent.id, type=GoalType.INVESTIGATE.value, priority=5, created_at=1000),
            Goal(agent_id=agent.id, type=GoalType.MAKE_FRIEND.value, priority=8, created_at=1000),
            Goal(agent_id=agent.id, type=GoalType.EXPLORE.value, priority=3, created_at=1000),
        ]

        sorted_goals = prioritize_goals(goals)

        assert sorted_goals[0].priority == 8
        assert sorted_goals[1].priority == 5
        assert sorted_goals[2].priority == 3

    def test_needs_beat_desires_at_same_priority(self, agent):
        """Need goals beat desire goals at equal priority."""
        goals = [
            Goal(agent_id=agent.id, type=GoalType.INVESTIGATE.value, priority=7, created_at=1000),
            Goal(agent_id=agent.id, type=GoalType.EAT.value, priority=7, created_at=1000),
        ]

        sorted_goals = prioritize_goals(goals)

        # EAT (need) should come before INVESTIGATE (desire) at same priority
        assert sorted_goals[0].type == GoalType.EAT.value


@pytest.mark.integration
class TestGoalCompletion:
    """Test goal completion detection."""

    def test_eat_goal_completes_when_satiated(self, agent, world):
        """Eat goal completes when hunger is low."""
        goal = Goal(agent_id=agent.id, type=GoalType.EAT.value, priority=7, created_at=1000)
        agent.hunger = 1  # Well fed
        world.commit()

        status = check_goal_completion(goal, agent)

        assert status == "completed"

    def test_eat_goal_stays_active_when_hungry(self, agent, world):
        """Eat goal stays active when still hungry."""
        goal = Goal(agent_id=agent.id, type=GoalType.EAT.value, priority=7, created_at=1000)
        agent.hunger = 5  # Still hungry
        world.commit()

        status = check_goal_completion(goal, agent)

        assert status == "active"

    def test_sleep_goal_completes_when_rested(self, agent, world):
        """Sleep goal completes when energy is high."""
        goal = Goal(agent_id=agent.id, type=GoalType.SLEEP.value, priority=7, created_at=1000)
        agent.energy = 9  # Well rested
        world.commit()

        status = check_goal_completion(goal, agent)

        assert status == "completed"

    def test_socialize_goal_completes_when_social(self, agent, world):
        """Socialize goal completes when social need is met."""
        goal = Goal(agent_id=agent.id, type=GoalType.SOCIALIZE.value, priority=5, created_at=1000)
        agent.social = 8  # Socially satisfied
        world.commit()

        status = check_goal_completion(goal, agent)

        assert status == "completed"


@pytest.mark.integration
class TestConflictResolution:
    """Test goal conflict resolution."""

    def test_only_one_need_of_each_type(self, agent):
        """Can't have multiple EAT goals simultaneously."""
        goals = [
            Goal(agent_id=agent.id, type=GoalType.EAT.value, priority=9, created_at=1000),
            Goal(agent_id=agent.id, type=GoalType.EAT.value, priority=7, created_at=1100),
            Goal(agent_id=agent.id, type=GoalType.SLEEP.value, priority=5, created_at=1000),
        ]

        resolved = resolve_conflicts(goals)

        eat_goals = [g for g in resolved if g.type == GoalType.EAT.value]
        assert len(eat_goals) == 1
        assert eat_goals[0].priority == 9  # Kept the higher priority one

    def test_help_vs_confront_conflict(self, agent):
        """Can't help and confront same person."""
        goals = [
            Goal(
                agent_id=agent.id,
                type=GoalType.CONFRONT.value,
                priority=8,
                target_id="bob",
                created_at=1000,
            ),
            Goal(
                agent_id=agent.id,
                type=GoalType.HELP_FRIEND.value,
                priority=6,
                target_id="bob",
                created_at=1100,
            ),
        ]

        resolved = resolve_conflicts(goals)

        # Should only have CONFRONT (higher priority)
        bob_goals = [g for g in resolved if g.target_id == "bob"]
        assert len(bob_goals) == 1
        assert bob_goals[0].type == GoalType.CONFRONT.value

    def test_different_targets_no_conflict(self, agent):
        """Can confront one person and help another."""
        goals = [
            Goal(
                agent_id=agent.id,
                type=GoalType.CONFRONT.value,
                priority=8,
                target_id="bob",
                created_at=1000,
            ),
            Goal(
                agent_id=agent.id,
                type=GoalType.HELP_FRIEND.value,
                priority=6,
                target_id="martha",
                created_at=1100,
            ),
        ]

        resolved = resolve_conflicts(goals)

        # Both should remain
        assert len(resolved) == 2
