"""Test script for LLM integration."""

import logging

from hamlet.llm import (
    MockLLMClient,
    build_agent_context,
    decide_action,
    get_available_actions,
    parse_action_response,
    set_llm_client,
)
from hamlet.simulation.world import World

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def test_context_building():
    """Test that we can build context for an agent."""
    logger.info("=" * 50)
    logger.info("Testing context building...")

    world = World()
    agent = world.get_agent("agnes")

    context = build_agent_context(agent, world)
    token_estimate = len(context.split())

    logger.info(f"Context built: ~{token_estimate} tokens")
    logger.info("-" * 30)
    logger.info(context[:500] + "..." if len(context) > 500 else context)
    logger.info("-" * 30)

    world.close()
    return token_estimate


def test_available_actions():
    """Test getting available actions for an agent."""
    logger.info("=" * 50)
    logger.info("Testing available actions...")

    world = World()
    agent = world.get_agent("agnes")

    actions = get_available_actions(agent.id, world)

    logger.info(f"Available actions for {agent.name}: {len(actions)}")
    for action in actions[:10]:
        logger.info(f"  - {action}")
    if len(actions) > 10:
        logger.info(f"  ... and {len(actions) - 10} more")

    world.close()
    return actions


def test_action_parsing():
    """Test parsing LLM responses into actions."""
    logger.info("=" * 50)
    logger.info("Testing action parsing...")

    test_cases = [
        ("ACTION: wait", "wait"),
        ("ACTION: move town_square", "move"),
        ("ACTION: greet Bob", "greet"),
        ("ACTION: talk Martha about the weather", "talk"),
        ("ACTION: examine fountain", "examine"),
        ("I think I'll wait.\nACTION: wait", "wait"),
        ("ACTION: help Bob with gardening", "help"),
    ]

    all_passed = True
    for response, expected_type in test_cases:
        action = parse_action_response(response, "agnes")
        if action:
            result = "PASS" if action.type.value == expected_type else "FAIL"
            logger.info(f"  {result}: '{response[:30]}...' -> {action.type.value}")
            if action.type.value != expected_type:
                all_passed = False
        else:
            logger.info(f"  FAIL: '{response[:30]}...' -> None")
            all_passed = False

    return all_passed


def test_mock_llm_decision():
    """Test decision making with mock LLM."""
    logger.info("=" * 50)
    logger.info("Testing mock LLM decision...")

    # Set up mock client
    mock_client = MockLLMClient(responses=["ACTION: move town_square"])
    set_llm_client(mock_client)

    world = World()
    agent = world.get_agent("agnes")

    action = decide_action(agent, world)

    logger.info(f"Decision for {agent.name}: {action}")
    logger.info(f"Prompt length: {len(mock_client.last_prompt)} chars")

    world.close()

    # Reset to None so future tests don't use mock
    set_llm_client(None)

    return action


def test_real_llm_decision():
    """Test decision making with real LLM (requires API key)."""
    logger.info("=" * 50)
    logger.info("Testing real LLM decision...")

    from hamlet.config import settings

    if not settings.anthropic_api_key:
        logger.info("  Skipped: No API key configured")
        return None

    world = World()
    agent = world.get_agent("agnes")

    try:
        action = decide_action(agent, world)
        logger.info(f"Decision for {agent.name}: {action}")
    except Exception as e:
        logger.info(f"  Error: {e}")
        action = None

    world.close()
    return action


def main():
    """Run all integration tests."""
    logger.info("\n" + "=" * 50)
    logger.info("LLM INTEGRATION TESTS")
    logger.info("=" * 50 + "\n")

    # Run tests
    token_count = test_context_building()
    actions = test_available_actions()
    parsing_ok = test_action_parsing()
    mock_action = test_mock_llm_decision()
    real_action = test_real_llm_decision()

    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Context built: ~{token_count} tokens")
    logger.info(f"Available actions: {len(actions)}")
    logger.info(f"Action parsing: {'PASS' if parsing_ok else 'FAIL'}")
    logger.info(f"Mock decision: {mock_action}")
    logger.info(f"Real decision: {real_action or 'Skipped (no API key)'}")


if __name__ == "__main__":
    main()
