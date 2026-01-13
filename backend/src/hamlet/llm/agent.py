"""LLM-powered agent decision making."""

import logging

from hamlet.actions import Action, Wait, execute_action
from hamlet.db import Agent
from hamlet.llm.client import LLMClient, get_llm_client
from hamlet.llm.context import build_decision_prompt, build_dialogue_prompt
from hamlet.llm.parser import get_available_actions, parse_action_response
from hamlet.simulation.world import World

logger = logging.getLogger(__name__)

# System prompt for agent decision making
DECISION_SYSTEM_PROMPT = """You are an AI playing a character in a village simulation.
Your job is to decide what your character does next based on their personality,
current situation, relationships, and goals.

Always respond with a single action in the exact format requested.
Stay in character and make choices that fit your character's personality."""

DIALOGUE_SYSTEM_PROMPT = """You are an AI playing a character in a village simulation.
Generate natural, in-character dialogue that fits the situation and your character's personality.
Keep responses short and conversational."""


def decide_action(agent: Agent, world: World, client: LLMClient | None = None) -> Action:
    """Use LLM to decide what action an agent should take.

    Args:
        agent: The agent making the decision
        world: The world state
        client: Optional LLM client (uses global if not provided)

    Returns:
        The chosen Action
    """
    client = client or get_llm_client()

    # Get available actions for context
    available_actions = get_available_actions(agent.id, world)

    if not available_actions:
        logger.warning(f"No available actions for {agent.name}")
        return Wait(agent.id)

    # Build the decision prompt
    prompt = build_decision_prompt(agent, world, available_actions)

    # Get LLM response
    response = client.complete(
        prompt=prompt,
        system=DECISION_SYSTEM_PROMPT,
        max_tokens=100,
        temperature=0.7,
    )

    logger.debug(f"LLM response for {agent.name}: {response.content}")

    # Parse into action
    action = parse_action_response(response.content, agent.id)

    if action is None:
        logger.warning(f"Could not parse action, defaulting to wait: {response.content}")
        return Wait(agent.id)

    return action


def generate_dialogue(
    agent: Agent,
    target: Agent,
    world: World,
    context_type: str = "greeting",
    client: LLMClient | None = None,
) -> str:
    """Generate dialogue for an agent.

    Args:
        agent: The agent speaking
        target: The agent being spoken to
        world: The world state
        context_type: Type of dialogue (greeting, conversation, question, etc.)
        client: Optional LLM client

    Returns:
        Generated dialogue string
    """
    client = client or get_llm_client()

    prompt = build_dialogue_prompt(agent, target, world, context_type)

    response = client.complete(
        prompt=prompt,
        system=DIALOGUE_SYSTEM_PROMPT,
        max_tokens=100,
        temperature=0.8,
    )

    # Clean up the response
    dialogue = response.content.strip()
    # Remove any quotes if the model added them
    dialogue = dialogue.strip("\"'")

    return dialogue


def process_agent_turn(agent: Agent, world: World, use_llm: bool = True) -> Action | None:
    """Process a single agent's turn, optionally using LLM.

    Args:
        agent: The agent whose turn it is
        world: The world state
        use_llm: Whether to use LLM for decisions

    Returns:
        The action taken, or None if no action
    """
    if agent.state == "sleeping":
        return None

    if use_llm:
        action = decide_action(agent, world)
    else:
        # Fall back to random action selection
        from hamlet.simulation.engine import SimulationEngine

        engine = SimulationEngine()
        perception = world.get_agent_perception(agent)
        action_dict = engine._choose_random_action(agent, perception)
        if action_dict is None:
            return None
        # Convert dict to Action - simplified for now
        action = Wait(agent.id)

    # Execute the action
    result = execute_action(action, world)

    if result.success:
        logger.info(f"  {agent.name}: {result.message}")
    else:
        logger.debug(f"  {agent.name} action failed: {result.message}")

    return action if result.success else None
