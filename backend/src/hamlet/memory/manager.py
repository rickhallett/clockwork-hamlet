"""Memory management: CRUD operations for agent memories."""

import time

from sqlalchemy.orm import Session

from hamlet.db import Agent, Memory
from hamlet.memory.significance import calculate_significance
from hamlet.memory.types import (
    LONGTERM_MEMORY_LIMIT,
    RECENT_MEMORY_LIMIT,
    WORKING_MEMORY_LIMIT,
    MemoryType,
)


def add_memory(
    agent_id: str,
    content: str,
    db: Session,
    memory_type: MemoryType = MemoryType.WORKING,
    significance: int | None = None,
    event_type: str = "action",
    timestamp: int | None = None,
) -> Memory:
    """Add a new memory for an agent.

    Args:
        agent_id: ID of the agent
        content: The memory content
        db: Database session
        memory_type: Type of memory (working, recent, longterm)
        significance: Optional significance score (auto-calculated if not provided)
        event_type: Type of event for significance calculation
        timestamp: Optional timestamp (defaults to now)

    Returns:
        The created Memory object
    """
    if significance is None:
        significance = calculate_significance(event_type)

    if timestamp is None:
        timestamp = int(time.time())

    memory = Memory(
        agent_id=agent_id,
        content=content,
        type=memory_type.value,
        significance=significance,
        timestamp=timestamp,
        compressed=memory_type != MemoryType.WORKING,
    )

    db.add(memory)
    db.commit()

    return memory


def get_working_memories(
    agent_id: str,
    db: Session,
    limit: int = WORKING_MEMORY_LIMIT,
) -> list[Memory]:
    """Get working (recent uncompressed) memories for an agent.

    Returns memories ordered by timestamp (newest first).
    """
    return (
        db.query(Memory)
        .filter(Memory.agent_id == agent_id, Memory.type == MemoryType.WORKING.value)
        .order_by(Memory.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_recent_memories(
    agent_id: str,
    db: Session,
    limit: int = RECENT_MEMORY_LIMIT,
) -> list[Memory]:
    """Get recent (daily summary) memories for an agent.

    Returns memories ordered by timestamp (newest first).
    """
    return (
        db.query(Memory)
        .filter(Memory.agent_id == agent_id, Memory.type == MemoryType.RECENT.value)
        .order_by(Memory.timestamp.desc())
        .limit(limit)
        .all()
    )


def get_longterm_memories(
    agent_id: str,
    db: Session,
    limit: int = LONGTERM_MEMORY_LIMIT,
) -> list[Memory]:
    """Get long-term (compressed facts) memories for an agent.

    Returns memories ordered by significance (highest first).
    """
    return (
        db.query(Memory)
        .filter(Memory.agent_id == agent_id, Memory.type == MemoryType.LONGTERM.value)
        .order_by(Memory.significance.desc())
        .limit(limit)
        .all()
    )


def get_all_memories(
    agent_id: str,
    db: Session,
) -> dict[str, list[Memory]]:
    """Get all memories for an agent, organized by type."""
    return {
        "working": get_working_memories(agent_id, db),
        "recent": get_recent_memories(agent_id, db),
        "longterm": get_longterm_memories(agent_id, db),
    }


class MemoryManager:
    """Manages memories for an agent throughout simulation."""

    def __init__(self, db: Session):
        self.db = db

    def add_working_memory(
        self,
        agent: Agent,
        content: str,
        event_type: str = "action",
        significance: int | None = None,
    ) -> Memory:
        """Add a working memory for an agent."""
        return add_memory(
            agent_id=agent.id,
            content=content,
            db=self.db,
            memory_type=MemoryType.WORKING,
            significance=significance,
            event_type=event_type,
        )

    def add_longterm_fact(
        self,
        agent: Agent,
        content: str,
        significance: int = 7,
    ) -> Memory:
        """Add a long-term fact/memory."""
        return add_memory(
            agent_id=agent.id,
            content=content,
            db=self.db,
            memory_type=MemoryType.LONGTERM,
            significance=significance,
        )

    def add_daily_summary(
        self,
        agent: Agent,
        content: str,
        day_timestamp: int,
    ) -> Memory:
        """Add a daily summary memory."""
        return add_memory(
            agent_id=agent.id,
            content=content,
            db=self.db,
            memory_type=MemoryType.RECENT,
            significance=5,
            timestamp=day_timestamp,
        )

    def get_memories_for_context(self, agent: Agent) -> dict[str, list[Memory]]:
        """Get memories formatted for LLM context."""
        return get_all_memories(agent.id, self.db)

    def clear_working_memories(self, agent: Agent) -> int:
        """Clear all working memories for an agent.

        Returns the number of memories deleted.
        """
        count = (
            self.db.query(Memory)
            .filter(Memory.agent_id == agent.id, Memory.type == MemoryType.WORKING.value)
            .delete()
        )
        self.db.commit()
        return count

    def should_compress(self, agent: Agent) -> bool:
        """Check if agent has enough working memories to warrant compression."""
        count = (
            self.db.query(Memory)
            .filter(Memory.agent_id == agent.id, Memory.type == MemoryType.WORKING.value)
            .count()
        )
        return count >= WORKING_MEMORY_LIMIT
