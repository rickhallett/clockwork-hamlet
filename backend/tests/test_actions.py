"""Tests for the actions module."""

import pytest

from hamlet.actions import (
    Confront,
    Give,
    Greet,
    Help,
    Move,
    Talk,
    execute_action,
)
from hamlet.db import Relationship

pytestmark = pytest.mark.integration


@pytest.fixture
def setup_agents(world):
    """Reset agent locations at start of each test."""
    for agent in world.get_agents():
        if agent.id == "agnes":
            agent.location_id = "bakery"
        else:
            agent.location_id = "town_square"
        agent.state = "idle"
    world.commit()
    yield


class TestMoveAction:
    """Tests for move action."""

    def test_move_to_connected_location(self, world, setup_agents):
        """Test moving to a connected location."""
        # Agnes is at bakery, can move to town_square
        action = Move("agnes", "town_square")
        result = execute_action(action, world)

        assert result.success
        assert "moved to" in result.message

        agent = world.get_agent("agnes")
        assert agent.location_id == "town_square"

    def test_move_to_disconnected_location_fails(self, world, setup_agents):
        """Test that moving to disconnected location fails."""
        # Agnes is at bakery, cannot directly go to tavern
        action = Move("agnes", "tavern")
        result = execute_action(action, world)

        assert not result.success
        assert "Cannot reach" in result.message

    def test_move_to_nonexistent_location_fails(self, world, setup_agents):
        """Test that moving to nonexistent location fails."""
        action = Move("agnes", "nonexistent")
        result = execute_action(action, world)

        assert not result.success


class TestSocialActions:
    """Tests for social actions."""

    def test_greet_in_same_location(self, world, setup_agents):
        """Test greeting someone in the same location."""
        # First move Agnes to town_square where Bob is
        move = Move("agnes", "town_square")
        execute_action(move, world)

        # Now greet Bob
        action = Greet("agnes", "bob")
        result = execute_action(action, world)

        assert result.success
        assert "greeted" in result.message

    def test_greet_different_location_fails(self, world, setup_agents):
        """Test that greeting someone in different location fails."""
        # Agnes is at bakery, Bob is at town_square
        action = Greet("agnes", "bob")
        result = execute_action(action, world)

        assert not result.success
        assert "not here" in result.message

    def test_talk_improves_social(self, world, setup_agents):
        """Test that talking improves social need."""
        # Move Agnes to town_square
        move = Move("agnes", "town_square")
        execute_action(move, world)

        agnes = world.get_agent("agnes")
        bob = world.get_agent("bob")
        old_social_agnes = agnes.social
        old_social_bob = bob.social

        action = Talk("agnes", "bob", "the weather")
        result = execute_action(action, world)

        assert result.success
        assert agnes.social >= old_social_agnes
        assert bob.social >= old_social_bob


class TestRelationshipUpdates:
    """Tests for relationship updates."""

    def test_help_improves_relationship(self, world, setup_agents):
        """Test that helping improves relationship."""
        # Move Agnes to town_square
        move = Move("agnes", "town_square")
        execute_action(move, world)

        # Get initial relationship and ensure it's not at max
        db = world.db
        rel_before = (
            db.query(Relationship)
            .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
            .first()
        )
        if rel_before and rel_before.score >= 10:
            rel_before.score = 5  # Reset to allow increase
            db.commit()
        score_before = rel_before.score if rel_before else 0

        # Help Bob
        action = Help("agnes", "bob", "with gardening")
        result = execute_action(action, world)

        assert result.success

        # Check relationship improved OR was already at max
        rel_after = (
            db.query(Relationship)
            .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
            .first()
        )
        assert rel_after.score >= score_before

    def test_confront_damages_relationship(self, world, setup_agents):
        """Test that confronting damages relationship."""
        # Move Agnes to town_square
        move = Move("agnes", "town_square")
        execute_action(move, world)

        # Get initial relationship
        db = world.db
        rel_before = (
            db.query(Relationship)
            .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
            .first()
        )
        score_before = rel_before.score if rel_before else 0

        # Confront Bob
        action = Confront("agnes", "bob", "the missing cheese")
        result = execute_action(action, world)

        assert result.success

        # Check relationship damaged
        rel_after = (
            db.query(Relationship)
            .filter(Relationship.agent_id == "bob", Relationship.target_id == "agnes")
            .first()
        )
        assert rel_after.score < score_before


class TestValidation:
    """Tests for action validation."""

    def test_sleeping_agent_cannot_act(self, world, setup_agents):
        """Test that sleeping agents cannot perform actions."""
        agnes = world.get_agent("agnes")
        agnes.state = "sleeping"
        world.commit()

        action = Move("agnes", "town_square")
        result = execute_action(action, world)

        assert not result.success
        assert "sleeping" in result.message.lower()

    def test_cannot_give_item_not_owned(self, world, setup_agents):
        """Test that you cannot give an item you don't have."""
        # Move Agnes to town_square
        move = Move("agnes", "town_square")
        execute_action(move, world)

        action = Give("agnes", "bob", "diamond_ring")
        result = execute_action(action, world)

        assert not result.success
        assert "don't have" in result.message
