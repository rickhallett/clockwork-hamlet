"""LLM integration module."""

from hamlet.llm.agent import decide_action, generate_dialogue, process_agent_turn
from hamlet.llm.client import (
    LLMClient,
    LLMResponse,
    MockLLMClient,
    ResponseCache,
    get_llm_client,
    set_llm_client,
)
from hamlet.llm.context import (
    build_agent_context,
    build_decision_prompt,
    build_dialogue_prompt,
    build_reaction_prompt,
)
from hamlet.llm.parser import get_available_actions, parse_action_response

__all__ = [
    # Agent
    "decide_action",
    "generate_dialogue",
    "process_agent_turn",
    # Client
    "LLMClient",
    "LLMResponse",
    "MockLLMClient",
    "ResponseCache",
    "get_llm_client",
    "set_llm_client",
    # Context
    "build_agent_context",
    "build_decision_prompt",
    "build_dialogue_prompt",
    "build_reaction_prompt",
    # Parser
    "get_available_actions",
    "parse_action_response",
]
