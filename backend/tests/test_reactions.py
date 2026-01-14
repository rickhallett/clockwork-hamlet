"""Tests for witness reaction generation.

Tests the witness reaction system that generates personality-driven
visible reactions when agents witness significant events.
"""

import random
from unittest.mock import MagicMock

import pytest

from hamlet.simulation.reactions import generate_witness_reaction


def create_witness(empathy=5, curiosity=5, discretion=5, name="Witness"):
    """Create a mock witness agent with specified traits.

    Args:
        empathy: Empathy trait value (1-10)
        curiosity: Curiosity trait value (1-10)
        discretion: Discretion trait value (1-10)
        name: Name of the witness

    Returns:
        MagicMock agent with traits_dict and name attributes
    """
    agent = MagicMock()
    agent.name = name
    agent.traits_dict = {
        "empathy": empathy,
        "curiosity": curiosity,
        "discretion": discretion,
    }
    return agent


class TestWitnessReactions:
    """Tests for witness reaction generation based on personality traits."""

    def test_high_empathy_concerned_at_conflict(self):
        """High empathy witnesses show concern at conflict events."""
        witness = create_witness(empathy=8, name="Emma")

        # Run multiple times to account for weighted randomness
        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["Alice", "Bob"],
                significance=7,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # High empathy reactions to conflict include concern-related words
        concern_keywords = ["concerned", "winces", "uncomfortably", "worry", "frowns"]
        has_concern_reaction = any(
            any(keyword in r.lower() for keyword in concern_keywords)
            for r in reactions
        )
        assert has_concern_reaction, f"Expected concern reactions, got: {reactions}"

    def test_high_empathy_smiles_at_kindness(self):
        """High empathy witnesses smile warmly at help/kindness events."""
        witness = create_witness(empathy=8, name="Emma")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="help",
                actors=["Alice", "Bob"],
                significance=6,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # High empathy reactions to help include positive responses
        positive_keywords = ["smiles", "warmly", "nods", "approvingly"]
        has_positive_reaction = any(
            any(keyword in r.lower() for keyword in positive_keywords)
            for r in reactions
        )
        assert has_positive_reaction, f"Expected positive reactions, got: {reactions}"

    def test_high_curiosity_interested_in_gossip(self):
        """High curiosity witnesses show interest in gossip events."""
        witness = create_witness(curiosity=8, name="Cora")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["Alice", "Bob"],
                significance=5,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # High curiosity reactions to gossip include interest-related words
        interest_keywords = ["leans", "interest", "perks", "closer", "hear"]
        has_interest_reaction = any(
            any(keyword in r.lower() for keyword in interest_keywords)
            for r in reactions
        )
        assert has_interest_reaction, f"Expected interest reactions, got: {reactions}"

    def test_low_discretion_gasps_audibly(self):
        """Low discretion witnesses gasp audibly at dramatic events."""
        witness = create_witness(discretion=2, name="Diana")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["Alice", "Bob"],
                significance=8,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Low discretion reactions include audible/visible responses
        audible_keywords = ["gasps", "audibly", "mutters", "whispers", "exclaims"]
        has_audible_reaction = any(
            any(keyword in r.lower() for keyword in audible_keywords)
            for r in reactions
        )
        assert has_audible_reaction, f"Expected audible reactions, got: {reactions}"

    def test_high_discretion_subtle_glance(self):
        """High discretion witnesses react subtly with glances."""
        witness = create_witness(discretion=8, name="Stanley")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["Alice", "Bob"],
                significance=7,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # High discretion reactions are subtle
        subtle_keywords = ["glances", "briefly", "eyebrow", "imperceptibly", "noticed"]
        has_subtle_reaction = any(
            any(keyword in r.lower() for keyword in subtle_keywords)
            for r in reactions
        )
        assert has_subtle_reaction, f"Expected subtle reactions, got: {reactions}"

    def test_low_significance_sometimes_no_reaction(self):
        """Low significance events (<=3) only get reactions 50% of the time."""
        witness = create_witness(empathy=7, curiosity=7, name="Tester")

        # Run many iterations to verify probabilistic behavior
        no_reaction_count = 0
        reaction_count = 0
        iterations = 200

        for _ in range(iterations):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="talk",
                actors=["Alice", "Bob"],
                significance=2,  # Low significance
            )
            if reaction is None:
                no_reaction_count += 1
            else:
                reaction_count += 1

        # With 50% probability over 200 iterations, we expect roughly 100 each
        # Allow for statistical variance (between 30% and 70%)
        no_reaction_ratio = no_reaction_count / iterations
        assert 0.3 <= no_reaction_ratio <= 0.7, (
            f"Expected ~50% no reactions for low significance, "
            f"got {no_reaction_ratio:.1%} ({no_reaction_count}/{iterations})"
        )

    def test_confront_generates_strong_reaction(self):
        """Confrontation events generate strong reactions."""
        witness = create_witness(empathy=5, curiosity=5, discretion=5, name="Observer")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["Alice", "Bob"],
                significance=8,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Neutral witnesses still react to confrontation
        assert all("Observer" in r for r in reactions)

    def test_gossip_generates_curiosity_reaction(self):
        """Gossip events generate curiosity-related reactions."""
        witness = create_witness(empathy=5, curiosity=5, discretion=5, name="Observer")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["Alice", "Bob"],
                significance=5,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Check for gossip-related neutral reactions
        gossip_keywords = ["pretends", "listen", "curiously", "glances"]
        has_gossip_reaction = any(
            any(keyword in r.lower() for keyword in gossip_keywords)
            for r in reactions
        )
        assert has_gossip_reaction, f"Expected gossip reactions, got: {reactions}"

    def test_help_generates_positive_reaction(self):
        """Help events generate positive reactions."""
        witness = create_witness(empathy=5, curiosity=5, discretion=5, name="Observer")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="help",
                actors=["Alice", "Bob"],
                significance=5,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Neutral witnesses notice help gestures
        notice_keywords = ["notices", "helpful", "gesture"]
        has_notice_reaction = any(
            any(keyword in r.lower() for keyword in notice_keywords)
            for r in reactions
        )
        assert has_notice_reaction, f"Expected notice reactions, got: {reactions}"


class TestReactionsByPersonality:
    """Tests for reactions based on specific personality trait combinations."""

    def test_empathetic_witness(self):
        """Empathetic witnesses (empathy >= 7) show emotional responses."""
        witness = create_witness(empathy=9, curiosity=3, discretion=5, name="Empath")

        reactions = []
        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["Alice", "Bob"],
                significance=7,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Empathetic reactions include emotional words
        emotional_keywords = [
            "concerned",
            "winces",
            "sympathetically",
            "uncomfortably",
            "worry",
            "frowns",
            "thoughtful",
        ]
        has_emotional = any(
            any(keyword in r.lower() for keyword in emotional_keywords)
            for r in reactions
        )
        assert has_emotional, f"Expected emotional reactions, got: {reactions}"

    def test_curious_witness(self):
        """Curious witnesses (curiosity >= 7) show interest-based responses."""
        witness = create_witness(empathy=3, curiosity=9, discretion=5, name="Curious")

        reactions = []
        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="tell",
                actors=["Alice", "Bob"],
                significance=6,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Curious reactions include interest-related words
        curious_keywords = [
            "curiosity",
            "interest",
            "intently",
            "tilts",
            "head",
            "keen",
        ]
        has_curious = any(
            any(keyword in r.lower() for keyword in curious_keywords)
            for r in reactions
        )
        assert has_curious, f"Expected curious reactions, got: {reactions}"

    def test_indiscreet_witness(self):
        """Indiscreet witnesses (discretion <= 3) react audibly."""
        witness = create_witness(empathy=5, curiosity=5, discretion=2, name="Loud")

        reactions = []
        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["Alice", "Bob"],
                significance=6,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Indiscreet reactions are audible
        audible_keywords = ["giggle", "audible", "ooh", "suppresses"]
        has_audible = any(
            any(keyword in r.lower() for keyword in audible_keywords)
            for r in reactions
        )
        assert has_audible, f"Expected audible reactions, got: {reactions}"

    def test_discreet_witness(self):
        """Discreet witnesses (discretion >= 7) react subtly."""
        witness = create_witness(empathy=5, curiosity=5, discretion=9, name="Subtle")

        reactions = []
        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["Alice", "Bob"],
                significance=6,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Discreet reactions are subtle
        subtle_keywords = [
            "glances",
            "briefly",
            "eyebrow",
            "imperceptibly",
            "noticed",
            "continues",
        ]
        has_subtle = any(
            any(keyword in r.lower() for keyword in subtle_keywords)
            for r in reactions
        )
        assert has_subtle, f"Expected subtle reactions, got: {reactions}"

    def test_neutral_witness(self):
        """Neutral witnesses (moderate traits) use default reactions."""
        witness = create_witness(empathy=5, curiosity=5, discretion=5, name="Neutral")

        reactions = []
        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="give",
                actors=["Alice", "Bob"],
                significance=5,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Neutral reactions are observational
        neutral_keywords = ["observes", "exchange", "glances", "eyebrow"]
        has_neutral = any(
            any(keyword in r.lower() for keyword in neutral_keywords)
            for r in reactions
        )
        assert has_neutral, f"Expected neutral reactions, got: {reactions}"


class TestReactionTraitThresholds:
    """Parameterized tests for trait threshold behavior."""

    @pytest.mark.parametrize(
        "empathy,expected_concern",
        [
            (7, True),  # Threshold - should have concern reactions
            (8, True),  # Above threshold
            (10, True),  # Max empathy
            (6, False),  # Below threshold
            (5, False),  # Default/neutral
        ],
    )
    def test_empathy_threshold_for_concern(self, empathy, expected_concern):
        """Test that empathy threshold (>=7) triggers concerned reactions."""
        witness = create_witness(empathy=empathy, name="TestWitness")

        concern_keywords = ["concerned", "winces", "sympathetically", "worry", "frowns"]
        found_concern = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["A", "B"],
                significance=7,
            )
            if reaction and any(kw in reaction.lower() for kw in concern_keywords):
                found_concern = True
                break

        if expected_concern:
            assert found_concern, f"Expected concern reaction for empathy={empathy}"

    @pytest.mark.parametrize(
        "curiosity,expected_interest",
        [
            (7, True),  # Threshold
            (9, True),  # High curiosity
            (6, False),  # Below threshold
            (4, False),  # Low curiosity
        ],
    )
    def test_curiosity_threshold_for_interest(self, curiosity, expected_interest):
        """Test that curiosity threshold (>=7) triggers interest reactions."""
        witness = create_witness(curiosity=curiosity, name="TestWitness")

        interest_keywords = ["leans", "interest", "perks", "closer", "intently", "keen"]
        found_interest = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["A", "B"],
                significance=6,
            )
            if reaction and any(kw in reaction.lower() for kw in interest_keywords):
                found_interest = True
                break

        if expected_interest:
            assert found_interest, f"Expected interest reaction for curiosity={curiosity}"

    @pytest.mark.parametrize(
        "discretion,expected_audible",
        [
            (3, True),  # Threshold
            (2, True),  # Low discretion
            (1, True),  # Very low discretion
            (4, False),  # Above threshold
            (5, False),  # Default
        ],
    )
    def test_discretion_threshold_for_audible(self, discretion, expected_audible):
        """Test that low discretion (<=3) triggers audible reactions."""
        witness = create_witness(discretion=discretion, name="TestWitness")

        audible_keywords = ["gasps", "audibly", "mutters", "whispers", "exclaims", "ooh", "giggle"]
        found_audible = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["A", "B"],
                significance=7,
            )
            if reaction and any(kw in reaction.lower() for kw in audible_keywords):
                found_audible = True
                break

        if expected_audible:
            assert found_audible, f"Expected audible reaction for discretion={discretion}"

    @pytest.mark.parametrize(
        "discretion,expected_subtle",
        [
            (7, True),  # Threshold
            (8, True),  # High discretion
            (10, True),  # Max discretion
            (6, False),  # Below threshold
        ],
    )
    def test_discretion_threshold_for_subtle(self, discretion, expected_subtle):
        """Test that high discretion (>=7) triggers subtle reactions."""
        witness = create_witness(discretion=discretion, name="TestWitness")

        subtle_keywords = ["glances", "briefly", "eyebrow", "imperceptibly", "noticed", "continues"]
        found_subtle = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="talk",
                actors=["A", "B"],
                significance=5,
            )
            if reaction and any(kw in reaction.lower() for kw in subtle_keywords):
                found_subtle = True
                break

        if expected_subtle:
            assert found_subtle, f"Expected subtle reaction for discretion={discretion}"


class TestReactionEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_reaction_includes_witness_name(self):
        """All reactions should include the witness's name."""
        witness = create_witness(name="UniqueWitnessName")

        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["A", "B"],
                significance=7,
            )
            if reaction:
                assert "UniqueWitnessName" in reaction

    def test_missing_traits_use_defaults(self):
        """Missing traits in traits_dict should use default value of 5."""
        agent = MagicMock()
        agent.name = "NoTraits"
        agent.traits_dict = {}  # No traits defined

        # Should still generate reactions using defaults
        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=agent,
                event_type="confront",
                actors=["A", "B"],
                significance=7,
            )
            if reaction:
                reactions.append(reaction)

        # With default traits (5 for all), should get neutral reactions
        assert len(reactions) > 0

    def test_high_significance_always_generates_reaction(self):
        """High significance events should always generate a reaction."""
        witness = create_witness(name="Watcher")

        # High significance (>3) should always produce reactions
        for _ in range(50):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="confront",
                actors=["A", "B"],
                significance=10,  # Maximum significance
            )
            assert reaction is not None, "High significance should always produce reaction"

    def test_unknown_event_type_uses_defaults(self):
        """Unknown event types should use default reactions."""
        witness = create_witness(empathy=5, curiosity=5, discretion=5, name="Observer")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="unknown_event",
                actors=["A", "B"],
                significance=5,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0
        # Default reactions include generic responses
        default_keywords = ["glances", "direction", "eyebrow"]
        has_default = any(
            any(kw in r.lower() for kw in default_keywords) for r in reactions
        )
        assert has_default, f"Expected default reactions, got: {reactions}"

    def test_multiple_high_traits_combine_reactions(self):
        """Witnesses with multiple high traits can produce varied reactions."""
        # Witness with both high empathy and high curiosity
        witness = create_witness(empathy=8, curiosity=8, discretion=5, name="Complex")

        reactions = set()
        for _ in range(50):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="gossip",
                actors=["A", "B"],
                significance=6,
            )
            if reaction:
                reactions.add(reaction)

        # Should have variety due to multiple trait-based reaction pools
        assert len(reactions) > 1, "Expected varied reactions from multiple high traits"


class TestEventTypeReactions:
    """Tests for specific event type reactions."""

    @pytest.mark.parametrize(
        "event_type",
        ["confront", "gossip", "help", "give", "tell", "investigate", "avoid"],
    )
    def test_all_event_types_generate_reactions(self, event_type):
        """All defined event types should be able to generate reactions."""
        witness = create_witness(empathy=7, curiosity=7, discretion=3, name="Tester")

        reactions = []
        for _ in range(20):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type=event_type,
                actors=["A", "B"],
                significance=7,
            )
            if reaction:
                reactions.append(reaction)

        assert len(reactions) > 0, f"Event type '{event_type}' should generate reactions"

    def test_avoid_triggers_empathy_concern(self):
        """Avoid events trigger concern in empathetic witnesses (like confront)."""
        witness = create_witness(empathy=8, name="Empath")

        concern_keywords = ["concerned", "winces", "sympathetically", "worry", "frowns"]
        found_concern = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="avoid",
                actors=["A", "B"],
                significance=6,
            )
            if reaction and any(kw in reaction.lower() for kw in concern_keywords):
                found_concern = True
                break

        assert found_concern, "Avoid events should trigger empathy concern reactions"

    def test_investigate_triggers_curiosity(self):
        """Investigate events trigger reactions in curious witnesses."""
        witness = create_witness(curiosity=8, name="Detective")

        interest_keywords = ["eyes", "widen", "interest"]
        found_interest = False

        for _ in range(30):
            reaction = generate_witness_reaction(
                witness_agent=witness,
                event_type="investigate",
                actors=["A", "B"],
                significance=6,
            )
            if reaction and any(kw in reaction.lower() for kw in interest_keywords):
                found_interest = True
                break

        assert found_interest, "Investigate events should trigger curiosity reactions"
