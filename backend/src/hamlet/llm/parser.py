"""Parse LLM responses into actions."""

import logging
import re

from hamlet.actions.types import (
    Action,
    Ask,
    Avoid,
    Confront,
    Drop,
    Examine,
    Give,
    Gossip,
    Greet,
    Help,
    Investigate,
    Move,
    Observe,
    Sleep,
    Take,
    Talk,
    Tell,
    Wait,
    Work,
)

logger = logging.getLogger(__name__)


def parse_action_response(response: str, actor_id: str) -> Action | None:
    """Parse an LLM response into an Action.

    Expected format: ACTION: <action_type> [target] [parameters]

    Examples:
    - ACTION: wait
    - ACTION: move town_square
    - ACTION: greet Bob
    - ACTION: talk Martha about the weather
    - ACTION: examine fountain
    - ACTION: give Bob bread_loaf
    """
    # Extract the ACTION line
    match = re.search(r"ACTION:\s*(.+)", response, re.IGNORECASE)
    if not match:
        logger.warning(f"Could not parse action from response: {response[:100]}")
        return None

    action_str = match.group(1).strip().lower()
    parts = action_str.split()

    if not parts:
        return None

    action_type = parts[0]
    args = parts[1:] if len(parts) > 1 else []

    try:
        return _create_action(actor_id, action_type, args)
    except Exception as e:
        logger.warning(f"Error creating action: {e}")
        return None


def _create_action(actor_id: str, action_type: str, args: list[str]) -> Action | None:
    """Create an Action object from parsed components."""
    # Solo actions
    if action_type == "wait":
        return Wait(actor_id)

    if action_type == "sleep":
        return Sleep(actor_id)

    if action_type == "work":
        job_type = args[0] if args else "default"
        return Work(actor_id, job_type)

    if action_type == "move":
        if not args:
            logger.warning("Move action requires destination")
            return None
        destination = args[0]
        return Move(actor_id, destination)

    if action_type == "examine":
        if not args:
            logger.warning("Examine action requires target")
            return None
        target = args[0]
        return Examine(actor_id, target)

    if action_type == "take":
        if not args:
            logger.warning("Take action requires item")
            return None
        item = args[0]
        return Take(actor_id, item)

    if action_type == "drop":
        if not args:
            logger.warning("Drop action requires item")
            return None
        item = args[0]
        return Drop(actor_id, item)

    # Social actions
    if action_type == "greet":
        if not args:
            logger.warning("Greet action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        return Greet(actor_id, target_id)

    if action_type == "talk":
        if not args:
            logger.warning("Talk action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        # Extract topic if present (everything after "about")
        topic = ""
        if "about" in args:
            about_idx = args.index("about")
            topic = " ".join(args[about_idx + 1 :])
        return Talk(actor_id, target_id, topic)

    if action_type == "ask":
        if not args:
            logger.warning("Ask action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        # Extract question (everything after target)
        question = " ".join(args[1:]) if len(args) > 1 else "something"
        return Ask(actor_id, target_id, question)

    if action_type == "tell":
        if not args:
            logger.warning("Tell action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        information = " ".join(args[1:]) if len(args) > 1 else "something"
        return Tell(actor_id, target_id, information)

    if action_type == "give":
        if len(args) < 2:
            logger.warning("Give action requires target and item")
            return None
        target_id = _normalize_agent_id(args[0])
        item = args[1]
        return Give(actor_id, target_id, item)

    if action_type == "help":
        if not args:
            logger.warning("Help action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        task = " ".join(args[1:]) if len(args) > 1 else ""
        return Help(actor_id, target_id, task)

    if action_type == "confront":
        if not args:
            logger.warning("Confront action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        accusation = " ".join(args[1:]) if len(args) > 1 else ""
        return Confront(actor_id, target_id, accusation)

    if action_type == "avoid":
        if not args:
            logger.warning("Avoid action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        return Avoid(actor_id, target_id)

    # Special actions
    if action_type == "gossip":
        if len(args) < 2:
            logger.warning("Gossip action requires target and subject")
            return None
        target_id = _normalize_agent_id(args[0])
        subject_id = _normalize_agent_id(args[1])
        rumor = " ".join(args[2:]) if len(args) > 2 else ""
        return Gossip(actor_id, target_id, subject_id, rumor)

    if action_type == "investigate":
        mystery = " ".join(args) if args else "something"
        return Investigate(actor_id, mystery)

    if action_type == "observe":
        if not args:
            logger.warning("Observe action requires target")
            return None
        target_id = _normalize_agent_id(args[0])
        return Observe(actor_id, target_id)

    logger.warning(f"Unknown action type: {action_type}")
    return None


def _normalize_agent_id(name: str) -> str:
    """Convert agent name to ID format.

    Handles common name formats:
    - "Bob" -> "bob"
    - "Bob Millwright" -> "bob"
    - "Agnes" -> "agnes"
    """
    # Take first word and lowercase
    first_name = name.split()[0].lower()
    return first_name


def get_available_actions(agent_id: str, world) -> list[str]:
    """Get list of available action descriptions for an agent."""

    agent = world.get_agent(agent_id)
    if not agent:
        return []

    actions = []
    perception = world.get_agent_perception(agent)

    # Always available
    actions.append("wait - do nothing and observe")

    # Movement - can move to connected locations
    if agent.location_id:
        location = world.get_location(agent.location_id)
        if location:
            for conn in location.connections_list:
                dest = world.get_location(conn)
                if dest:
                    actions.append(f"move {conn} - go to {dest.name}")

    # Examine nearby objects
    for obj in perception.nearby_objects:
        actions.append(f"examine {obj} - look at the {obj}")

    # Social actions with nearby agents
    for other_name in perception.nearby_agents:
        other_id = _normalize_agent_id(other_name)
        actions.append(f"greet {other_id} - say hello to {other_name}")
        actions.append(f"talk {other_id} about <topic> - have a conversation with {other_name}")
        actions.append(f"ask {other_id} <question> - ask {other_name} something")
        actions.append(f"help {other_id} - offer to help {other_name}")

    # Inventory actions
    inventory = agent.inventory_list
    for item in inventory:
        actions.append(f"drop {item} - drop the {item}")
        for other_name in perception.nearby_agents:
            other_id = _normalize_agent_id(other_name)
            actions.append(f"give {other_id} {item} - give {item} to {other_name}")

    # Take items from location
    if agent.location_id:
        location = world.get_location(agent.location_id)
        if location:
            # Only some objects can be taken
            takeable = [obj for obj in location.objects_list if _is_takeable(obj)]
            for obj in takeable:
                actions.append(f"take {obj} - pick up the {obj}")

    # Special actions based on traits
    traits = agent.traits_dict
    if traits.get("curiosity", 5) >= 6:
        actions.append("investigate <mystery> - look into something suspicious")

    # Sleep if tired
    if agent.energy <= 5:
        actions.append("sleep - take a rest")

    return actions


def _is_takeable(obj: str) -> bool:
    """Check if an object can be taken."""
    # Large/fixed objects cannot be taken
    non_takeable = {
        "fountain",
        "bench",
        "notice_board",
        "counter",
        "oven",
        "bar",
        "fireplace",
        "dartboard",
        "tables",
    }
    return obj.lower() not in non_takeable
