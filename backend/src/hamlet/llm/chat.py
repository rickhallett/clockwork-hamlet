"""LLM integration for agent chat with users."""

import logging
import time
from typing import TYPE_CHECKING

from hamlet.db import Agent, ChatConversation, ChatMessage, Memory
from hamlet.llm.client import LLMClient, LLMResponse, get_llm_client
from hamlet.llm.context import (
    format_goals,
    format_memories,
    format_mood,
    format_needs,
    format_relationships,
    format_traits,
    get_trait_voice_hints,
    get_wit_hints,
)
from hamlet.llm.usage import get_usage_tracker
from hamlet.simulation.world import World

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# System prompt for chat with users
CHAT_SYSTEM_PROMPT = """You are an AI playing a character in a village simulation. You are having a conversation with a visitor (the user). Stay fully in character at all times.

CRITICAL RULES:
1. You ARE this character - speak in first person, never break character
2. You know nothing about being an AI, simulation, or the real world
3. Respond naturally as a villager would to a stranger or acquaintance
4. Keep responses conversational and relatively brief (1-3 paragraphs max)
5. Show personality through your speech patterns, word choice, and reactions
6. Reference your current situation, mood, and recent experiences when relevant
7. If asked about things outside your knowledge (internet, computers, etc), respond with confusion or curiosity as a medieval villager would
8. Your responses should feel like natural dialogue, not exposition"""


def build_chat_context(
    agent: Agent,
    world: World | None,
    db: "Session",
    recent_messages: list[ChatMessage] | None = None,
) -> str:
    """Build the context for a chat response.

    Args:
        agent: The agent responding to the chat
        world: The world object (optional, for full context)
        db: Database session
        recent_messages: Recent messages in this conversation for context

    Returns:
        A context string for the LLM prompt
    """
    traits = format_traits(agent)
    mood = format_mood(agent)
    needs = format_needs(agent)
    voice_hints = get_trait_voice_hints(agent)
    wit_hints = get_wit_hints(agent)

    # Get location info
    location_name = "the village"
    if agent.location:
        location_name = agent.location.name

    # Get relationships (limited, for context)
    relationship_context = ""
    if world:
        relationship_context = format_relationships(agent, world, limit=5)
    else:
        relationship_context = "You have various relationships with other villagers."

    # Get recent memories
    memory_context = ""
    if world:
        memory_context = format_memories(agent, world, limit=5)
    else:
        # Query memories directly
        memories = (
            db.query(Memory)
            .filter(Memory.agent_id == agent.id)
            .order_by(Memory.timestamp.desc())
            .limit(5)
            .all()
        )
        if memories:
            lines = []
            for memory in reversed(memories):
                significance = "!" * min(memory.significance // 3, 3)
                lines.append(f"  {significance} {memory.content}")
            memory_context = "\n".join(lines)
        else:
            memory_context = "  No recent memories"

    # Get goals
    goal_context = ""
    if world:
        goal_context = format_goals(agent, world, limit=3)
    else:
        goal_context = "  You have various personal goals"

    # Build conversation history context
    conversation_context = ""
    if recent_messages:
        conv_lines = []
        for msg in recent_messages[-10:]:  # Last 10 messages
            speaker = "Visitor" if msg.role == "user" else agent.name
            conv_lines.append(f"{speaker}: {msg.content}")
        if conv_lines:
            conversation_context = f"""
RECENT CONVERSATION:
{chr(10).join(conv_lines)}
"""

    # Build the wit section if applicable
    wit_section = ""
    if wit_hints:
        wit_section = f"\nYOUR WIT: {wit_hints}"

    context = f"""You are {agent.name}. {agent.personality_prompt or ""}

PERSONALITY TRAITS (1-10 scale):
{traits}

CURRENT STATE:
- Location: {location_name}
- Current mood: {mood}
- Physical state: {agent.state}

NEEDS:
{needs}

RELATIONSHIPS (people you know):
{relationship_context}

RECENT MEMORIES:
{memory_context}

CURRENT GOALS:
{goal_context}

YOUR VOICE: {voice_hints}{wit_section}
{conversation_context}
A visitor has approached you and wants to talk. Respond in character as {agent.name}."""

    return context.strip()


def generate_chat_response(
    agent: Agent,
    user_message: str,
    db: "Session",
    world: World | None = None,
    recent_messages: list[ChatMessage] | None = None,
    client: LLMClient | None = None,
) -> tuple[str, LLMResponse]:
    """Generate an in-character chat response from an agent.

    Args:
        agent: The agent responding
        user_message: The user's message
        db: Database session
        world: Optional world object for full context
        recent_messages: Recent messages for conversation context
        client: Optional LLM client (uses global if not provided)

    Returns:
        Tuple of (response_text, llm_response) for tracking
    """
    if client is None:
        client = get_llm_client()

    # Build context
    context = build_chat_context(agent, world, db, recent_messages)

    # Build the prompt
    prompt = f"""{context}

Visitor says: "{user_message}"

Respond in character as {agent.name}. Keep your response natural and conversational."""

    # Make LLM call
    response = client.complete(
        prompt=prompt,
        system=CHAT_SYSTEM_PROMPT,
        max_tokens=500,
        temperature=0.8,  # Slightly higher for more natural conversation
        use_cache=False,  # Don't cache chat responses
    )

    # Track usage with "chat" call type
    tracker = get_usage_tracker()
    tracker.record_call(
        model=response.model,
        tokens_in=response.tokens_in,
        tokens_out=response.tokens_out,
        latency_ms=response.latency_ms,
        cached=response.cached,
        agent_id=agent.id,
        call_type="chat",
    )

    return response.content.strip(), response


def create_chat_memory(
    agent: Agent,
    user_message: str,
    agent_response: str,
    db: "Session",
) -> Memory | None:
    """Create a memory from a chat interaction.

    Args:
        agent: The agent who had the conversation
        user_message: What the user said
        agent_response: What the agent responded
        db: Database session

    Returns:
        The created memory, or None if not significant enough
    """
    # Create a summary of the interaction
    # For significant or interesting conversations, create a memory
    summary = f"A visitor asked about: {user_message[:50]}..."

    # Simple heuristic: longer or more detailed conversations are more memorable
    significance = 3  # Base significance
    if len(user_message) > 100:
        significance += 1
    if "?" in user_message:  # Questions are more engaging
        significance += 1
    if any(word in user_message.lower() for word in ["love", "hate", "secret", "help", "friend"]):
        significance += 2

    # Only create memory if significant enough
    if significance < 4:
        return None

    memory = Memory(
        agent_id=agent.id,
        timestamp=int(time.time()),
        type="recent",
        content=summary,
        significance=min(significance, 10),
        compressed=False,
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    return memory
