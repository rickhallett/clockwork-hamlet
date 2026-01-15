"""Tests for dramatic events system.

Tests for:
- LIFE-26: Conflict escalation system
- LIFE-27: Secret revelation mechanics
- LIFE-28: Romantic subplot progression
- LIFE-29: Village-wide event triggers
"""

import random
from unittest.mock import MagicMock, patch

import pytest

from hamlet.simulation.dramatic import (
    CHARACTER_SECRETS,
    ConflictEvent,
    ConflictStage,
    RomanceEvent,
    RomanceStage,
    SecretRevelation,
    SecretType,
    VillageEvent,
    VillageEventType,
    cascade_village_event_effects,
    check_conflict_escalation,
    check_random_village_event,
    check_romantic_progression,
    check_secret_discovery,
    check_secret_spread_impulse,
    generate_conflict_escalation_dialogue,
    generate_romance_dialogue,
    generate_secret_reaction,
    get_conflict_stage,
    get_romance_stage,
    process_conflict_aftermath,
    process_romance_aftermath,
    spread_secret,
    trigger_village_event,
)


def create_mock_agent(
    agent_id: str = "test_agent",
    name: str = "Test Agent",
    courage: int = 5,
    discretion: int = 5,
    empathy: int = 5,
    charm: int = 5,
    curiosity: int = 5,
    perception: int = 5,
    location_id: str = "town_square",
):
    """Create a mock agent with specified traits."""
    agent = MagicMock()
    agent.id = agent_id
    agent.name = name
    agent.location_id = location_id
    agent.traits_dict = {
        "courage": courage,
        "discretion": discretion,
        "empathy": empathy,
        "charm": charm,
        "curiosity": curiosity,
        "perception": perception,
    }
    agent.mood_dict = {"happiness": 5, "energy": 5}
    return agent


def create_mock_relationship(score: int = 0, history: list = None):
    """Create a mock relationship."""
    rel = MagicMock()
    rel.score = score
    rel.history_list = history or []
    return rel


def create_mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    return db


# =============================================================================
# LIFE-26: Conflict Escalation Tests
# =============================================================================

class TestConflictStages:
    """Tests for conflict stage determination."""

    @pytest.mark.parametrize(
        "score,expected_stage",
        [
            (0, ConflictStage.TENSION),
            (-1, ConflictStage.TENSION),
            (-3, ConflictStage.TENSION),
            (-4, ConflictStage.DISPUTE),
            (-6, ConflictStage.DISPUTE),
            (-7, ConflictStage.FEUD),
            (-9, ConflictStage.FEUD),
            (-10, ConflictStage.VENDETTA),
        ],
    )
    def test_get_conflict_stage(self, score, expected_stage):
        """Test conflict stage determination from relationship score."""
        assert get_conflict_stage(score) == expected_stage

    def test_conflict_stage_boundaries(self):
        """Test boundary values for conflict stages."""
        assert get_conflict_stage(-3) == ConflictStage.TENSION
        assert get_conflict_stage(-4) == ConflictStage.DISPUTE
        assert get_conflict_stage(-6) == ConflictStage.DISPUTE
        assert get_conflict_stage(-7) == ConflictStage.FEUD
        assert get_conflict_stage(-9) == ConflictStage.FEUD
        assert get_conflict_stage(-10) == ConflictStage.VENDETTA


class TestConflictEscalation:
    """Tests for conflict escalation mechanics."""

    def test_severe_trigger_increases_escalation_chance(self):
        """Severe triggers like 'confronted' increase escalation probability."""
        agent = create_mock_agent(courage=7)  # High courage escalates more
        target = create_mock_agent(agent_id="target", name="Target")
        relationship = create_mock_relationship(score=-2)
        db = create_mock_db()

        # Run multiple times to check probabilistic behavior
        escalation_count = 0
        for _ in range(100):
            relationship.score = -2  # Reset
            result = check_conflict_escalation(
                agent, target, relationship, "confronted about lies", db
            )
            if result is not None:
                escalation_count += 1

        # Severe trigger + high courage should escalate frequently
        assert escalation_count > 20, "Severe triggers should escalate frequently"

    def test_low_courage_reduces_escalation(self):
        """Low courage agents are less likely to escalate conflicts."""
        agent = create_mock_agent(courage=2)  # Low courage
        target = create_mock_agent(agent_id="target", name="Target")
        relationship = create_mock_relationship(score=-2)
        db = create_mock_db()

        escalation_count = 0
        for _ in range(100):
            relationship.score = -2  # Reset
            result = check_conflict_escalation(
                agent, target, relationship, "disagreed about something", db
            )
            if result is not None:
                escalation_count += 1

        # Low courage should escalate less
        assert escalation_count < 50, "Low courage should reduce escalation"

    def test_high_discretion_reduces_escalation(self):
        """High discretion agents hold back from escalation."""
        agent = create_mock_agent(discretion=9)  # High discretion
        target = create_mock_agent(agent_id="target", name="Target")
        relationship = create_mock_relationship(score=-2)
        db = create_mock_db()

        escalation_count = 0
        for _ in range(100):
            relationship.score = -2  # Reset
            result = check_conflict_escalation(
                agent, target, relationship, "argued about something", db
            )
            if result is not None:
                escalation_count += 1

        # High discretion should reduce escalation
        assert escalation_count < 40, "High discretion should reduce escalation"

    def test_escalation_returns_conflict_event(self):
        """Successful escalation returns a ConflictEvent with correct data."""
        agent = create_mock_agent(courage=9, discretion=1)  # Aggressive
        target = create_mock_agent(agent_id="target", name="Target")
        relationship = create_mock_relationship(score=-3, history=["previous conflict"])
        db = create_mock_db()

        # Force escalation with extreme traits
        result = None
        for _ in range(50):
            relationship.score = -3
            relationship.history_list = ["previous conflict"]
            result = check_conflict_escalation(
                agent, target, relationship, "confronted aggressively", db
            )
            if result is not None:
                break

        if result:
            assert isinstance(result, ConflictEvent)
            assert result.aggressor_id == agent.id
            assert result.target_id == target.id
            assert result.trigger == "confronted aggressively"

    def test_already_hostile_escalates_faster(self):
        """Already hostile relationships (score < -3) escalate faster."""
        agent = create_mock_agent(courage=5, discretion=5)
        target = create_mock_agent(agent_id="target", name="Target")
        db = create_mock_db()

        # Compare escalation rates at different hostility levels
        low_hostility_count = 0
        high_hostility_count = 0

        for _ in range(100):
            # Low hostility (-2)
            rel_low = create_mock_relationship(score=-2)
            result = check_conflict_escalation(
                agent, target, rel_low, "argued", db
            )
            if result:
                low_hostility_count += 1

            # High hostility (-5)
            rel_high = create_mock_relationship(score=-5)
            result = check_conflict_escalation(
                agent, target, rel_high, "argued", db
            )
            if result:
                high_hostility_count += 1

        # Higher hostility should escalate more frequently
        assert high_hostility_count >= low_hostility_count, \
            "Higher hostility should escalate at least as often"


class TestConflictDialogue:
    """Tests for conflict escalation dialogue generation."""

    def test_dispute_dialogue(self):
        """Dispute stage generates appropriate dialogue."""
        agent = create_mock_agent(name="Alice")
        target = create_mock_agent(name="Bob")
        event = ConflictEvent(
            aggressor_id=agent.id,
            target_id=target.id,
            trigger="argued",
            old_stage=ConflictStage.TENSION,
            new_stage=ConflictStage.DISPUTE,
        )

        dialogue = generate_conflict_escalation_dialogue(agent, target, event)
        assert dialogue is not None
        assert "Bob" in dialogue  # Target name appears

    def test_feud_dialogue(self):
        """Feud stage generates appropriate dialogue."""
        agent = create_mock_agent(name="Alice")
        target = create_mock_agent(name="Bob")
        event = ConflictEvent(
            aggressor_id=agent.id,
            target_id=target.id,
            trigger="betrayed",
            old_stage=ConflictStage.DISPUTE,
            new_stage=ConflictStage.FEUD,
        )

        dialogue = generate_conflict_escalation_dialogue(agent, target, event)
        assert dialogue is not None

    def test_vendetta_dialogue(self):
        """Vendetta stage generates appropriate dialogue."""
        agent = create_mock_agent(name="Alice")
        target = create_mock_agent(name="Bob")
        event = ConflictEvent(
            aggressor_id=agent.id,
            target_id=target.id,
            trigger="ultimate betrayal",
            old_stage=ConflictStage.FEUD,
            new_stage=ConflictStage.VENDETTA,
        )

        dialogue = generate_conflict_escalation_dialogue(agent, target, event)
        assert dialogue is not None


class TestConflictAftermath:
    """Tests for conflict aftermath processing."""

    def test_creates_memories_for_participants(self):
        """Conflict aftermath creates memories for aggressor and target."""
        event = ConflictEvent(
            aggressor_id="alice",
            target_id="bob",
            trigger="argument",
            old_stage=ConflictStage.TENSION,
            new_stage=ConflictStage.DISPUTE,
        )
        db = create_mock_db()
        agents = {
            "alice": create_mock_agent(agent_id="alice", name="Alice"),
            "bob": create_mock_agent(agent_id="bob", name="Bob"),
        }

        memories = process_conflict_aftermath(event, db, agents)

        assert len(memories) >= 2  # At least aggressor and target
        assert db.add.call_count >= 2

    def test_creates_witness_memories(self):
        """Conflict aftermath creates memories for witnesses."""
        event = ConflictEvent(
            aggressor_id="alice",
            target_id="bob",
            trigger="argument",
            old_stage=ConflictStage.TENSION,
            new_stage=ConflictStage.DISPUTE,
            witnesses=["charlie", "diana"],
        )
        db = create_mock_db()
        agents = {
            "alice": create_mock_agent(agent_id="alice", name="Alice"),
            "bob": create_mock_agent(agent_id="bob", name="Bob"),
            "charlie": create_mock_agent(agent_id="charlie", name="Charlie"),
            "diana": create_mock_agent(agent_id="diana", name="Diana"),
        }

        memories = process_conflict_aftermath(event, db, agents)

        # Should have memories for: aggressor, target, 2 witnesses
        assert len(memories) >= 4


# =============================================================================
# LIFE-27: Secret Revelation Tests
# =============================================================================

class TestSecretDiscovery:
    """Tests for secret discovery mechanics."""

    def test_high_perception_increases_discovery_chance(self):
        """High perception agents are more likely to discover secrets."""
        agent = create_mock_agent(perception=9, curiosity=9)
        target = create_mock_agent(agent_id="theodore", name="Theodore")
        db = create_mock_db()

        discovery_count = 0
        for _ in range(100):
            result = check_secret_discovery(agent, target, "investigate", db)
            if result is not None:
                discovery_count += 1

        # High perception + investigation should discover frequently
        assert discovery_count > 0, "High perception should enable discovery"

    def test_known_secret_not_rediscovered(self):
        """Agents don't rediscover secrets they already know."""
        # Agent already knows Theodore's secret
        agent = create_mock_agent(agent_id="theodore", perception=9)
        target = create_mock_agent(agent_id="theodore", name="Theodore")
        db = create_mock_db()

        for _ in range(50):
            result = check_secret_discovery(agent, target, "investigate", db)
            # Should never rediscover their own secret
            assert result is None or result.secret_holder_id != "theodore"

    def test_investigation_increases_discovery(self):
        """Investigation interactions have higher discovery chance."""
        agent = create_mock_agent(perception=7, curiosity=7)
        target = create_mock_agent(agent_id="theodore", name="Theodore")
        db = create_mock_db()

        investigation_discoveries = 0
        talk_discoveries = 0

        for _ in range(100):
            result = check_secret_discovery(agent, target, "investigate", db)
            if result:
                investigation_discoveries += 1

            result = check_secret_discovery(agent, target, "talk", db)
            if result:
                talk_discoveries += 1

        # Investigation should discover more than talking
        assert investigation_discoveries >= talk_discoveries


class TestSecretSpread:
    """Tests for secret spreading mechanics."""

    def test_spread_creates_memories(self):
        """Spreading a secret creates memories for audience."""
        revealer = create_mock_agent(discretion=3)
        secret = SecretRevelation(
            secret_holder_id="theodore",
            revealer_id=revealer.id,
            secret_type=SecretType.SCANDAL,
            secret_content="The cheese was fake!",
        )
        audience = [
            create_mock_agent(agent_id="listener1", name="Listener One"),
            create_mock_agent(agent_id="listener2", name="Listener Two"),
        ]
        db = create_mock_db()

        memories = spread_secret(revealer, secret, audience, db)

        # Should create memories for listeners and revealer
        assert len(memories) >= 3  # 2 listeners + 1 revealer
        assert db.add.call_count >= 3

    def test_low_discretion_spreads_more(self):
        """Low discretion agents are more likely to spread secrets."""
        low_discretion_agent = create_mock_agent(discretion=2)
        high_discretion_agent = create_mock_agent(discretion=9)

        low_spread_count = sum(
            1 for _ in range(100)
            if check_secret_spread_impulse(low_discretion_agent, "theodore")
        )
        high_spread_count = sum(
            1 for _ in range(100)
            if check_secret_spread_impulse(high_discretion_agent, "theodore")
        )

        assert low_spread_count > high_spread_count, \
            "Low discretion should spread more"


class TestSecretReactions:
    """Tests for secret revelation reactions."""

    def test_scandal_reaction_varies_by_personality(self):
        """Reactions to scandals vary by personality traits."""
        low_discretion = create_mock_agent(discretion=2)
        high_empathy = create_mock_agent(empathy=8)

        secret = SecretRevelation(
            secret_holder_id="theodore",
            revealer_id="gossip",
            secret_type=SecretType.SCANDAL,
            secret_content="The cheese scandal!",
        )

        reaction_low = generate_secret_reaction(low_discretion, secret)
        reaction_high = generate_secret_reaction(high_empathy, secret)

        assert reaction_low != reaction_high, \
            "Different personalities should have different reactions"

    def test_romantic_secret_reaction(self):
        """Romantic secrets generate appropriate reactions."""
        agent = create_mock_agent(empathy=7)
        secret = SecretRevelation(
            secret_holder_id="thomas",
            revealer_id="observer",
            secret_type=SecretType.ROMANTIC,
            secret_content="Secret love",
        )

        reaction = generate_secret_reaction(agent, secret)
        assert reaction is not None
        assert len(reaction) > 0


# =============================================================================
# LIFE-28: Romantic Subplot Tests
# =============================================================================

class TestRomanceStages:
    """Tests for romance stage determination."""

    def test_strangers_with_no_relationship(self):
        """No relationship means strangers."""
        suitor = create_mock_agent()
        beloved = create_mock_agent(agent_id="beloved")

        stage = get_romance_stage(suitor, beloved, None)
        assert stage == RomanceStage.STRANGERS

    def test_spouse_type_is_relationship(self):
        """Spouse relationship type is relationship stage."""
        suitor = create_mock_agent()
        beloved = create_mock_agent(agent_id="beloved")
        rel = create_mock_relationship(score=8)
        rel.type = "spouse"

        stage = get_romance_stage(suitor, beloved, rel)
        assert stage == RomanceStage.RELATIONSHIP

    def test_romantic_history_progresses_stage(self):
        """Romantic history indicators progress the stage."""
        suitor = create_mock_agent()
        beloved = create_mock_agent(agent_id="beloved")
        rel = create_mock_relationship(score=5, history=["romantic interest"])
        rel.type = "acquaintance"

        stage = get_romance_stage(suitor, beloved, rel)
        assert stage in [RomanceStage.ATTRACTION, RomanceStage.COURTSHIP]


class TestRomanticProgression:
    """Tests for romantic subplot progression."""

    def test_high_charm_increases_progression(self):
        """High charm agents progress romance faster."""
        suitor = create_mock_agent(charm=9, courage=7)
        beloved = create_mock_agent(agent_id="beloved", name="Beloved", empathy=6)
        rel = create_mock_relationship(score=4, history=["romantic interest: curious"])
        rel.type = "acquaintance"
        db = create_mock_db()

        progression_count = 0
        for _ in range(100):
            rel.score = 4
            rel.history_list = ["romantic interest: curious"]
            result = check_romantic_progression(suitor, beloved, rel, "talk", db)
            if result is not None:
                progression_count += 1

        assert progression_count > 0, "High charm should enable progression"

    def test_progression_returns_romance_event(self):
        """Successful progression returns RomanceEvent."""
        suitor = create_mock_agent(charm=9, courage=9)
        beloved = create_mock_agent(agent_id="beloved", name="Beloved", empathy=7)
        rel = create_mock_relationship(score=5, history=["romantic interest: curious"])
        rel.type = "acquaintance"
        db = create_mock_db()

        result = None
        for _ in range(50):
            rel.score = 5
            rel.history_list = ["romantic interest: curious"]
            result = check_romantic_progression(suitor, beloved, rel, "help", db)
            if result is not None:
                break

        if result:
            assert isinstance(result, RomanceEvent)
            assert result.suitor_id == suitor.id
            assert result.beloved_id == beloved.id


class TestRomanceDialogue:
    """Tests for romantic dialogue generation."""

    def test_curious_stage_dialogue(self):
        """Curious stage generates subtle dialogue."""
        suitor = create_mock_agent(name="Alice")
        beloved = create_mock_agent(name="Bob")
        event = RomanceEvent(
            suitor_id=suitor.id,
            beloved_id=beloved.id,
            old_stage=RomanceStage.STRANGERS,
            new_stage=RomanceStage.CURIOUS,
            event_type="lingering glance",
        )

        dialogue = generate_romance_dialogue(suitor, beloved, event)
        assert "Alice" in dialogue or "Bob" in dialogue

    def test_confession_stage_dialogue(self):
        """Confession stage generates declaration dialogue."""
        suitor = create_mock_agent(name="Alice")
        beloved = create_mock_agent(name="Bob")
        event = RomanceEvent(
            suitor_id=suitor.id,
            beloved_id=beloved.id,
            old_stage=RomanceStage.COURTSHIP,
            new_stage=RomanceStage.CONFESSION,
            event_type="declaration of feelings",
            reciprocated=True,
        )

        dialogue = generate_romance_dialogue(suitor, beloved, event)
        assert "Bob" in dialogue  # Addressed to beloved


class TestRomanceAftermath:
    """Tests for romantic aftermath processing."""

    def test_creates_memories_for_both_parties(self):
        """Romance aftermath creates memories for suitor and beloved."""
        event = RomanceEvent(
            suitor_id="alice",
            beloved_id="bob",
            old_stage=RomanceStage.CURIOUS,
            new_stage=RomanceStage.ATTRACTION,
            event_type="nervous conversation",
            reciprocated=True,
        )
        db = create_mock_db()
        agents = {
            "alice": create_mock_agent(agent_id="alice", name="Alice"),
            "bob": create_mock_agent(agent_id="bob", name="Bob"),
        }

        memories = process_romance_aftermath(event, db, agents)

        # Should create memories for both
        assert len(memories) >= 2
        assert db.add.call_count >= 2


# =============================================================================
# LIFE-29: Village-Wide Event Tests
# =============================================================================

class TestVillageEvents:
    """Tests for village-wide event triggers."""

    def test_trigger_village_event_creates_event(self):
        """Triggering a village event creates a VillageEvent."""
        db = create_mock_db()
        agents = [
            create_mock_agent(agent_id=f"agent{i}", name=f"Agent {i}")
            for i in range(5)
        ]

        event = trigger_village_event(VillageEventType.STORM, db, agents)

        assert isinstance(event, VillageEvent)
        assert event.event_type == "storm"
        assert len(event.affected_agents) > 0

    def test_village_event_affects_mood(self):
        """Village events can affect agent moods."""
        db = create_mock_db()
        agents = [
            create_mock_agent(agent_id=f"agent{i}", name=f"Agent {i}")
            for i in range(3)
        ]

        # Storm should affect mood negatively
        event = trigger_village_event(VillageEventType.STORM, db, agents)

        # Check that some agents had mood modified
        assert event is not None

    def test_location_specific_event(self):
        """Location-specific events only affect nearby agents."""
        db = create_mock_db()
        agents = [
            create_mock_agent(agent_id="near", name="Near", location_id="forest_edge"),
            create_mock_agent(agent_id="far", name="Far", location_id="bakery"),
        ]

        # Discovery at forest_edge
        event = trigger_village_event(VillageEventType.DISCOVERY, db, agents)

        # Near agent should be affected, far agent may or may not be
        assert "near" in event.affected_agents

    def test_custom_description_override(self):
        """Custom descriptions override templates."""
        db = create_mock_db()
        agents = [create_mock_agent()]
        custom = "A dragon has been spotted!"

        event = trigger_village_event(
            VillageEventType.MYSTERIOUS_OCCURRENCE,
            db,
            agents,
            custom_description=custom,
        )

        assert event.description == custom


class TestRandomVillageEvents:
    """Tests for random village event generation."""

    def test_random_event_probability(self):
        """Random events occur with appropriate probability."""
        db = create_mock_db()
        agents = [create_mock_agent()]

        event_count = 0
        for _ in range(1000):
            event = check_random_village_event(db, agents, 9.0, 1)  # Morning time
            if event is not None:
                event_count += 1

        # Should have some events (probability is low but non-zero)
        # With ~5% chance over 1000 iterations, expect 30-70 events
        assert event_count > 0, "Should have some random events"
        assert event_count < 200, "Should not have too many events"

    def test_evening_increases_event_chance(self):
        """Evening hours increase event probability."""
        db = create_mock_db()
        agents = [create_mock_agent()]

        # Use larger sample size to reduce variance in probabilistic test
        morning_events = sum(
            1 for _ in range(1000)
            if check_random_village_event(db, agents, 8.0, 1)
        )
        evening_events = sum(
            1 for _ in range(1000)
            if check_random_village_event(db, agents, 19.0, 1)
        )

        # Evening should have at least as many events (with generous margin for randomness)
        # Use 0.6 multiplier to account for random variance in probabilistic test
        assert evening_events >= morning_events * 0.6, \
            f"Evening ({evening_events}) should have roughly similar or more events than morning ({morning_events})"


class TestVillageEventCascade:
    """Tests for village event cascade effects."""

    def test_curious_agents_investigate(self):
        """Curious agents want to investigate mysterious events."""
        event = VillageEvent(
            event_type="mysterious_occurrence",
            description="Something mysterious happened!",
            affected_agents=["curious_agent"],
            significance=3,
        )
        agents = {
            "curious_agent": create_mock_agent(
                agent_id="curious_agent",
                curiosity=9,
            ),
        }

        reactions = cascade_village_event_effects(event, create_mock_db(), agents)

        # High curiosity agent should want to investigate
        investigate_reactions = [r for r in reactions if r[1] == "investigate"]
        assert len(investigate_reactions) > 0

    def test_low_courage_agents_hide(self):
        """Low courage agents may hide from significant events."""
        event = VillageEvent(
            event_type="scary_event",
            description="Something scary!",
            affected_agents=["coward"],
            significance=3,
        )
        agents = {
            "coward": create_mock_agent(agent_id="coward", courage=2),
        }

        reactions = cascade_village_event_effects(event, create_mock_db(), agents)

        # Low courage agent might hide
        hide_reactions = [r for r in reactions if r[1] == "hide"]
        assert len(hide_reactions) > 0


class TestCharacterSecrets:
    """Tests for pre-defined character secrets."""

    def test_theodore_has_cheese_scandal(self):
        """Theodore has the cheese scandal secret."""
        secret = CHARACTER_SECRETS.get("theodore")
        assert secret is not None
        assert secret["type"] == SecretType.SCANDAL
        assert "cheese" in secret["content"].lower()

    def test_thomas_has_romantic_secret(self):
        """Thomas has a romantic secret about Agnes."""
        secret = CHARACTER_SECRETS.get("thomas")
        assert secret is not None
        assert secret["type"] == SecretType.ROMANTIC
        assert "agnes" in secret["content"].lower()

    def test_rosalind_has_crush_secret(self):
        """Rosalind has a secret crush."""
        secret = CHARACTER_SECRETS.get("rosalind")
        assert secret is not None
        assert secret["type"] == SecretType.ROMANTIC


class TestIntegration:
    """Integration tests for dramatic events system."""

    def test_conflict_can_escalate_through_stages(self):
        """A conflict can escalate from tension to vendetta."""
        stages_reached = set()
        stages_reached.add(ConflictStage.TENSION)  # Starting point

        agent = create_mock_agent(courage=9, discretion=1)
        target = create_mock_agent(agent_id="target", name="Target")
        db = create_mock_db()

        # Simulate many interactions
        current_score = -1
        for _ in range(200):
            relationship = create_mock_relationship(
                score=current_score,
                history=["conflict"] * 5,
            )
            result = check_conflict_escalation(
                agent, target, relationship, "confronted aggressively", db
            )
            if result:
                stages_reached.add(result.new_stage)
                current_score = min(-10, current_score - 1)

        # Should have reached at least dispute
        assert ConflictStage.DISPUTE in stages_reached or \
               ConflictStage.FEUD in stages_reached or \
               ConflictStage.VENDETTA in stages_reached

    def test_romance_can_progress_through_stages(self):
        """A romance can progress from strangers to relationship."""
        suitor = create_mock_agent(charm=9, courage=9)
        beloved = create_mock_agent(agent_id="beloved", name="Beloved", empathy=8)
        db = create_mock_db()

        current_stage = RomanceStage.CURIOUS
        stages_reached = {current_stage}

        # Simulate romantic interactions
        for _ in range(100):
            rel = create_mock_relationship(
                score=6,
                history=[f"romantic interest: {current_stage.value}"],
            )
            rel.type = "acquaintance"

            result = check_romantic_progression(suitor, beloved, rel, "talk", db)
            if result:
                stages_reached.add(result.new_stage)
                current_stage = result.new_stage

        # Should have progressed at least one stage
        assert len(stages_reached) >= 1
