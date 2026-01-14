"""Tests for idle behaviors and spontaneous greetings.

This module tests the personality-driven idle behaviors and
relationship-aware greetings that agents exhibit during simulation.
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from hamlet.simulation.idle import IdleBehavior, get_idle_behavior
from hamlet.simulation.greetings import generate_arrival_comment
from hamlet.simulation.world import AgentPerception


def create_test_agent(traits: dict, **kwargs):
    """Create a mock agent with specific traits for testing.

    Args:
        traits: Dictionary of trait name to value (1-10)
        **kwargs: Additional agent attributes like name, mood, hunger, etc.

    Returns:
        A MagicMock agent configured with the specified attributes
    """
    agent = MagicMock()
    agent.name = kwargs.get("name", "Test Agent")
    agent.id = kwargs.get("id", "test_agent")
    agent.traits_dict = traits
    agent.mood_dict = kwargs.get("mood", {"happiness": 5, "energy": 5})
    agent.hunger = kwargs.get("hunger", 3)
    agent.energy = kwargs.get("energy", 7)
    agent.social = kwargs.get("social", 5)
    agent.relationships_as_source = kwargs.get("relationships", [])
    return agent


def create_test_perception(**kwargs):
    """Create an AgentPerception for testing.

    Args:
        **kwargs: Override default perception values

    Returns:
        An AgentPerception instance
    """
    return AgentPerception(
        location_name=kwargs.get("location_name", "Town Square"),
        nearby_agents=kwargs.get("nearby_agents", []),
        nearby_objects=kwargs.get("nearby_objects", []),
    )


def create_mock_relationship(target_id: str, rel_type: str, score: int):
    """Create a mock relationship object.

    Args:
        target_id: ID of the target agent
        rel_type: Type of relationship (friend, rival, acquaintance)
        score: Relationship score (-10 to 10)

    Returns:
        A MagicMock relationship
    """
    rel = MagicMock()
    rel.target_id = target_id
    rel.type = rel_type
    rel.score = score
    return rel


@pytest.mark.unit
class TestIdleBehaviors:
    """Tests for idle behavior generation based on agent state and traits."""

    def test_hungry_agent_thinks_about_food(self):
        """Hungry agents (hunger >= 6) should generate food-related thoughts."""
        agent = create_test_agent(traits={}, hunger=8)
        perception = create_test_perception()

        # Run multiple times to account for randomness
        food_thoughts_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "thought":
                    food_keywords = ["food", "stomach", "supper", "bread", "bakery"]
                    if any(kw in behavior.content.lower() for kw in food_keywords):
                        food_thoughts_found = True
                        break

        assert food_thoughts_found, "Hungry agent should think about food"

    def test_tired_agent_shows_tiredness(self):
        """Tired agents (energy <= 4) should generate tiredness-related behaviors."""
        agent = create_test_agent(traits={}, energy=2)
        perception = create_test_perception()

        tiredness_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "thought":
                    tiredness_keywords = ["yawn", "tired", "bed", "nap", "eyelids"]
                    if any(kw in behavior.content.lower() for kw in tiredness_keywords):
                        tiredness_found = True
                        break

        assert tiredness_found, "Tired agent should show signs of tiredness"

    def test_lonely_agent_wants_company(self):
        """Lonely agents (social <= 3) should generate loneliness-related thoughts."""
        agent = create_test_agent(traits={}, social=1)
        perception = create_test_perception()

        loneliness_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "thought":
                    loneliness_keywords = ["isolated", "company", "friends", "seeking", "sighs"]
                    if any(kw in behavior.content.lower() for kw in loneliness_keywords):
                        loneliness_found = True
                        break

        assert loneliness_found, "Lonely agent should want company"

    def test_high_curiosity_generates_observations(self):
        """High curiosity agents (curiosity >= 7) should generate curious observations."""
        agent = create_test_agent(traits={"curiosity": 9}, name="Curious Carl")
        perception = create_test_perception(nearby_objects=["old book", "strange stone"])

        curiosity_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior:
                    curiosity_keywords = ["wonders", "examining", "notices", "history", "secrets", "mysteries", "observations", "eyes", "interest"]
                    if any(kw in behavior.content.lower() for kw in curiosity_keywords):
                        curiosity_found = True
                        break

        assert curiosity_found, "High curiosity agent should make observations"

    def test_low_discretion_generates_mutters(self):
        """Low discretion agents (discretion <= 3) should mutter to themselves."""
        agent = create_test_agent(traits={"discretion": 2}, name="Blabby Bob")
        perception = create_test_perception()

        mutter_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "mutter":
                    mutter_found = True
                    break

        assert mutter_found, "Low discretion agent should mutter"

    def test_high_perception_notices_details(self):
        """High perception agents (perception >= 7) should notice environmental details."""
        agent = create_test_agent(traits={"perception": 9}, name="Perceptive Patty")
        perception = create_test_perception(nearby_agents=["Bob", "Martha"])

        observation_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "observation":
                    perception_keywords = ["notices", "observes", "catches", "shift", "spots", "note", "listens"]
                    if any(kw in behavior.content.lower() for kw in perception_keywords):
                        observation_found = True
                        break

        assert observation_found, "High perception agent should notice details"

    def test_location_specific_behaviors_bakery(self):
        """Agents at the bakery should have bakery-specific behaviors."""
        agent = create_test_agent(traits={})
        perception = create_test_perception(location_name="The Village Bakery")

        bakery_behavior_found = False
        for _ in range(100):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and "bread" in behavior.content.lower():
                    bakery_behavior_found = True
                    break

        assert bakery_behavior_found, "Bakery location should trigger bread-related behaviors"

    def test_location_specific_behaviors_tavern(self):
        """Agents at the tavern should have tavern-specific behaviors."""
        agent = create_test_agent(traits={})
        perception = create_test_perception(location_name="The Rusty Tavern")

        tavern_behavior_found = False
        for _ in range(100):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior:
                    tavern_keywords = ["bar", "fireplace"]
                    if any(kw in behavior.content.lower() for kw in tavern_keywords):
                        tavern_behavior_found = True
                        break

        assert tavern_behavior_found, "Tavern location should trigger tavern-related behaviors"

    def test_sometimes_returns_none(self):
        """The idle behavior system should sometimes return None (10% chance)."""
        agent = create_test_agent(traits={})
        perception = create_test_perception()

        none_count = 0
        iterations = 1000

        for _ in range(iterations):
            behavior = get_idle_behavior(agent, perception)
            if behavior is None:
                none_count += 1

        # With 10% chance, we expect roughly 100 None results
        # Allow for reasonable variance (5-20%)
        assert 30 < none_count < 200, f"Expected ~10% None results, got {none_count}/{iterations}"


@pytest.mark.unit
class TestSpontaneousGreetings:
    """Tests for relationship-aware greeting generation."""

    def test_greeting_friend_is_warm(self):
        """Greeting a friend should produce a warm greeting."""
        friend = create_test_agent(traits={}, name="Friend Bob", id="bob")
        relationship = create_mock_relationship("bob", "friend", 7)

        agent = create_test_agent(
            traits={"charm": 5},
            name="Test Agent",
            relationships=[relationship]
        )
        perception = create_test_perception()

        warm_greeting_found = False
        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [friend], perception)
                if greeting:
                    warm_keywords = ["friend", "good to see", "hello", "pleasure", "hoping", "pleasant", "warmly", "wave"]
                    if any(kw in greeting.lower() for kw in warm_keywords):
                        warm_greeting_found = True
                        break

        assert warm_greeting_found, "Greeting a friend should be warm"

    def test_greeting_rival_is_cold(self):
        """Greeting a rival should produce a cold acknowledgment."""
        rival = create_test_agent(traits={}, name="Rival Rick", id="rick")
        relationship = create_mock_relationship("rick", "rival", -7)

        agent = create_test_agent(
            traits={"charm": 5},
            name="Test Agent",
            relationships=[relationship]
        )
        perception = create_test_perception()

        cold_greeting_found = False
        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [rival], perception)
                if greeting:
                    cold_keywords = ["coolly", "thin", "curtly", "barely", "mutters", "pointed", "stiffens", "avoids", "grimaces", "it's you", "you're here"]
                    if any(kw in greeting.lower() for kw in cold_keywords):
                        cold_greeting_found = True
                        break

        assert cold_greeting_found, "Greeting a rival should be cold"

    def test_greeting_stranger_varies_by_charm(self):
        """Greeting strangers should vary based on charm level."""
        stranger = create_test_agent(traits={}, name="Stranger Sam", id="sam")

        # Test with high charm agent
        high_charm_agent = create_test_agent(
            traits={"charm": 9},
            name="Charming Charlie",
            relationships=[]
        )
        perception = create_test_perception()

        has_friendly_greeting = False
        for _ in range(30):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(high_charm_agent, [stranger], perception)
                if greeting:
                    friendly_keywords = ["hello", "good", "greets", "smile", "warm", "pleasant"]
                    if any(kw in greeting.lower() for kw in friendly_keywords):
                        has_friendly_greeting = True
                        break

        # Test with low charm agent
        low_charm_agent = create_test_agent(
            traits={"charm": 2},
            name="Awkward Andy",
            relationships=[]
        )

        has_awkward_greeting = False
        for _ in range(30):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(low_charm_agent, [stranger], perception)
                if greeting:
                    awkward_keywords = ["shuffles", "hesitant", "mumbles", "avoiding"]
                    if any(kw in greeting.lower() for kw in awkward_keywords):
                        has_awkward_greeting = True
                        break

        assert has_friendly_greeting, "High charm agent should give friendly greeting to stranger"
        assert has_awkward_greeting, "Low charm agent should give awkward greeting to stranger"

    def test_high_charm_warm_greeting(self):
        """High charm agents (charm >= 7) should give warm, effusive greetings."""
        friend = create_test_agent(traits={}, name="Friend Fiona", id="fiona")
        relationship = create_mock_relationship("fiona", "friend", 8)

        agent = create_test_agent(
            traits={"charm": 9},
            name="Charming Charlie",
            relationships=[relationship]
        )
        perception = create_test_perception()

        effusive_greeting_found = False
        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [friend], perception)
                if greeting:
                    effusive_keywords = ["beams", "enthusiastically", "warmly", "pleasant surprise", "hoping to see", "broadly", "always a pleasure"]
                    if any(kw in greeting.lower() for kw in effusive_keywords):
                        effusive_greeting_found = True
                        break

        assert effusive_greeting_found, "High charm agent should give effusive greeting"

    def test_low_charm_awkward_greeting(self):
        """Low charm agents (charm < 4) should give awkward greetings."""
        friend = create_test_agent(traits={}, name="Friend Fiona", id="fiona")
        relationship = create_mock_relationship("fiona", "friend", 8)

        agent = create_test_agent(
            traits={"charm": 2},
            name="Awkward Andy",
            relationships=[relationship]
        )
        perception = create_test_perception()

        awkward_greeting_found = False
        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [friend], perception)
                if greeting:
                    awkward_keywords = ["awkward", "mumbles", "stiffly", "um"]
                    if any(kw in greeting.lower() for kw in awkward_keywords):
                        awkward_greeting_found = True
                        break

        assert awkward_greeting_found, "Low charm agent should give awkward greeting"

    def test_sometimes_no_greeting(self):
        """The greeting system should sometimes return None (30% chance)."""
        other = create_test_agent(traits={}, name="Other Agent", id="other")
        agent = create_test_agent(traits={"charm": 5}, name="Test Agent", relationships=[])
        perception = create_test_perception()

        none_count = 0
        iterations = 1000

        for _ in range(iterations):
            greeting = generate_arrival_comment(agent, [other], perception)
            if greeting is None:
                none_count += 1

        # With 30% chance, we expect roughly 300 None results
        # Allow for reasonable variance (20-40%)
        assert 200 < none_count < 450, f"Expected ~30% None results, got {none_count}/{iterations}"

    def test_no_greeting_when_alone(self):
        """No greeting should be generated when there are no other agents."""
        agent = create_test_agent(traits={"charm": 5}, name="Lonely Larry", relationships=[])
        perception = create_test_perception()

        # When alone (no others), should always return None
        for _ in range(20):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [], perception)
                assert greeting is None, "No greeting when alone"


@pytest.mark.unit
class TestIdleBehaviorTypes:
    """Tests for the IdleBehavior dataclass and behavior types."""

    def test_idle_behavior_has_required_fields(self):
        """IdleBehavior should have type, content, and significance."""
        behavior = IdleBehavior(type="thought", content="Test thought", significance=2)

        assert behavior.type == "thought"
        assert behavior.content == "Test thought"
        assert behavior.significance == 2

    def test_idle_behavior_default_significance(self):
        """IdleBehavior should default to significance of 1."""
        behavior = IdleBehavior(type="action", content="Test action")

        assert behavior.significance == 1

    def test_valid_behavior_types(self):
        """Behaviors should be one of: thought, mutter, action, observation."""
        agent = create_test_agent(traits={"curiosity": 8, "discretion": 2, "perception": 8})
        perception = create_test_perception(
            nearby_agents=["Bob"],
            nearby_objects=["chair"]
        )

        valid_types = {"thought", "mutter", "action", "observation"}
        found_types = set()

        for _ in range(200):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior:
                    found_types.add(behavior.type)

        # Should find multiple valid types
        assert found_types.issubset(valid_types), f"Invalid behavior types found: {found_types - valid_types}"
        assert len(found_types) >= 2, f"Should find multiple behavior types, only found: {found_types}"


@pytest.mark.unit
class TestMoodBasedBehaviors:
    """Tests for mood-based idle behaviors."""

    def test_happy_agent_shows_happiness(self):
        """Happy agents (happiness >= 8) should show happy behaviors."""
        agent = create_test_agent(
            traits={},
            mood={"happiness": 9, "energy": 5}
        )
        perception = create_test_perception()

        happy_behavior_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "action":
                    happy_keywords = ["hums", "smiles", "spring", "whistles", "chuckles"]
                    if any(kw in behavior.content.lower() for kw in happy_keywords):
                        happy_behavior_found = True
                        break

        assert happy_behavior_found, "Happy agent should show happiness"

    def test_unhappy_agent_shows_unhappiness(self):
        """Unhappy agents (happiness <= 3) should show unhappy behaviors."""
        agent = create_test_agent(
            traits={},
            mood={"happiness": 2, "energy": 5}
        )
        perception = create_test_perception()

        unhappy_behavior_found = False
        for _ in range(50):
            with patch("hamlet.simulation.idle.random.random", return_value=0.5):
                behavior = get_idle_behavior(agent, perception)
                if behavior and behavior.type == "action":
                    unhappy_keywords = ["sighs", "frowns", "stares", "fidgets", "mutters"]
                    if any(kw in behavior.content.lower() for kw in unhappy_keywords):
                        unhappy_behavior_found = True
                        break

        assert unhappy_behavior_found, "Unhappy agent should show unhappiness"


@pytest.mark.unit
class TestRelationshipPriority:
    """Tests for greeting relationship priority."""

    def test_friend_priority_over_stranger(self):
        """Friends should be greeted over strangers."""
        friend = create_test_agent(traits={}, name="Friend Fiona", id="fiona")
        stranger = create_test_agent(traits={}, name="Stranger Sam", id="sam")
        relationship = create_mock_relationship("fiona", "friend", 8)

        agent = create_test_agent(
            traits={"charm": 5},
            name="Test Agent",
            relationships=[relationship]
        )
        perception = create_test_perception()

        # When both friend and stranger are present, friend should be greeted
        friend_greeted = 0
        stranger_greeted = 0

        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [friend, stranger], perception)
                if greeting and "Fiona" in greeting:
                    friend_greeted += 1
                elif greeting and "Sam" in greeting:
                    stranger_greeted += 1

        assert friend_greeted > stranger_greeted, "Friends should be greeted over strangers"

    def test_acquaintance_priority_over_stranger(self):
        """Acquaintances should be greeted over strangers when no friends present."""
        acquaintance = create_test_agent(traits={}, name="Acquaintance Alex", id="alex")
        stranger = create_test_agent(traits={}, name="Stranger Sam", id="sam")
        relationship = create_mock_relationship("alex", "acquaintance", 2)

        agent = create_test_agent(
            traits={"charm": 5},
            name="Test Agent",
            relationships=[relationship]
        )
        perception = create_test_perception()

        acquaintance_greeted = 0
        stranger_greeted = 0

        for _ in range(50):
            with patch("hamlet.simulation.greetings.random.random", return_value=0.5):
                greeting = generate_arrival_comment(agent, [acquaintance, stranger], perception)
                if greeting and "Alex" in greeting:
                    acquaintance_greeted += 1
                elif greeting and "Sam" in greeting:
                    stranger_greeted += 1

        assert acquaintance_greeted > stranger_greeted, "Acquaintances should be greeted over strangers"
