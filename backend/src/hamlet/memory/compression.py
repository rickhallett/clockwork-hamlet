"""Memory compression using LLM summarization."""

import logging
import time

from sqlalchemy.orm import Session

from hamlet.db import Agent, Memory
from hamlet.memory.manager import MemoryManager, get_working_memories
from hamlet.memory.types import (
    SIGNIFICANCE_THRESHOLD_FOR_LONGTERM,
    SIGNIFICANCE_THRESHOLD_FOR_SUMMARY,
)

logger = logging.getLogger(__name__)

# Prompts for LLM compression
SUMMARY_SYSTEM_PROMPT = """You are a memory compression assistant.
Summarize the given memories into a concise daily summary from the character's perspective.
Keep the most important events and emotions. Be brief but capture the essence."""

FACTS_SYSTEM_PROMPT = """You are a memory analyst.
Extract important facts from memories that should be remembered long-term.
Return only factual statements, one per line. Focus on:
- New information learned about people
- Relationship changes
- Discoveries or secrets
- Important events that happened"""


def compress_memories(
    memories: list[Memory],
    llm_client=None,
) -> tuple[str, list[str]]:
    """Compress a list of memories into summary and facts.

    Args:
        memories: List of memories to compress
        llm_client: Optional LLM client (uses mock if not provided)

    Returns:
        Tuple of (daily_summary, list_of_facts)
    """
    if not memories:
        return "", []

    # Sort by timestamp
    sorted_memories = sorted(memories, key=lambda m: m.timestamp)

    # Filter by significance for summary
    significant = [
        m for m in sorted_memories if m.significance >= SIGNIFICANCE_THRESHOLD_FOR_SUMMARY
    ]

    if not significant:
        significant = sorted_memories[-5:]  # Use last 5 if none meet threshold

    # Build memory text
    memory_text = "\n".join(f"- {m.content} (significance: {m.significance})" for m in significant)

    # Generate summary
    if llm_client:
        summary = _generate_summary_with_llm(memory_text, llm_client)
        facts = _extract_facts_with_llm(memory_text, llm_client)
    else:
        # Mock compression for testing
        summary = _mock_summarize(significant)
        facts = _mock_extract_facts(sorted_memories)

    return summary, facts


def _generate_summary_with_llm(memory_text: str, llm_client) -> str:
    """Generate a summary using the LLM."""
    prompt = f"""Summarize these memories into a brief daily summary (2-3 sentences):

{memory_text}

Daily summary:"""

    response = llm_client.complete(
        prompt=prompt,
        system=SUMMARY_SYSTEM_PROMPT,
        max_tokens=150,
        temperature=0.7,
    )
    return response.content.strip()


def _extract_facts_with_llm(memory_text: str, llm_client) -> list[str]:
    """Extract long-term facts using the LLM."""
    prompt = f"""Extract important facts from these memories (one per line):

{memory_text}

Facts:"""

    response = llm_client.complete(
        prompt=prompt,
        system=FACTS_SYSTEM_PROMPT,
        max_tokens=200,
        temperature=0.5,
    )

    # Parse facts from response
    facts = []
    for line in response.content.strip().split("\n"):
        line = line.strip()
        if line and not line.startswith("#"):
            # Remove leading bullets or numbers
            line = line.lstrip("-•*0123456789. ")
            if line:
                facts.append(line)

    return facts


def _mock_summarize(memories: list[Memory]) -> str:
    """Mock summarization for testing without LLM."""
    if not memories:
        return "Nothing notable happened."

    # Create simple summary from highest significance memories
    top = sorted(memories, key=lambda m: m.significance, reverse=True)[:3]
    events = [m.content for m in top]

    if len(events) == 1:
        return f"Today: {events[0]}"
    elif len(events) == 2:
        return f"Today: {events[0]}. Also, {events[1].lower()}"
    else:
        return f"Today: {events[0]}. {events[1]}. {events[2]}"


def _mock_extract_facts(memories: list[Memory]) -> list[str]:
    """Mock fact extraction for testing without LLM."""
    facts = []

    for memory in memories:
        if memory.significance >= SIGNIFICANCE_THRESHOLD_FOR_LONGTERM:
            # Simple fact extraction - just keep high significance content
            facts.append(memory.content)

    return facts[:5]  # Limit to 5 facts


def end_of_day_compression(
    agent: Agent,
    db: Session,
    llm_client=None,
) -> dict:
    """Perform end-of-day memory compression for an agent.

    1. Get all working memories
    2. Generate daily summary
    3. Extract long-term facts
    4. Store summary as recent memory
    5. Store facts as long-term memories
    6. Clear working memories

    Args:
        agent: The agent whose memories to compress
        db: Database session
        llm_client: Optional LLM client

    Returns:
        Dict with compression results
    """
    manager = MemoryManager(db)

    # Get working memories
    working = get_working_memories(agent.id, db, limit=50)

    if not working:
        logger.info(f"No working memories to compress for {agent.name}")
        return {"summary": None, "facts": [], "working_count": 0}

    logger.info(f"Compressing {len(working)} working memories for {agent.name}")

    # Compress
    summary, facts = compress_memories(working, llm_client)

    # Store summary as recent memory
    if summary:
        day_timestamp = int(time.time())
        manager.add_daily_summary(agent, summary, day_timestamp)
        logger.info(f"Created daily summary for {agent.name}: {summary[:50]}...")

    # Store facts as long-term memories
    for fact in facts:
        manager.add_longterm_fact(agent, fact, significance=7)
        logger.debug(f"Added long-term fact for {agent.name}: {fact}")

    # Clear working memories
    cleared = manager.clear_working_memories(agent)
    logger.info(f"Cleared {cleared} working memories for {agent.name}")

    return {
        "summary": summary,
        "facts": facts,
        "working_count": len(working),
        "cleared_count": cleared,
    }
