"""Context building for LLM prompts."""

from hamlet.db import Agent, Goal, Memory, Relationship
from hamlet.simulation.world import World


def build_agent_context(agent: Agent, world: World) -> str:
    """Build the full context string for an agent's LLM call."""
    perception = world.get_agent_perception(agent)
    traits = format_traits(agent)
    relationships = format_relationships(agent, world)
    memories = format_memories(agent, world)
    goals = format_goals(agent, world)
    needs = format_needs(agent)

    context = f"""You are {agent.name}. {agent.personality_prompt or ""}

PERSONALITY TRAITS (1-10 scale):
{traits}

CURRENT STATE:
- Location: {perception.location_name}
- Nearby people: {", ".join(perception.nearby_agents) if perception.nearby_agents else "No one"}
- Nearby objects: {", ".join(perception.nearby_objects) if perception.nearby_objects else "Nothing notable"}
- Current mood: {format_mood(agent)}
- Physical state: {agent.state}

NEEDS:
{needs}

RELATIONSHIPS (people you know):
{relationships}

RECENT MEMORIES:
{memories}

CURRENT GOALS:
{goals}
"""
    return context.strip()


def format_traits(agent: Agent) -> str:
    """Format agent traits for display."""
    traits = agent.traits_dict
    if not traits:
        return "No specific traits defined"

    lines = []
    trait_names = [
        "curiosity",
        "empathy",
        "ambition",
        "discretion",
        "energy",
        "courage",
        "charm",
        "perception",
    ]
    for name in trait_names:
        value = traits.get(name, 5)
        bar = "█" * value + "░" * (10 - value)
        lines.append(f"  {name.capitalize():12} {bar} {value}/10")

    return "\n".join(lines)


def format_mood(agent: Agent) -> str:
    """Format agent mood."""
    mood = agent.mood_dict
    happiness = mood.get("happiness", 5)
    energy = mood.get("energy", 5)

    happiness_word = "happy" if happiness >= 7 else "content" if happiness >= 4 else "unhappy"
    energy_word = "energetic" if energy >= 7 else "normal" if energy >= 4 else "tired"

    return f"{happiness_word}, {energy_word}"


def format_needs(agent: Agent) -> str:
    """Format agent needs."""
    lines = []

    # Hunger
    if agent.hunger >= 7:
        lines.append("  - Very hungry (urgent)")
    elif agent.hunger >= 4:
        lines.append("  - Somewhat hungry")
    else:
        lines.append("  - Not hungry")

    # Energy
    if agent.energy <= 3:
        lines.append("  - Very tired (need rest)")
    elif agent.energy <= 5:
        lines.append("  - Somewhat tired")
    else:
        lines.append("  - Well rested")

    # Social
    if agent.social <= 3:
        lines.append("  - Lonely (want company)")
    elif agent.social <= 5:
        lines.append("  - Could use some conversation")
    else:
        lines.append("  - Socially satisfied")

    return "\n".join(lines)


def format_relationships(agent: Agent, world: World, limit: int = 10) -> str:
    """Format agent relationships."""
    db = world.db
    relationships = (
        db.query(Relationship)
        .filter(Relationship.agent_id == agent.id)
        .order_by(Relationship.score.desc())
        .limit(limit)
        .all()
    )

    if not relationships:
        return "  No established relationships yet"

    lines = []
    for rel in relationships:
        target = world.get_agent(rel.target_id)
        if target:
            # Create sentiment indicator
            if rel.score >= 7:
                sentiment = "♥♥♥♥♥"
            elif rel.score >= 4:
                sentiment = "♥♥♥♥○"
            elif rel.score >= 1:
                sentiment = "♥♥♥○○"
            elif rel.score >= -2:
                sentiment = "♥♥○○○"
            elif rel.score >= -5:
                sentiment = "♥○○○○"
            else:
                sentiment = "○○○○○"

            lines.append(f"  {sentiment} {target.name} ({rel.type})")

    return "\n".join(lines) if lines else "  No established relationships yet"


def format_memories(agent: Agent, world: World, limit: int = 10) -> str:
    """Format agent's recent memories."""
    db = world.db
    memories = (
        db.query(Memory)
        .filter(Memory.agent_id == agent.id)
        .order_by(Memory.timestamp.desc())
        .limit(limit)
        .all()
    )

    if not memories:
        return "  No recent memories"

    lines = []
    for memory in reversed(memories):  # Show oldest first
        significance = "!" * min(memory.significance // 3, 3)
        lines.append(f"  {significance} {memory.content}")

    return "\n".join(lines)


def format_goals(agent: Agent, world: World, limit: int = 5) -> str:
    """Format agent's current goals."""
    db = world.db
    goals = (
        db.query(Goal)
        .filter(Goal.agent_id == agent.id, Goal.status == "active")
        .order_by(Goal.priority.desc())
        .limit(limit)
        .all()
    )

    if not goals:
        return "  No specific goals right now"

    lines = []
    for goal in goals:
        priority = "HIGH" if goal.priority >= 7 else "MEDIUM" if goal.priority >= 4 else "LOW"
        lines.append(f"  [{priority}] {goal.description or goal.type}")

    return "\n".join(lines)


def build_decision_prompt(agent: Agent, world: World, available_actions: list[str]) -> str:
    """Build the prompt for agent decision making."""
    context = build_agent_context(agent, world)

    prompt = f"""{context}

AVAILABLE ACTIONS:
{chr(10).join(f"  - {action}" for action in available_actions)}

Based on your personality, current state, relationships, and goals, what do you do next?

INSTRUCTIONS:
- Choose ONE action from the available actions
- Consider your personality traits when deciding
- If you're hungry, consider finding food
- If you're tired, consider resting
- If you're lonely, consider socializing
- Stay in character as {agent.name}

Respond with ONLY the action in this exact format:
ACTION: <action_type> [target]

Examples:
- ACTION: wait
- ACTION: move town_square
- ACTION: greet Bob
- ACTION: talk Martha about the weather
- ACTION: examine fountain
"""
    return prompt


def build_dialogue_prompt(
    agent: Agent,
    target: Agent,
    world: World,
    context_type: str = "greeting",
) -> str:
    """Build the prompt for generating dialogue."""
    agent_context = build_agent_context(agent, world)

    # Get relationship with target
    db = world.db
    rel = (
        db.query(Relationship)
        .filter(Relationship.agent_id == agent.id, Relationship.target_id == target.id)
        .first()
    )

    relationship_desc = "stranger"
    if rel:
        if rel.score >= 7:
            relationship_desc = "close friend (very fond of them)"
        elif rel.score >= 4:
            relationship_desc = "friend (like them)"
        elif rel.score >= 0:
            relationship_desc = "acquaintance (neutral)"
        elif rel.score >= -4:
            relationship_desc = "someone you're wary of"
        else:
            relationship_desc = "someone you dislike"

    prompt = f"""{agent_context}

You are about to speak to {target.name}, who is a {relationship_desc}.

DIALOGUE CONTEXT: {context_type}

Generate a short, natural line of dialogue that:
- Matches your personality
- Reflects your relationship with {target.name}
- Is appropriate for the context
- Sounds natural and conversational
- Is 1-2 sentences maximum

Respond with ONLY the dialogue (no quotes, no name prefix):
"""
    return prompt


def build_reaction_prompt(
    agent: Agent,
    event_description: str,
    world: World,
) -> str:
    """Build the prompt for reacting to an event."""
    agent_context = build_agent_context(agent, world)

    prompt = f"""{agent_context}

SOMETHING JUST HAPPENED:
{event_description}

How do you react to this? Consider:
- Your personality traits
- Your relationships with anyone involved
- Your current goals and state

Describe your reaction in 1-2 sentences from first person perspective:
"""
    return prompt
