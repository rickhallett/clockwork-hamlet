"""Tests for the situational comedy detection module.

This module tests the comedy detection functions used to identify
absurd situations and generate humorous reactions for witty witnesses.

Tests cover:
- Absurd situation detection for various event types
- Witty reaction generation based on agent traits
- Edge cases and threshold behaviors
"""

import pytest

from hamlet.db import Agent, Relationship
from hamlet.simulation.comedy import (
    AbsurdSituation,
    detect_absurd_situation,
    generate_witty_reaction,
    is_witty_agent,
)


# Note: The 'agent' and 'db' fixtures are provided by conftest.py


@pytest.mark.unit
class TestDetectAbsurdSituation:
    """Test detect_absurd_situation() function.

    This function analyzes events and context to determine if
    a situation is absurd or comedic.
    """

    def test_rivals_helping_detected(self, agent, db):
        """Detects absurdity when rivals help each other."""
        # Create a rival relationship (very negative)
        rival = Agent(
            id="rival_agent",
            name="Rival Bob",
            traits='{"charm": 5, "curiosity": 5}',
        )
        db.add(rival)
        db.flush()

        relationship = Relationship(
            agent_id=agent.id,
            target_id=rival.id,
            score=-7,
            type="rival",
        )

        situation = detect_absurd_situation(
            event_type="help",
            actor=agent,
            target=rival,
            relationship=relationship,
        )

        assert situation is not None
        assert situation.situation_type == "rivals_helping"
        assert situation.comedy_level >= 7

    def test_rivals_giving_detected(self, agent, db):
        """Detects absurdity when rivals give gifts."""
        rival = Agent(
            id="rival_giver",
            name="Rival Carol",
            traits='{"charm": 5, "curiosity": 5}',
        )
        db.add(rival)
        db.flush()

        relationship = Relationship(
            agent_id=agent.id,
            target_id=rival.id,
            score=-6,
            type="enemy",
        )

        situation = detect_absurd_situation(
            event_type="give",
            actor=agent,
            target=rival,
            relationship=relationship,
        )

        assert situation is not None
        assert situation.situation_type == "rivals_generous"
        assert situation.comedy_level >= 6

    def test_friends_fighting_detected(self, agent, db):
        """Detects absurdity when close friends confront each other."""
        friend = Agent(
            id="friend_agent",
            name="Best Friend Dave",
            traits='{"charm": 5, "curiosity": 5}',
        )
        db.add(friend)
        db.flush()

        relationship = Relationship(
            agent_id=agent.id,
            target_id=friend.id,
            score=8,
            type="friend",
        )

        situation = detect_absurd_situation(
            event_type="confront",
            actor=agent,
            target=friend,
            relationship=relationship,
        )

        assert situation is not None
        assert situation.situation_type == "friends_fighting"
        assert situation.comedy_level >= 6

    def test_investigating_obvious_detected(self, agent, db):
        """Detects absurdity when investigating obvious things."""
        situation = detect_absurd_situation(
            event_type="investigate",
            actor=agent,
            target=None,
            relationship=None,
            context={"mystery": "the weather"},
        )

        assert situation is not None
        assert situation.situation_type == "investigating_obvious"
        assert "weather" in situation.description.lower()

    def test_talking_alone_detected(self, agent, db):
        """Detects absurdity when talking to no one."""
        situation = detect_absurd_situation(
            event_type="talk",
            actor=agent,
            target=None,
            relationship=None,
            context={"alone": True},
        )

        assert situation is not None
        assert situation.situation_type == "talking_alone"

    def test_day_sleeping_detected(self, agent, db):
        """Detects absurdity when sleeping during the day."""
        situation = detect_absurd_situation(
            event_type="sleep",
            actor=agent,
            target=None,
            relationship=None,
            context={"hour": 12},  # Noon
        )

        assert situation is not None
        assert situation.situation_type == "day_sleeper"

    def test_immediate_sleep_after_waking(self, agent, db):
        """Detects absurdity when going back to sleep immediately."""
        situation = detect_absurd_situation(
            event_type="sleep",
            actor=agent,
            target=None,
            relationship=None,
            context={"just_woke_up": True},
        )

        assert situation is not None
        assert situation.situation_type == "sleep_immediately"
        assert situation.comedy_level >= 7

    def test_normal_help_not_detected(self, agent, db):
        """Normal help between strangers is not absurd."""
        stranger = Agent(
            id="stranger_agent",
            name="Stranger Eve",
            traits='{"charm": 5, "curiosity": 5}',
        )
        db.add(stranger)
        db.flush()

        relationship = Relationship(
            agent_id=agent.id,
            target_id=stranger.id,
            score=0,
            type="acquaintance",
        )

        situation = detect_absurd_situation(
            event_type="help",
            actor=agent,
            target=stranger,
            relationship=relationship,
        )

        assert situation is None

    def test_night_sleeping_not_detected(self, agent, db):
        """Sleeping at night is not absurd."""
        situation = detect_absurd_situation(
            event_type="sleep",
            actor=agent,
            target=None,
            relationship=None,
            context={"hour": 22},  # 10 PM
        )

        assert situation is None

    def test_neutral_relationship_no_comedy(self, agent, db):
        """Neutral relationships don't trigger comedy for normal actions."""
        neutral = Agent(
            id="neutral_agent",
            name="Neutral Fran",
            traits='{"charm": 5, "curiosity": 5}',
        )
        db.add(neutral)
        db.flush()

        relationship = Relationship(
            agent_id=agent.id,
            target_id=neutral.id,
            score=3,
            type="acquaintance",
        )

        # Normal greet between acquaintances
        situation = detect_absurd_situation(
            event_type="greet",
            actor=agent,
            target=neutral,
            relationship=relationship,
        )

        assert situation is None


@pytest.mark.unit
class TestGenerateWittyReaction:
    """Test generate_witty_reaction() function.

    This function generates humorous reactions for witty witnesses
    (high charm or curiosity) when they observe absurd situations.
    """

    def test_high_charm_gets_reaction(self, agent, db):
        """High charm agents get witty reactions."""
        traits = agent.traits_dict
        traits["charm"] = 9
        traits["curiosity"] = 5
        agent.traits_dict = traits
        db.flush()

        situation = AbsurdSituation(
            situation_type="rivals_helping",
            description="Someone is helping their nemesis",
            comedy_level=8,
        )

        reaction = generate_witty_reaction(agent, situation, ["Bob", "Carol"])

        assert reaction is not None
        assert agent.name in reaction

    def test_high_curiosity_gets_reaction(self, agent, db):
        """High curiosity agents get witty reactions."""
        traits = agent.traits_dict
        traits["charm"] = 5
        traits["curiosity"] = 9
        agent.traits_dict = traits
        db.flush()

        situation = AbsurdSituation(
            situation_type="friends_fighting",
            description="Friends are having a confrontation",
            comedy_level=7,
        )

        reaction = generate_witty_reaction(agent, situation, ["Dave", "Eve"])

        assert reaction is not None
        assert agent.name in reaction

    def test_moderate_traits_no_reaction(self, agent, db):
        """Moderate trait agents don't get witty reactions."""
        traits = {
            "charm": 5,
            "curiosity": 5,
            "discretion": 5,
        }
        agent.traits_dict = traits
        db.flush()

        situation = AbsurdSituation(
            situation_type="rivals_helping",
            description="Someone is helping their nemesis",
            comedy_level=8,
        )

        reaction = generate_witty_reaction(agent, situation, ["Bob", "Carol"])

        assert reaction is None

    def test_low_comedy_needs_higher_wit(self, agent, db):
        """Low comedy situations need higher wit to notice."""
        traits = agent.traits_dict
        traits["charm"] = 7  # Just at threshold
        traits["curiosity"] = 5
        agent.traits_dict = traits
        db.flush()

        low_comedy = AbsurdSituation(
            situation_type="over_examining",
            description="Examining something again",
            comedy_level=4,  # Low comedy
        )

        reaction = generate_witty_reaction(agent, low_comedy, ["Bob"])

        # Charm 7 is not enough for comedy level 4
        assert reaction is None

        # But charm 8+ should catch it
        traits["charm"] = 8
        agent.traits_dict = traits
        db.flush()

        reaction = generate_witty_reaction(agent, low_comedy, ["Bob"])
        assert reaction is not None

    def test_combined_high_traits_better_reactions(self, agent, db):
        """Agents with both high charm and curiosity should get reactions."""
        traits = agent.traits_dict
        traits["charm"] = 9
        traits["curiosity"] = 9
        agent.traits_dict = traits
        db.flush()

        situation = AbsurdSituation(
            situation_type="investigating_obvious",
            description="Investigating the weather",
            comedy_level=7,
        )

        reaction = generate_witty_reaction(agent, situation, ["Bob"])

        assert reaction is not None
        assert agent.name in reaction


@pytest.mark.unit
class TestIsWittyAgent:
    """Test is_witty_agent() helper function."""

    def test_high_charm_is_witty(self, agent, db):
        """High charm agents are considered witty."""
        traits = agent.traits_dict
        traits["charm"] = 8
        traits["curiosity"] = 5
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is True

    def test_high_curiosity_is_witty(self, agent, db):
        """High curiosity agents are considered witty."""
        traits = agent.traits_dict
        traits["charm"] = 5
        traits["curiosity"] = 8
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is True

    def test_both_high_is_witty(self, agent, db):
        """Agents with both high traits are witty."""
        traits = agent.traits_dict
        traits["charm"] = 9
        traits["curiosity"] = 9
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is True

    def test_moderate_traits_not_witty(self, agent, db):
        """Moderate trait agents are not considered witty."""
        traits = {
            "charm": 5,
            "curiosity": 5,
        }
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is False

    def test_charm_at_threshold(self, agent, db):
        """Charm exactly at 7 is considered witty."""
        traits = agent.traits_dict
        traits["charm"] = 7
        traits["curiosity"] = 5
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is True

    def test_charm_below_threshold(self, agent, db):
        """Charm at 6 is not considered witty."""
        traits = agent.traits_dict
        traits["charm"] = 6
        traits["curiosity"] = 5
        agent.traits_dict = traits
        db.flush()

        assert is_witty_agent(agent) is False


@pytest.mark.unit
class TestAbsurdSituationDataclass:
    """Test the AbsurdSituation dataclass."""

    def test_create_absurd_situation(self):
        """Can create an AbsurdSituation with all fields."""
        situation = AbsurdSituation(
            situation_type="test_type",
            description="Test description",
            comedy_level=5,
        )

        assert situation.situation_type == "test_type"
        assert situation.description == "Test description"
        assert situation.comedy_level == 5
