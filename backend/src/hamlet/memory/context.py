"""Build LLM context from memory layers."""

from hamlet.db import Memory
from hamlet.memory.manager import get_all_memories


def format_memory(memory: Memory, include_significance: bool = False) -> str:
    """Format a single memory for display."""
    if include_significance:
        return f"[{memory.significance}/10] {memory.content}"
    return memory.content


def build_memory_context(
    agent_id: str,
    db,
    max_working: int = 5,
    max_recent: int = 3,
    max_longterm: int = 10,
) -> str:
    """Build a formatted memory context string for LLM prompts.

    Combines working, recent, and long-term memories into a coherent context.

    Args:
        agent_id: The agent's ID
        db: Database session
        max_working: Max working memories to include
        max_recent: Max recent summaries to include
        max_longterm: Max long-term facts to include

    Returns:
        Formatted string with memory context
    """
    memories = get_all_memories(agent_id, db)

    sections = []

    # Long-term facts (foundational knowledge)
    longterm = memories.get("longterm", [])[:max_longterm]
    if longterm:
        facts = "\n".join(f"  - {format_memory(m)}" for m in longterm)
        sections.append(f"THINGS I KNOW:\n{facts}")

    # Recent summaries (what happened recently)
    recent = memories.get("recent", [])[:max_recent]
    if recent:
        summaries = "\n".join(
            f"  Day {i + 1}: {format_memory(m)}" for i, m in enumerate(reversed(recent))
        )
        sections.append(f"RECENT DAYS:\n{summaries}")

    # Working memories (immediate context)
    working = memories.get("working", [])[:max_working]
    if working:
        # Show in chronological order (oldest first)
        events = "\n".join(f"  - {format_memory(m)}" for m in reversed(working))
        sections.append(f"JUST NOW:\n{events}")

    if not sections:
        return "No memories yet."

    return "\n\n".join(sections)


def get_memory_summary(agent_id: str, db) -> dict:
    """Get a summary of memory counts by type.

    Returns:
        Dict with counts for each memory type
    """
    memories = get_all_memories(agent_id, db)

    return {
        "working_count": len(memories.get("working", [])),
        "recent_count": len(memories.get("recent", [])),
        "longterm_count": len(memories.get("longterm", [])),
        "total_count": sum(len(v) for v in memories.values()),
    }


def get_relevant_memories(
    agent_id: str,
    db,
    keywords: list[str],
    limit: int = 5,
) -> list[Memory]:
    """Search memories for relevant content.

    Simple keyword matching - could be enhanced with embeddings.

    Args:
        agent_id: The agent's ID
        db: Database session
        keywords: Keywords to search for
        limit: Max memories to return

    Returns:
        List of relevant memories
    """
    memories = get_all_memories(agent_id, db)
    all_memories = (
        memories.get("working", []) + memories.get("recent", []) + memories.get("longterm", [])
    )

    # Score by keyword matches
    scored = []
    for memory in all_memories:
        content_lower = memory.content.lower()
        score = sum(1 for kw in keywords if kw.lower() in content_lower)
        if score > 0:
            scored.append((score, memory))

    # Sort by score and return top matches
    scored.sort(key=lambda x: (-x[0], -x[1].significance))
    return [m for _, m in scored[:limit]]
