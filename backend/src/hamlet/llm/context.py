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

    # Get emergent narrative context
    narrative_context = get_narrative_context(agent, world)

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
{narrative_context}"""
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


def get_trait_voice_hints(agent: Agent) -> str:
    """Generate speaking style hints based on personality traits."""
    traits = agent.traits_dict
    hints = []

    # Discretion affects how freely they share
    discretion = traits.get("discretion", 5)
    if discretion <= 3:
        hints.append("You tend to blurt things out and overshare")
    elif discretion >= 8:
        hints.append("You speak carefully, revealing little")

    # Charm affects how they come across
    charm = traits.get("charm", 5)
    if charm >= 8:
        hints.append("You're naturally charming and put people at ease")
    elif charm <= 3:
        hints.append("You're blunt and sometimes awkward socially")

    # Energy affects verbosity
    energy = traits.get("energy", 5)
    if energy >= 8:
        hints.append("You speak quickly and with enthusiasm")
    elif energy <= 3:
        hints.append("You speak slowly, with economy of words")

    # Empathy affects attentiveness
    empathy = traits.get("empathy", 5)
    if empathy >= 8:
        hints.append("You notice how others feel and respond to it")

    # Curiosity affects questions
    curiosity = traits.get("curiosity", 5)
    if curiosity >= 8:
        hints.append("You ask questions and want to know more")

    return "; ".join(hints) if hints else "You speak in a straightforward manner"


def get_wit_hints(agent: Agent) -> str | None:
    """Generate wit/humor hints for agents with high charm or curiosity.

    High charm agents make clever, witty observations and playful remarks.
    High curiosity agents make insightful observations and clever connections.
    Agents with both traits are particularly sharp and entertaining.

    Args:
        agent: The agent to generate wit hints for

    Returns:
        A string of wit hints if the agent has high charm or curiosity,
        None otherwise
    """
    traits = agent.traits_dict
    charm = traits.get("charm", 5)
    curiosity = traits.get("curiosity", 5)

    wit_hints = []

    # High charm (>=7) - clever, playful wit
    if charm >= 7:
        if charm >= 9:
            wit_hints.append(
                "You have a gift for witty banter - your remarks are clever, "
                "well-timed, and make people smile"
            )
        else:
            wit_hints.append(
                "You enjoy making clever observations and playful remarks "
                "that lighten the mood"
            )

    # High curiosity (>=7) - insightful, observational humor
    if curiosity >= 7:
        if curiosity >= 9:
            wit_hints.append(
                "You notice things others miss and can't help making clever "
                "connections - your insights often have a humorous edge"
            )
        else:
            wit_hints.append(
                "Your curiosity leads you to make interesting observations "
                "that sometimes come out as wry comments"
            )

    # Combined high charm AND curiosity - extra sharp
    if charm >= 7 and curiosity >= 7:
        wit_hints.append(
            "Your quick mind and social grace combine into particularly sharp wit"
        )

    if not wit_hints:
        return None

    return "; ".join(wit_hints)


def get_shared_memory_hint(agent: Agent, target: Agent, world: World) -> str | None:
    """Generate a hint about shared memories between agent and target.

    Queries the agent's memories for ones mentioning the target,
    prioritizing high-significance memories.

    Args:
        agent: The agent whose memories to query
        target: The target agent to find shared memories with
        world: The world containing the database

    Returns:
        A hint string if significant shared memories exist, None otherwise
    """
    db = world.db

    # Query agent's memories, ordered by significance then recency
    memories = (
        db.query(Memory)
        .filter(Memory.agent_id == agent.id)
        .order_by(Memory.significance.desc(), Memory.timestamp.desc())
        .limit(50)  # Check a reasonable number of memories
        .all()
    )

    # Filter for memories mentioning the target's name
    target_name = target.name
    shared_memories = []
    for memory in memories:
        if target_name.lower() in memory.content.lower():
            shared_memories.append(memory)
            if len(shared_memories) >= 2:  # Limit to 2 shared memories
                break

    if not shared_memories:
        return None

    # Build hints from the shared memories
    hints = []
    for memory in shared_memories:
        # Only include memories with significance >= 5 for hints
        if memory.significance >= 5:
            hints.append(f"You could reference: {memory.content}")

    if not hints:
        return None

    return "\n".join(hints)


def get_relationship_subtext(agent: Agent, target: Agent, rel: Relationship | None, world: World) -> str:
    """Generate relationship-aware subtext hints."""
    if not rel:
        return f"You don't know {target.name} well yet."

    subtext_parts = []

    # Basic relationship level
    if rel.score >= 7:
        subtext_parts.append(f"You're very fond of {target.name}")
    elif rel.score >= 4:
        subtext_parts.append(f"You like {target.name}")
    elif rel.score >= 0:
        subtext_parts.append(f"You're neutral about {target.name}")
    elif rel.score >= -4:
        subtext_parts.append(f"You're wary of {target.name}")
    else:
        subtext_parts.append(f"You dislike {target.name}")

    # Add history color if available
    if rel.history:
        import json
        try:
            history = json.loads(rel.history) if isinstance(rel.history, str) else rel.history
            if history:
                subtext_parts.append(f"History: {history[0]}")
        except (json.JSONDecodeError, TypeError):
            pass

    # Check for romantic subtext in personality prompts
    agent_prompt = (agent.personality_prompt or "").lower()
    target_name_lower = target.name.lower().split()[0]  # First name
    if f"crush on {target_name_lower}" in agent_prompt or f"love with {target_name_lower}" in agent_prompt or f"loves {target_name_lower}" in agent_prompt:
        subtext_parts.append(f"SECRET: You have romantic feelings for {target.name} (this affects how you act around them - nervous, trying to impress, etc.)")

    return ". ".join(subtext_parts)


def get_running_joke_hints(agent: Agent, target: Agent, world: World) -> str | None:
    """Generate running joke hints based on shared memorable experiences.

    Looks for funny, embarrassing, or highly memorable shared moments
    that could be referenced as inside jokes between agents.

    Args:
        agent: The agent generating dialogue
        target: The agent being spoken to
        world: The world containing the database

    Returns:
        Hints about inside jokes to reference, or None if no joke material exists
    """
    db = world.db

    # Keywords that suggest funny or memorable moments
    funny_keywords = [
        "funny", "hilarious", "laugh", "absurd", "ridiculous",
        "embarrass", "awkward", "strange", "weird", "unusual",
        "failed", "disaster", "mishap", "accident", "fell",
        "tripped", "spilled", "broke", "forgot", "lost",
        "confused", "mix-up",
    ]

    # Query agent's memories, ordered by significance then recency
    memories = (
        db.query(Memory)
        .filter(Memory.agent_id == agent.id)
        .order_by(Memory.significance.desc(), Memory.timestamp.desc())
        .limit(100)  # Check a larger set for joke material
        .all()
    )

    # Filter for memories mentioning the target that are joke-worthy
    target_name = target.name
    running_jokes = []

    for memory in memories:
        content_lower = memory.content.lower()

        # Must mention the target
        if target_name.lower() not in content_lower:
            continue

        # Check if this memory has joke potential
        is_joke_material = False
        joke_type = None

        # Check for funny keywords
        for keyword in funny_keywords:
            if keyword in content_lower:
                is_joke_material = True
                joke_type = "funny_memory"
                break

        # High significance memories are memorable enough to reference
        if memory.significance >= 8 and not is_joke_material:
            is_joke_material = True
            joke_type = "memorable_event"

        if is_joke_material:
            running_jokes.append({
                "content": memory.content,
                "type": joke_type,
                "significance": memory.significance,
            })
            if len(running_jokes) >= 2:  # Limit to 2 running jokes
                break

    if not running_jokes:
        return None

    # Build hints for inside jokes
    hints = []
    for joke in running_jokes:
        if joke["type"] == "funny_memory":
            hints.append(
                f"INSIDE JOKE: You might tease {target.name} about: {joke['content']} "
                "(reference it playfully or with a knowing look)"
            )
        else:
            hints.append(
                f"SHARED MOMENT: You both remember: {joke['content']} "
                "(you might reference this with a smile or meaningful glance)"
            )

    return "\n".join(hints)


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

    # Rich relationship context
    relationship_subtext = get_relationship_subtext(agent, target, rel, world)

    # Shared memory hints
    shared_memory_hint = get_shared_memory_hint(agent, target, world)

    # Running joke hints (for agents who are at least acquaintances)
    running_joke_hints = None
    if rel and rel.score >= 0:  # Only for non-negative relationships
        running_joke_hints = get_running_joke_hints(agent, target, world)

    # Voice hints based on personality
    voice_hints = get_trait_voice_hints(agent)

    # Wit hints for high charm/curiosity agents
    wit_hints = get_wit_hints(agent)

    # Mood influence
    mood = agent.mood_dict
    happiness = mood.get("happiness", 5)
    energy_mood = mood.get("energy", 5)
    mood_influence = ""
    if happiness <= 3:
        mood_influence = "You're in a bad mood - it shows in your tone."
    elif happiness >= 8:
        mood_influence = "You're in great spirits - more talkative and warm."
    if energy_mood <= 3:
        mood_influence += " You're tired - keep it brief."

    # Build shared history section
    shared_history_section = ""
    if shared_memory_hint:
        shared_history_section = f"""
SHARED HISTORY (you may naturally reference past interactions):
{shared_memory_hint}
"""

    # Build running jokes section
    running_jokes_section = ""
    if running_joke_hints:
        running_jokes_section = f"""
RUNNING JOKES (inside jokes you share with {target.name}):
{running_joke_hints}
"""

    # Build wit section for high charm/curiosity agents
    wit_section = ""
    if wit_hints:
        wit_section = f"""
YOUR WIT: {wit_hints}
"""

    prompt = f"""{agent_context}

SPEAKING TO: {target.name}
{relationship_subtext}
{shared_history_section}{running_jokes_section}
YOUR VOICE: {voice_hints}
{wit_section}{mood_influence}

SITUATION: {context_type}

Generate dialogue that sounds like a real villager, not a video game NPC. Be specific, be yourself, and don't be afraid to be funny, awkward, or indirect. If you have shared history with this person, you might occasionally reference past interactions naturally (e.g., "Remember when..." or "Like that time we...").

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


def get_narrative_context(agent: Agent, world: World) -> str:
    """Get emergent narrative context for an agent.

    This includes:
    - Active narrative arcs the agent is part of
    - Faction memberships and their goals
    - Significant life events (marriage, rivalries, mentorship)
    - Long-term ambitions and plans

    Args:
        agent: The agent to get context for
        world: The world containing the database

    Returns:
        A formatted string of narrative context, or empty string if none
    """
    context_parts = []

    # Get faction context
    faction_ctx = get_faction_context(agent, world)
    if faction_ctx:
        context_parts.append(faction_ctx)

    # Get life events context
    life_event_ctx = get_life_event_context(agent, world)
    if life_event_ctx:
        context_parts.append(life_event_ctx)

    # Get narrative arc context
    arc_ctx = get_arc_context(agent, world)
    if arc_ctx:
        context_parts.append(arc_ctx)

    # Get long-term plan context
    plan_ctx = get_plan_context(agent, world)
    if plan_ctx:
        context_parts.append(plan_ctx)

    if not context_parts:
        return ""

    return "\n\n" + "\n\n".join(context_parts)


def get_faction_context(agent: Agent, world: World) -> str | None:
    """Get faction membership context for an agent."""
    from hamlet.db.models import Faction, FactionMembership

    db = world.db

    memberships = (
        db.query(FactionMembership)
        .filter(
            FactionMembership.agent_id == agent.id,
            FactionMembership.left_at.is_(None),
        )
        .all()
    )

    if not memberships:
        return None

    lines = ["YOUR FACTIONS:"]
    for membership in memberships:
        faction = db.query(Faction).filter(Faction.id == membership.faction_id).first()
        if faction:
            goals_str = ", ".join(faction.goals_list[:2]) if faction.goals_list else "none specified"
            lines.append(
                f"  - {faction.name} ({membership.role}): {faction.description or 'A local group'}. "
                f"Goals: {goals_str}. Loyalty: {membership.loyalty}%"
            )

    return "\n".join(lines) if len(lines) > 1 else None


def get_life_event_context(agent: Agent, world: World) -> str | None:
    """Get active life events context for an agent."""
    from hamlet.db.models import LifeEvent
    from hamlet.life_events.types import LifeEventStatus, LifeEventType

    db = world.db

    events = (
        db.query(LifeEvent)
        .filter(
            LifeEvent.status == LifeEventStatus.ACTIVE.value,
            (LifeEvent.primary_agent_id == agent.id)
            | (LifeEvent.secondary_agent_id == agent.id),
        )
        .all()
    )

    if not events:
        return None

    lines = ["YOUR LIFE SITUATIONS:"]
    for event in events:
        other_agent = None
        if event.primary_agent_id == agent.id and event.secondary_agent_id:
            other = db.query(Agent).filter(Agent.id == event.secondary_agent_id).first()
            other_agent = other.name if other else event.secondary_agent_id
        elif event.secondary_agent_id == agent.id:
            other = db.query(Agent).filter(Agent.id == event.primary_agent_id).first()
            other_agent = other.name if other else event.primary_agent_id

        event_type = event.type
        if event_type == LifeEventType.MARRIAGE.value and other_agent:
            lines.append(f"  - You are married to {other_agent}")
        elif event_type == LifeEventType.MENTORSHIP.value:
            if event.primary_agent_id == agent.id:
                lines.append(f"  - You are mentoring {other_agent}")
            else:
                lines.append(f"  - You are being mentored by {other_agent}")
        elif event_type == LifeEventType.RIVALRY.value and other_agent:
            lines.append(f"  - You have an ongoing rivalry with {other_agent} (you're competing)")
        elif event_type == LifeEventType.FEUD.value and other_agent:
            lines.append(f"  - You are in a bitter feud with {other_agent} (deep animosity)")
        elif event_type == LifeEventType.FRIENDSHIP.value and other_agent:
            lines.append(f"  - You have a deep friendship with {other_agent}")
        else:
            lines.append(f"  - {event.description}")

    return "\n".join(lines) if len(lines) > 1 else None


def get_arc_context(agent: Agent, world: World) -> str | None:
    """Get narrative arc context for an agent."""
    from hamlet.db.models import NarrativeArc
    from hamlet.narrative_arcs.types import ACT_NAMES, ArcStatus, ArcType

    db = world.db

    arcs = (
        db.query(NarrativeArc)
        .filter(
            NarrativeArc.status.notin_([ArcStatus.RESOLUTION.value, ArcStatus.ABANDONED.value]),
            (NarrativeArc.primary_agent_id == agent.id)
            | (NarrativeArc.secondary_agent_id == agent.id),
        )
        .order_by(NarrativeArc.significance.desc())
        .limit(3)
        .all()
    )

    if not arcs:
        return None

    lines = ["YOUR ONGOING STORIES (you're part of these narratives):"]
    for arc in arcs:
        act_name = ACT_NAMES.get(arc.current_act, "unfolding")

        # Determine role
        if arc.primary_agent_id == agent.id:
            role = "protagonist"
        else:
            role = "co-protagonist"

        # Get other agent name if exists
        other_name = None
        if arc.secondary_agent_id and arc.secondary_agent_id != agent.id:
            other = db.query(Agent).filter(Agent.id == arc.secondary_agent_id).first()
            other_name = other.name if other else None
        elif arc.primary_agent_id != agent.id:
            other = db.query(Agent).filter(Agent.id == arc.primary_agent_id).first()
            other_name = other.name if other else None

        arc_desc = f"  - {arc.title or arc.type} ({role}): Currently in '{act_name}' phase."
        if arc.theme:
            arc_desc += f" Theme: {arc.theme}"
        if other_name:
            arc_desc += f" With: {other_name}"

        lines.append(arc_desc)

        # Add dramatic hints based on arc phase
        if arc.status == ArcStatus.CLIMAX.value:
            lines.append("    [This is a critical moment - your choices now matter greatly!]")
        elif arc.status == ArcStatus.RISING_ACTION.value:
            lines.append("    [Tensions are building - events are leading toward something significant]")

    return "\n".join(lines) if len(lines) > 1 else None


def get_plan_context(agent: Agent, world: World) -> str | None:
    """Get long-term plan/ambition context for an agent."""
    from hamlet.db.models import GoalPlan
    from hamlet.goals.types import PlanStatus

    db = world.db

    plan = (
        db.query(GoalPlan)
        .filter(
            GoalPlan.agent_id == agent.id,
            GoalPlan.status.in_([PlanStatus.ACTIVE.value, PlanStatus.PLANNING.value]),
        )
        .first()
    )

    if not plan:
        return None

    milestones = plan.milestones_list
    current_milestone = None
    for m in milestones:
        if m.get("status") == "pending":
            current_milestone = m
            break

    lines = ["YOUR LONG-TERM AMBITION:"]
    lines.append(f"  Goal: {plan.description}")
    lines.append(f"  Progress: {plan.progress:.0f}%")

    if current_milestone:
        lines.append(f"  Current focus: {current_milestone.get('description', 'Continue working')}")

    return "\n".join(lines)
