"""Tests for the memory system."""

import time

import pytest

from hamlet.db import Agent, Memory
from hamlet.memory import (
    MemoryManager,
    MemoryType,
    add_memory,
    build_memory_context,
    calculate_significance,
    compress_memories,
    end_of_day_compression,
    get_recent_memories,
    get_working_memories,
)
from hamlet.memory.context import get_memory_summary, get_relevant_memories
from hamlet.memory.significance import decay_significance
from hamlet.simulation.world import World


@pytest.fixture
def world():
    """Create a test world with seeded database."""
    w = World()
    yield w
    w.close()


@pytest.fixture
def agent(world) -> Agent:
    """Get a test agent."""
    return world.get_agent("agnes")


@pytest.fixture
def db(world):
    """Get database session."""
    return world.db


class TestMemoryTypes:
    """Test memory type definitions."""

    def test_memory_types_defined(self):
        """Memory types are properly defined."""
        assert MemoryType.WORKING.value == "working"
        assert MemoryType.RECENT.value == "recent"
        assert MemoryType.LONGTERM.value == "longterm"


class TestSignificance:
    """Test significance calculation."""

    def test_base_significance(self):
        """Base significance varies by event type."""
        assert calculate_significance("movement") < calculate_significance("discovery")
        assert calculate_significance("dialogue") < calculate_significance("conflict")
        assert calculate_significance("secret") >= 8

    def test_modifiers_increase_significance(self):
        """Modifiers increase significance score."""
        base = calculate_significance("dialogue")
        with_friend = calculate_significance("dialogue", involves_friend=True)
        first_time = calculate_significance("dialogue", is_first_time=True)

        assert with_friend > base
        assert first_time > base

    def test_significance_clamped(self):
        """Significance is clamped to 1-10."""
        # Very low
        low = calculate_significance("movement", involves_self=False, emotional_impact=-5)
        assert low >= 1

        # Very high
        high = calculate_significance("death", involves_friend=True, is_first_time=True)
        assert high <= 10

    def test_decay_significance(self):
        """Significance decays over time for moderate memories."""
        # Low significance decays
        assert decay_significance(4, hours_passed=72) < 4

        # High significance doesn't decay
        assert decay_significance(9, hours_passed=72) == 9

    def test_decay_minimum(self):
        """Decayed significance doesn't go below 1."""
        assert decay_significance(2, hours_passed=1000) >= 1


class TestMemoryManager:
    """Test memory CRUD operations."""

    def test_add_working_memory(self, agent, db):
        """Can add a working memory."""
        manager = MemoryManager(db)
        memory = manager.add_working_memory(agent, "Saw Bob at the market")

        assert memory.agent_id == agent.id
        assert memory.type == MemoryType.WORKING.value
        assert memory.content == "Saw Bob at the market"
        assert memory.compressed is False

    def test_add_longterm_fact(self, agent, db):
        """Can add a long-term fact."""
        manager = MemoryManager(db)
        memory = manager.add_longterm_fact(agent, "Bob is the baker's son")

        assert memory.type == MemoryType.LONGTERM.value
        assert memory.compressed is True
        assert memory.significance >= 7

    def test_get_working_memories(self, agent, db):
        """Can retrieve working memories in order."""
        manager = MemoryManager(db)

        # Clear existing memories
        manager.clear_working_memories(agent)

        # Add some memories with slight time gaps
        now = int(time.time())
        add_memory(agent.id, "First event", db, timestamp=now - 100)
        add_memory(agent.id, "Second event", db, timestamp=now - 50)
        add_memory(agent.id, "Third event", db, timestamp=now)

        memories = get_working_memories(agent.id, db)

        # Should be newest first
        assert len(memories) == 3
        assert memories[0].content == "Third event"
        assert memories[1].content == "Second event"
        assert memories[2].content == "First event"

    def test_clear_working_memories(self, agent, db):
        """Can clear working memories."""
        manager = MemoryManager(db)

        manager.add_working_memory(agent, "Memory 1")
        manager.add_working_memory(agent, "Memory 2")

        count = manager.clear_working_memories(agent)
        assert count >= 2

        remaining = get_working_memories(agent.id, db)
        assert len(remaining) == 0


class TestCompression:
    """Test memory compression."""

    def test_compress_memories_mock(self, agent):
        """Compression generates summary and facts without LLM."""
        memories = [
            Memory(
                agent_id=agent.id,
                content="Had a long conversation with Bob",
                significance=5,
                timestamp=1000,
            ),
            Memory(
                agent_id=agent.id,
                content="Discovered a secret about Martha",
                significance=8,
                timestamp=2000,
            ),
            Memory(
                agent_id=agent.id,
                content="Walked to the market",
                significance=2,
                timestamp=3000,
            ),
        ]

        summary, facts = compress_memories(memories, llm_client=None)

        # Should have a summary
        assert len(summary) > 0
        assert "secret" in summary.lower() or "Martha" in summary

        # Should extract the high-significance fact
        assert len(facts) >= 1

    def test_compress_empty_memories(self, agent):
        """Compressing empty list returns empty results."""
        summary, facts = compress_memories([], llm_client=None)

        assert summary == ""
        assert facts == []

    def test_end_of_day_compression_mock(self, agent, db):
        """End of day compression works without LLM."""
        manager = MemoryManager(db)

        # Add working memories
        manager.add_working_memory(agent, "Morning: woke up and had breakfast")
        manager.add_working_memory(agent, "Met Bob at the square", event_type="dialogue")
        manager.add_working_memory(agent, "Discovered Martha's secret", event_type="discovery")

        # Run compression
        result = end_of_day_compression(agent, db, llm_client=None)

        assert result["working_count"] >= 3
        assert result["summary"] is not None
        assert len(result["summary"]) > 0

        # Working memories should be cleared
        remaining = get_working_memories(agent.id, db)
        assert len(remaining) == 0

        # Should have recent memory (daily summary)
        recent = get_recent_memories(agent.id, db)
        assert len(recent) >= 1


class TestContext:
    """Test memory context building."""

    def test_build_memory_context(self, agent, db):
        """Can build context from all memory types."""
        manager = MemoryManager(db)

        # Add various memories
        manager.add_longterm_fact(agent, "Bob is my friend")
        manager.add_daily_summary(agent, "Yesterday was a good day", int(time.time()) - 86400)
        manager.add_working_memory(agent, "Just saw Martha")

        context = build_memory_context(agent.id, db)

        assert "THINGS I KNOW" in context
        assert "Bob is my friend" in context
        assert "RECENT DAYS" in context
        assert "JUST NOW" in context
        assert "Martha" in context

    def test_memory_context_empty(self, agent, db):
        """Empty memories return appropriate message."""
        # Clear any existing memories
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.commit()

        context = build_memory_context(agent.id, db)

        assert context == "No memories yet."

    def test_get_memory_summary(self, agent, db):
        """Can get memory count summary."""
        manager = MemoryManager(db)

        manager.add_working_memory(agent, "Working 1")
        manager.add_working_memory(agent, "Working 2")
        manager.add_longterm_fact(agent, "Fact 1")

        summary = get_memory_summary(agent.id, db)

        assert summary["working_count"] >= 2
        assert summary["longterm_count"] >= 1
        assert summary["total_count"] >= 3

    def test_get_relevant_memories(self, agent, db):
        """Can search memories by keywords."""
        manager = MemoryManager(db)

        manager.add_working_memory(agent, "Bob gave me some bread")
        manager.add_working_memory(agent, "Martha told a secret")
        manager.add_longterm_fact(agent, "Bob is the baker")

        relevant = get_relevant_memories(agent.id, db, ["Bob", "bread"])

        assert len(relevant) >= 2
        # Bob-related memories should be found
        contents = [m.content for m in relevant]
        assert any("Bob" in c for c in contents)


class TestMemoryWorkflow:
    """Test complete memory workflow."""

    def test_full_memory_lifecycle(self, agent, db):
        """Test complete cycle: add -> compress -> retrieve."""
        manager = MemoryManager(db)

        # Clear existing
        db.query(Memory).filter(Memory.agent_id == agent.id).delete()
        db.commit()

        # 1. Add working memories throughout the day
        for i in range(5):
            manager.add_working_memory(
                agent,
                f"Event {i + 1} happened",
                event_type="action",
            )

        # 2. Check should_compress
        assert manager.should_compress(agent) is False  # Only 5, need 10

        # Add more to trigger threshold
        for i in range(7):
            manager.add_working_memory(agent, f"More event {i}")

        assert manager.should_compress(agent) is True

        # 3. Run compression
        result = end_of_day_compression(agent, db, llm_client=None)

        # 4. Verify results
        assert result["working_count"] >= 10
        assert result["cleared_count"] >= 10
        assert result["summary"] is not None

        # 5. New day - working memories cleared
        working = get_working_memories(agent.id, db)
        assert len(working) == 0

        # 6. But we have a summary
        recent = get_recent_memories(agent.id, db)
        assert len(recent) >= 1
