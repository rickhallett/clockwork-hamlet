"""Action validation logic."""

from dataclasses import dataclass

from hamlet.actions.types import Action, ActionType
from hamlet.db import Agent
from hamlet.simulation.world import World


@dataclass
class ValidationResult:
    """Result of action validation."""

    valid: bool
    reason: str | None = None


def validate_action(action: Action, world: World) -> ValidationResult:
    """Validate if an action can be performed."""
    actor = world.get_agent(action.actor_id)
    if not actor:
        return ValidationResult(False, f"Actor {action.actor_id} not found")

    # Check actor state
    if actor.state == "sleeping" and action.type != ActionType.WAIT:
        return ValidationResult(False, "Agent is sleeping")

    # Dispatch to specific validators
    validators = {
        ActionType.MOVE: validate_move,
        ActionType.EXAMINE: validate_examine,
        ActionType.TAKE: validate_take,
        ActionType.DROP: validate_drop,
        ActionType.WAIT: validate_wait,
        ActionType.SLEEP: validate_sleep,
        ActionType.WORK: validate_work,
        ActionType.GREET: validate_social,
        ActionType.TALK: validate_social,
        ActionType.ASK: validate_social,
        ActionType.TELL: validate_social,
        ActionType.GIVE: validate_give,
        ActionType.HELP: validate_social,
        ActionType.CONFRONT: validate_social,
        ActionType.AVOID: validate_avoid,
        ActionType.GOSSIP: validate_gossip,
        ActionType.INVESTIGATE: validate_investigate,
        ActionType.OBSERVE: validate_observe,
    }

    validator = validators.get(action.type)
    if validator:
        return validator(action, actor, world)

    return ValidationResult(True)


def validate_move(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a move action."""
    if not action.target_id:
        return ValidationResult(False, "No destination specified")

    # Check destination exists
    destination = world.get_location(action.target_id)
    if not destination:
        return ValidationResult(False, f"Location {action.target_id} not found")

    # Check destination is connected to current location
    if actor.location_id:
        current = world.get_location(actor.location_id)
        if current and action.target_id not in current.connections_list:
            return ValidationResult(False, f"Cannot reach {destination.name} from here")

    # Check destination capacity
    agents_there = world.get_agents_at_location(action.target_id)
    if len(agents_there) >= destination.capacity:
        return ValidationResult(False, f"{destination.name} is full")

    return ValidationResult(True)


def validate_examine(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate an examine action."""
    if not action.target_object and not action.target_id:
        return ValidationResult(False, "No target to examine")

    # If examining an object, check it's in the current location
    if action.target_object and actor.location_id:
        location = world.get_location(actor.location_id)
        if location and action.target_object not in location.objects_list:
            # Check if it's in actor's inventory
            if action.target_object not in actor.inventory_list:
                return ValidationResult(False, f"{action.target_object} not found here")

    return ValidationResult(True)


def validate_take(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a take action."""
    if not action.target_object:
        return ValidationResult(False, "No item to take")

    # Check item is in current location
    if actor.location_id:
        location = world.get_location(actor.location_id)
        if location and action.target_object not in location.objects_list:
            return ValidationResult(False, f"{action.target_object} not found here")

    # Check inventory isn't full (max 10 items)
    if len(actor.inventory_list) >= 10:
        return ValidationResult(False, "Inventory is full")

    return ValidationResult(True)


def validate_drop(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a drop action."""
    if not action.target_object:
        return ValidationResult(False, "No item to drop")

    if action.target_object not in actor.inventory_list:
        return ValidationResult(False, f"You don't have {action.target_object}")

    return ValidationResult(True)


def validate_wait(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a wait action."""
    return ValidationResult(True)


def validate_sleep(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a sleep action."""
    if actor.state == "sleeping":
        return ValidationResult(False, "Already sleeping")
    return ValidationResult(True)


def validate_work(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a work action."""
    if actor.energy < 2:
        return ValidationResult(False, "Too tired to work")
    return ValidationResult(True)


def validate_social(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a social action (greet, talk, ask, tell, help, confront)."""
    if not action.target_id:
        return ValidationResult(False, "No target for social action")

    target = world.get_agent(action.target_id)
    if not target:
        return ValidationResult(False, f"Agent {action.target_id} not found")

    # Check target is in same location
    if actor.location_id != target.location_id:
        return ValidationResult(False, f"{target.name} is not here")

    # Check target is not sleeping
    if target.state == "sleeping":
        return ValidationResult(False, f"{target.name} is sleeping")

    return ValidationResult(True)


def validate_give(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a give action."""
    # First validate as social action
    result = validate_social(action, actor, world)
    if not result.valid:
        return result

    # Check actor has the item
    if not action.target_object:
        return ValidationResult(False, "No item to give")

    if action.target_object not in actor.inventory_list:
        return ValidationResult(False, f"You don't have {action.target_object}")

    return ValidationResult(True)


def validate_avoid(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate an avoid action."""
    if not action.target_id:
        return ValidationResult(False, "No one to avoid")

    target = world.get_agent(action.target_id)
    if not target:
        return ValidationResult(False, f"Agent {action.target_id} not found")

    # Can only avoid someone in the same location
    if actor.location_id != target.location_id:
        return ValidationResult(False, f"{target.name} is not here")

    # Need somewhere to go
    if actor.location_id:
        location = world.get_location(actor.location_id)
        if location and not location.connections_list:
            return ValidationResult(False, "Nowhere to go")

    return ValidationResult(True)


def validate_gossip(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate a gossip action."""
    # First validate as social action
    result = validate_social(action, actor, world)
    if not result.valid:
        return result

    # Check subject exists
    subject_id = action.parameters.get("subject_id")
    if not subject_id:
        return ValidationResult(False, "No one to gossip about")

    subject = world.get_agent(subject_id)
    if not subject:
        return ValidationResult(False, f"Agent {subject_id} not found")

    # Can't gossip about someone who is present
    if actor.location_id == subject.location_id:
        return ValidationResult(False, f"Can't gossip about {subject.name} while they're here")

    return ValidationResult(True)


def validate_investigate(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate an investigate action."""
    mystery = action.parameters.get("mystery")
    if not mystery:
        return ValidationResult(False, "Nothing to investigate")

    # Check actor has curiosity trait high enough
    traits = actor.traits_dict
    if traits.get("curiosity", 5) < 3:
        return ValidationResult(False, "Not curious enough to investigate")

    return ValidationResult(True)


def validate_observe(action: Action, actor: Agent, world: World) -> ValidationResult:
    """Validate an observe action (hidden observation)."""
    if not action.target_id:
        return ValidationResult(False, "No one to observe")

    target = world.get_agent(action.target_id)
    if not target:
        return ValidationResult(False, f"Agent {action.target_id} not found")

    # Must be in same location
    if actor.location_id != target.location_id:
        return ValidationResult(False, f"{target.name} is not here")

    return ValidationResult(True)


def calculate_receptiveness(target: Agent, initiator: Agent, world: World) -> float:
    """Calculate how receptive target is to initiator's social action."""
    # Base receptiveness from mood
    mood = target.mood_dict
    base = mood.get("happiness", 5) / 10.0

    # Modify by relationship
    from hamlet.db import Relationship

    db = world.db
    rel = (
        db.query(Relationship)
        .filter(Relationship.agent_id == target.id, Relationship.target_id == initiator.id)
        .first()
    )

    if rel:
        # Score from -10 to +10, normalize to 0-1 range
        rel_modifier = (rel.score + 10) / 20.0
        base = (base + rel_modifier) / 2

    # Modify by energy
    energy_modifier = target.energy / 10.0
    base = base * 0.7 + energy_modifier * 0.3

    return max(0.0, min(1.0, base))
