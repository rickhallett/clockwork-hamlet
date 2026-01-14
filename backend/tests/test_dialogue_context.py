"""Tests for the dialogue context helper functions.

This module tests the context building functions used to generate
rich, personality-aware dialogue prompts for agents.

Tests cover:
- Trait voice hints based on personality traits
- Relationship subtext based on relationship scores and history
- Shared memory hints for referencing past interactions
"""

import json
import time

import pytest

from hamlet.db import Agent, Memory, Relationship
from hamlet.llm.context import (
    build_dialogue_prompt,
    get_relationship_subtext,
    get_running_joke_hints,
    get_shared_memory_hint,
    get_trait_voice_hints,
)


# Note: The 'world', 'agent', and 'db' fixtures are provided by conftest.py


@pytest.mark.unit
class TestTraitVoiceHints:
    """Test get_trait_voice_hints() function.

    This function generates speaking style hints based on an agent's
    personality traits to guide dialogue generation.
    """

    def test_low_discretion_blurts_out(self, agent, db):
        """Low discretion trait causes blurting/oversharing hint."""
        # Set low discretion
        traits = agent.traits_dict
        traits["discretion"] = 2
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "blurt" in hints.lower()
        assert "overshare" in hints.lower()

    def test_high_discretion_speaks_carefully(self, agent, db):
        """High discretion trait causes careful speaking hint."""
        traits = agent.traits_dict
        traits["discretion"] = 9
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "carefully" in hints.lower()
        assert "revealing little" in hints.lower()

    def test_high_charm_puts_at_ease(self, agent, db):
        """High charm trait causes putting people at ease hint."""
        traits = agent.traits_dict
        traits["charm"] = 9
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "charming" in hints.lower()
        assert "at ease" in hints.lower()

    def test_low_charm_blunt_awkward(self, agent, db):
        """Low charm trait causes blunt/awkward hint."""
        traits = agent.traits_dict
        traits["charm"] = 2
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "blunt" in hints.lower()
        assert "awkward" in hints.lower()

    def test_high_energy_speaks_quickly(self, agent, db):
        """High energy trait causes quick/enthusiastic speech hint."""
        traits = agent.traits_dict
        traits["energy"] = 9
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "quickly" in hints.lower()
        assert "enthusiasm" in hints.lower()

    def test_low_energy_economy_of_words(self, agent, db):
        """Low energy trait causes economy of words hint."""
        traits = agent.traits_dict
        traits["energy"] = 2
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "slowly" in hints.lower()
        assert "economy of words" in hints.lower()

    def test_high_empathy_notices_feelings(self, agent, db):
        """High empathy trait causes noticing feelings hint."""
        traits = agent.traits_dict
        traits["empathy"] = 9
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "feel" in hints.lower()
        assert "notice" in hints.lower()

    def test_high_curiosity_asks_questions(self, agent, db):
        """High curiosity trait causes question-asking hint."""
        traits = agent.traits_dict
        traits["curiosity"] = 9
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert "question" in hints.lower()
        assert "know more" in hints.lower()

    def test_moderate_traits_straightforward(self, agent, db):
        """Moderate traits result in straightforward speaking hint."""
        # Set all traits to moderate values (5)
        traits = {
            "discretion": 5,
            "charm": 5,
            "energy": 5,
            "empathy": 5,
            "curiosity": 5,
        }
        agent.traits_dict = traits
        db.flush()

        hints = get_trait_voice_hints(agent)

        assert hints == "You speak in a straightforward manner"


@pytest.mark.unit
class TestRelationshipSubtext:
    """Test get_relationship_subtext() function.

    This function generates relationship-aware subtext hints
    based on the relationship score and history between two agents.

    Note: These tests create relationship objects in memory without
    persisting them to the database, since get_relationship_subtext()
    takes a relationship object as a parameter.
    """

    def test_high_score_very_fond(self, world, agent, db):
        """High relationship score generates 'very fond' subtext."""
        target = world.get_agent("bob")

        # Create a high-score relationship (not persisted to DB)
        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="friend",
            score=8,
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "very fond" in subtext.lower()
        assert target.name in subtext

    def test_medium_score_likes(self, world, agent, db):
        """Medium relationship score generates 'like' subtext."""
        target = world.get_agent("bob")

        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="acquaintance",
            score=5,
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "like" in subtext.lower()
        assert target.name in subtext

    def test_neutral_score_neutral(self, world, agent, db):
        """Neutral relationship score generates 'neutral' subtext."""
        target = world.get_agent("bob")

        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="acquaintance",
            score=0,
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "neutral" in subtext.lower()
        assert target.name in subtext

    def test_negative_score_wary(self, world, agent, db):
        """Negative relationship score generates 'wary' subtext."""
        target = world.get_agent("bob")

        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="rival",
            score=-2,
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "wary" in subtext.lower()
        assert target.name in subtext

    def test_very_negative_score_dislikes(self, world, agent, db):
        """Very negative relationship score generates 'dislike' subtext."""
        target = world.get_agent("bob")

        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="enemy",
            score=-6,
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "dislike" in subtext.lower()
        assert target.name in subtext

    def test_no_relationship_stranger(self, world, agent, db):
        """No relationship returns stranger subtext."""
        target = world.get_agent("bob")

        subtext = get_relationship_subtext(agent, target, None, world)

        assert "don't know" in subtext.lower()
        assert "well yet" in subtext.lower()
        assert target.name in subtext

    def test_includes_history_when_present(self, world, agent, db):
        """Relationship with history includes history in subtext."""
        target = world.get_agent("bob")

        history = ["They helped me when I was sick"]
        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="friend",
            score=6,
            history=json.dumps(history),
        )

        subtext = get_relationship_subtext(agent, target, rel, world)

        assert "history" in subtext.lower()
        assert "helped me when I was sick" in subtext

    def test_detects_romantic_subtext_in_prompt(self, world, db):
        """Detects romantic feelings from personality prompt."""
        # Get Agnes and Bob
        agnes = world.get_agent("agnes")
        bob = world.get_agent("bob")

        # Set Agnes's personality to have a crush on Bob
        agnes.personality_prompt = "Agnes is a shy woman who has a crush on Bob."
        db.flush()

        rel = Relationship(
            agent_id=agnes.id,
            target_id=bob.id,
            type="acquaintance",
            score=4,
        )

        subtext = get_relationship_subtext(agnes, bob, rel, world)

        assert "romantic feelings" in subtext.lower()
        assert "secret" in subtext.lower()


@pytest.mark.integration
class TestSharedMemoryHint:
    """Test get_shared_memory_hint() function.

    This function finds memories mentioning a target agent
    and returns hints for referencing past interactions.
    """

    def test_finds_memories_mentioning_target(self, world, agent, db):
        """Finds memories that mention the target agent's name."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a memory mentioning Bob with high significance
        memory = Memory(
            agent_id=agent.id,
            content=f"Had an interesting conversation with {target.name} about farming",
            significance=7,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        assert hint is not None
        assert "conversation" in hint.lower()
        assert target.name in hint

    def test_prioritizes_high_significance_memories(self, world, agent, db):
        """Higher significance memories are prioritized."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        now = int(time.time())

        # Add low significance memory first (older)
        low_sig = Memory(
            agent_id=agent.id,
            content=f"Saw {target.name} walking by",
            significance=3,
            timestamp=now - 1000,
            type="working",
        )
        db.add(low_sig)

        # Add high significance memory (newer)
        high_sig = Memory(
            agent_id=agent.id,
            content=f"{target.name} saved my life from the fire!",
            significance=9,
            timestamp=now,
            type="working",
        )
        db.add(high_sig)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        assert hint is not None
        # High significance memory should be included
        assert "saved my life" in hint or "fire" in hint
        # Low significance memory (below 5) should NOT be included
        assert "walking by" not in hint

    def test_limits_to_two_memories(self, world, agent, db):
        """Only returns up to two shared memories."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        now = int(time.time())

        # Add multiple high-significance memories mentioning the target
        for i in range(5):
            memory = Memory(
                agent_id=agent.id,
                content=f"Memory {i}: {target.name} did something memorable",
                significance=7,
                timestamp=now - i * 100,
                type="working",
            )
            db.add(memory)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        assert hint is not None
        # Count how many "You could reference:" lines there are
        reference_count = hint.count("You could reference:")
        assert reference_count <= 2

    def test_returns_none_when_no_shared_memories(self, world, agent, db):
        """Returns None when no memories mention the target."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add memories that don't mention the target
        memory = Memory(
            agent_id=agent.id,
            content="Had breakfast alone this morning",
            significance=5,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        assert hint is None

    def test_only_includes_significance_5_or_higher(self, world, agent, db):
        """Only includes memories with significance >= 5."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        now = int(time.time())

        # Add a low significance memory mentioning target
        low_sig = Memory(
            agent_id=agent.id,
            content=f"Briefly saw {target.name} pass by",
            significance=4,
            timestamp=now,
            type="working",
        )
        db.add(low_sig)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        # Should return None because the only matching memory is below significance 5
        assert hint is None

        # Now add a high significance memory
        high_sig = Memory(
            agent_id=agent.id,
            content=f"{target.name} shared a secret with me",
            significance=8,
            timestamp=now + 100,
            type="working",
        )
        db.add(high_sig)
        db.flush()

        hint = get_shared_memory_hint(agent, target, world)

        assert hint is not None
        assert "secret" in hint.lower()


@pytest.mark.integration
class TestBuildDialoguePrompt:
    """Test the full build_dialogue_prompt() function.

    This tests the integration of all the helper functions
    into a complete dialogue prompt.
    """

    def test_includes_voice_hints(self, world, agent, db):
        """Built prompt includes voice hints section."""
        target = world.get_agent("bob")

        prompt = build_dialogue_prompt(agent, target, world)

        assert "YOUR VOICE:" in prompt

    def test_includes_relationship_info(self, world, agent, db):
        """Built prompt includes relationship information."""
        target = world.get_agent("bob")

        # The seeded database already has relationships between agents,
        # so we just verify the prompt includes the expected sections
        prompt = build_dialogue_prompt(agent, target, world)

        assert target.name in prompt
        assert "SPEAKING TO:" in prompt

    def test_includes_shared_history_when_present(self, world, agent, db):
        """Built prompt includes shared history section when memories exist."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a significant shared memory
        memory = Memory(
            agent_id=agent.id,
            content=f"Worked together with {target.name} on the harvest",
            significance=7,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        prompt = build_dialogue_prompt(agent, target, world)

        assert "SHARED HISTORY" in prompt
        assert "harvest" in prompt.lower()

    def test_includes_context_type(self, world, agent, db):
        """Built prompt includes the context type."""
        target = world.get_agent("bob")

        prompt = build_dialogue_prompt(agent, target, world, context_type="argument")

        assert "SITUATION:" in prompt
        assert "argument" in prompt

    def test_includes_running_jokes_for_positive_relationship(self, world, agent, db):
        """Built prompt includes running jokes section when agents have positive relationship and shared funny memories."""
        target = world.get_agent("bob")

        # Clear existing memories and relationships
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.query(Relationship).filter(
            Relationship.agent_id == agent.id, Relationship.target_id == target.id
        ).delete()
        db.flush()

        # Create a positive relationship
        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="friend",
            score=5,
        )
        db.add(rel)

        # Add a funny memory mentioning target
        memory = Memory(
            agent_id=agent.id,
            content=f"Had a hilarious time with {target.name} when he tripped into the fountain",
            significance=7,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        prompt = build_dialogue_prompt(agent, target, world)

        assert "RUNNING JOKES" in prompt
        assert "INSIDE JOKE" in prompt
        assert "fountain" in prompt.lower()

    def test_no_running_jokes_for_negative_relationship(self, world, agent, db):
        """Built prompt does not include running jokes for negative relationships."""
        target = world.get_agent("bob")

        # Clear existing memories and relationships
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.query(Relationship).filter(
            Relationship.agent_id == agent.id, Relationship.target_id == target.id
        ).delete()
        db.flush()

        # Create a negative relationship
        rel = Relationship(
            agent_id=agent.id,
            target_id=target.id,
            type="rival",
            score=-3,
        )
        db.add(rel)

        # Add a funny memory mentioning target
        memory = Memory(
            agent_id=agent.id,
            content=f"Saw {target.name} fall in an embarrassing way",
            significance=7,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        prompt = build_dialogue_prompt(agent, target, world)

        # Running jokes section should NOT appear for negative relationships
        assert "RUNNING JOKES" not in prompt


@pytest.mark.integration
class TestRunningJokeHints:
    """Test get_running_joke_hints() function.

    This function finds funny or highly memorable shared experiences
    that could be referenced as inside jokes between agents.
    """

    def test_finds_funny_memory_with_keyword(self, world, agent, db):
        """Finds memories with funny keywords mentioning the target."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a funny memory mentioning target
        memory = Memory(
            agent_id=agent.id,
            content=f"{target.name} had a hilarious accident with the chicken coop",
            significance=6,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        assert hint is not None
        assert "INSIDE JOKE" in hint
        assert target.name in hint
        assert "chicken" in hint.lower()

    def test_finds_embarrassing_memory(self, world, agent, db):
        """Finds memories with embarrassing situations."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add an embarrassing memory
        memory = Memory(
            agent_id=agent.id,
            content=f"{target.name} tripped and spilled soup everywhere",
            significance=6,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        assert hint is not None
        assert "INSIDE JOKE" in hint
        assert "soup" in hint.lower()

    def test_finds_high_significance_memorable_event(self, world, agent, db):
        """High significance memories (>=8) are treated as memorable events."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a highly significant memory without funny keywords
        memory = Memory(
            agent_id=agent.id,
            content=f"{target.name} and I saved the village during the storm",
            significance=9,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        assert hint is not None
        assert "SHARED MOMENT" in hint
        assert "storm" in hint.lower()

    def test_limits_to_two_jokes(self, world, agent, db):
        """Only returns up to two running jokes."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        now = int(time.time())

        # Add multiple funny memories
        for i in range(5):
            memory = Memory(
                agent_id=agent.id,
                content=f"Funny incident {i}: {target.name} did something hilarious",
                significance=7,
                timestamp=now - i * 100,
                type="working",
            )
            db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        assert hint is not None
        # Count how many INSIDE JOKE lines there are
        joke_count = hint.count("INSIDE JOKE")
        assert joke_count <= 2

    def test_returns_none_when_no_joke_material(self, world, agent, db):
        """Returns None when no memories qualify as joke material."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a boring, low-significance memory mentioning target
        memory = Memory(
            agent_id=agent.id,
            content=f"Saw {target.name} at the market today",
            significance=4,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        assert hint is None

    def test_ignores_memories_not_mentioning_target(self, world, agent, db):
        """Only considers memories that mention the target."""
        target = world.get_agent("bob")

        # Clear existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.flush()

        # Add a funny memory NOT mentioning target
        memory = Memory(
            agent_id=agent.id,
            content="Something hilarious happened with a chicken",
            significance=7,
            timestamp=int(time.time()),
            type="working",
        )
        db.add(memory)
        db.flush()

        hint = get_running_joke_hints(agent, target, world)

        # Should be None because the memory doesn't mention Bob
        assert hint is None
