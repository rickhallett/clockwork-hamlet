"""Action execution logic."""

import json
import logging
import time

from hamlet.actions.types import Action, ActionResult, ActionType
from hamlet.actions.validation import calculate_receptiveness, validate_action
from hamlet.db import Agent, Event, Memory, Relationship
from hamlet.simulation.world import World

logger = logging.getLogger(__name__)

# Receptiveness threshold for social actions
RECEPTIVENESS_THRESHOLD = 0.3


def execute_action(action: Action, world: World) -> ActionResult:
    """Execute an action and return the result."""
    # Validate action
    validation = validate_action(action, world)
    if not validation.valid:
        return ActionResult(
            success=False,
            action=action,
            message=f"Action invalid: {validation.reason}",
            reason=validation.reason,
        )

    actor = world.get_agent(action.actor_id)
    if not actor:
        return ActionResult(
            success=False,
            action=action,
            message="Actor not found",
            reason="actor_not_found",
        )

    # For social actions, check receptiveness
    if action.is_social and action.target_id:
        target = world.get_agent(action.target_id)
        if target:
            receptiveness = calculate_receptiveness(target, actor, world)
            if receptiveness < RECEPTIVENESS_THRESHOLD:
                return ActionResult(
                    success=False,
                    action=action,
                    message=f"{target.name} is not receptive",
                    reason="rebuffed",
                    data={"receptiveness": receptiveness},
                )

    # Execute the action
    executors = {
        ActionType.MOVE: execute_move,
        ActionType.EXAMINE: execute_examine,
        ActionType.TAKE: execute_take,
        ActionType.DROP: execute_drop,
        ActionType.WAIT: execute_wait,
        ActionType.SLEEP: execute_sleep,
        ActionType.WORK: execute_work,
        ActionType.GREET: execute_greet,
        ActionType.TALK: execute_talk,
        ActionType.ASK: execute_ask,
        ActionType.TELL: execute_tell,
        ActionType.GIVE: execute_give,
        ActionType.HELP: execute_help,
        ActionType.CONFRONT: execute_confront,
        ActionType.AVOID: execute_avoid,
        ActionType.GOSSIP: execute_gossip,
        ActionType.INVESTIGATE: execute_investigate,
        ActionType.OBSERVE: execute_observe,
    }

    executor = executors.get(action.type, execute_default)
    result = executor(action, actor, world)

    # Process witnesses
    if result.success:
        process_witnesses(action, result, actor, world)

    # Commit changes
    world.commit()

    return result


def execute_move(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a move action."""
    destination = world.get_location(action.target_id)
    old_location = actor.location_id
    actor.location_id = action.target_id

    record_event(
        world,
        "movement",
        f"{actor.name} arrived at {destination.name}",
        [actor.id],
        action.target_id,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} moved to {destination.name}",
        data={"from": old_location, "to": action.target_id},
    )


def execute_examine(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute an examine action."""
    target = action.target_object or action.target_id
    record_event(
        world,
        "action",
        f"{actor.name} examined the {target}",
        [actor.id],
        actor.location_id,
    )

    # Create memory for the actor
    create_memory(
        world,
        actor,
        f"I examined the {target}",
        significance=2,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} examined {target}",
    )


def execute_take(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a take action."""
    item = action.target_object

    # Remove from location
    if actor.location_id:
        location = world.get_location(actor.location_id)
        if location:
            objects = location.objects_list
            if item in objects:
                objects.remove(item)
                location.objects_list = objects

    # Add to inventory
    inventory = actor.inventory_list
    inventory.append(item)
    actor.inventory_list = inventory

    record_event(
        world,
        "action",
        f"{actor.name} took the {item}",
        [actor.id],
        actor.location_id,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} took {item}",
    )


def execute_drop(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a drop action."""
    item = action.target_object

    # Remove from inventory
    # CLAUDE: why does this pattern below repeat in many functions? does this serve a benefit over actor.inventory_list.remove(item) ?
    inventory = actor.inventory_list
    inventory.remove(item)
    actor.inventory_list = inventory

    # Add to location
    if actor.location_id:
        location = world.get_location(actor.location_id)
        if location:
            objects = location.objects_list
            objects.append(item)
            location.objects_list = objects

    record_event(
        world,
        "action",
        f"{actor.name} dropped the {item}",
        [actor.id],
        actor.location_id,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} dropped {item}",
    )


def execute_wait(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a wait action."""
    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} waited",
    )


def execute_sleep(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a sleep action."""
    actor.state = "sleeping"

    record_event(
        world,
        "system",
        f"{actor.name} went to sleep",
        [actor.id],
        actor.location_id,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} went to sleep",
    )


def execute_work(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a work action."""
    job_type = action.parameters.get("job_type", "default")
    actor.energy = max(0, actor.energy - 1)

    record_event(
        world,
        "action",
        f"{actor.name} worked ({job_type})",
        [actor.id],
        actor.location_id,
    )

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} worked",
    )


def execute_greet(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a greet action."""
    target = world.get_agent(action.target_id)

    record_event(
        world,
        "dialogue",
        f"{actor.name} greeted {target.name}",
        [actor.id, target.id],
        actor.location_id,
        f'{actor.name}: "Hello, {target.name}!"',
    )

    # Improve relationship slightly
    update_relationship(world, actor.id, target.id, 1, "greeted")
    update_relationship(world, target.id, actor.id, 1, "was greeted by")

    # Create memories
    create_memory(world, actor, f"I greeted {target.name}", significance=3)
    create_memory(world, target, f"{actor.name} greeted me", significance=3)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} greeted {target.name}",
    )


def execute_talk(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a talk action."""
    target = world.get_agent(action.target_id)
    topic = action.parameters.get("topic", "various things")

    record_event(
        world,
        "dialogue",
        f"{actor.name} talked with {target.name} about {topic}",
        [actor.id, target.id],
        actor.location_id,
    )

    # Improve relationship
    update_relationship(world, actor.id, target.id, 1, f"talked about {topic}")
    update_relationship(world, target.id, actor.id, 1, f"talked about {topic}")

    # Increase social satisfaction
    actor.social = min(10, actor.social + 1)
    target.social = min(10, target.social + 1)

    # Create memories
    create_memory(world, actor, f"I talked with {target.name} about {topic}", significance=4)
    create_memory(world, target, f"{actor.name} talked to me about {topic}", significance=4)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} talked with {target.name}",
    )


def execute_ask(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute an ask action."""
    target = world.get_agent(action.target_id)
    question = action.parameters.get("question", "something")

    record_event(
        world,
        "dialogue",
        f"{actor.name} asked {target.name} about {question}",
        [actor.id, target.id],
        actor.location_id,
    )

    create_memory(world, actor, f"I asked {target.name} about {question}", significance=4)
    create_memory(world, target, f"{actor.name} asked me about {question}", significance=4)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} asked {target.name} about {question}",
    )


def execute_tell(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a tell action."""
    target = world.get_agent(action.target_id)
    information = action.parameters.get("information", "something")

    record_event(
        world,
        "dialogue",
        f"{actor.name} told {target.name} something",
        [actor.id, target.id],
        actor.location_id,
        f'{actor.name} shared information with {target.name}: "{information}"',
    )

    # Create memories with the information
    create_memory(world, actor, f"I told {target.name}: {information}", significance=5)
    create_memory(world, target, f"{actor.name} told me: {information}", significance=5)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} told {target.name} something",
    )


def execute_give(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a give action."""
    target = world.get_agent(action.target_id)
    item = action.target_object

    # Transfer item
    actor_inv = actor.inventory_list
    actor_inv.remove(item)
    actor.inventory_list = actor_inv

    target_inv = target.inventory_list
    target_inv.append(item)
    target.inventory_list = target_inv

    record_event(
        world,
        "action",
        f"{actor.name} gave {item} to {target.name}",
        [actor.id, target.id],
        actor.location_id,
    )

    # Giving improves relationship
    update_relationship(world, target.id, actor.id, 2, f"received {item}")
    update_relationship(world, actor.id, target.id, 1, f"gave {item}")

    create_memory(world, actor, f"I gave {item} to {target.name}", significance=5)
    create_memory(world, target, f"{actor.name} gave me {item}", significance=6)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} gave {item} to {target.name}",
    )


def execute_help(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a help action."""
    target = world.get_agent(action.target_id)
    task = action.parameters.get("task", "with something")

    record_event(
        world,
        "action",
        f"{actor.name} helped {target.name} {task}",
        [actor.id, target.id],
        actor.location_id,
    )

    # Helping significantly improves relationship
    update_relationship(world, target.id, actor.id, 3, f"helped {task}")
    update_relationship(world, actor.id, target.id, 1, f"helped with {task}")

    create_memory(world, actor, f"I helped {target.name} {task}", significance=6)
    create_memory(world, target, f"{actor.name} helped me {task}", significance=7)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} helped {target.name}",
    )


def execute_confront(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a confront action."""
    target = world.get_agent(action.target_id)
    accusation = action.parameters.get("accusation", "something")

    record_event(
        world,
        "dialogue",
        f"{actor.name} confronted {target.name}",
        [actor.id, target.id],
        actor.location_id,
        f"{actor.name} confronted {target.name} about {accusation}",
        significance=3,
    )

    # Confrontation damages relationships
    update_relationship(world, target.id, actor.id, -2, f"confronted about {accusation}")
    update_relationship(world, actor.id, target.id, -1, f"confronted about {accusation}")

    create_memory(world, actor, f"I confronted {target.name} about {accusation}", significance=7)
    create_memory(world, target, f"{actor.name} confronted me about {accusation}", significance=8)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} confronted {target.name}",
        data={"accusation": accusation},
    )


def execute_avoid(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute an avoid action - move to escape someone."""
    target = world.get_agent(action.target_id)

    # Find somewhere to go
    if actor.location_id:
        location = world.get_location(actor.location_id)
        if location and location.connections_list:
            # Move to first available connection
            new_location_id = location.connections_list[0]
            actor.location_id = new_location_id

            record_event(
                world,
                "movement",
                f"{actor.name} left to avoid {target.name}",
                [actor.id],
                new_location_id,
            )

            create_memory(world, actor, f"I left to avoid {target.name}", significance=5)

            return ActionResult(
                success=True,
                action=action,
                message=f"{actor.name} left to avoid {target.name}",
            )

    return ActionResult(
        success=False,
        action=action,
        message="Nowhere to go",
        reason="no_exit",
    )


def execute_gossip(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute a gossip action."""
    target = world.get_agent(action.target_id)
    subject_id = action.parameters.get("subject_id")
    subject = world.get_agent(subject_id)
    rumor = action.parameters.get("rumor", "something interesting")

    record_event(
        world,
        "dialogue",
        f"{actor.name} gossiped with {target.name} about {subject.name}",
        [actor.id, target.id],
        actor.location_id,
        significance=2,
    )

    # Gossip affects discretion reputation
    # Low discretion actors are known gossips

    # Create memories for both parties
    create_memory(
        world, actor, f"I gossiped with {target.name} about {subject.name}", significance=4
    )
    create_memory(
        world, target, f"{actor.name} told me gossip about {subject.name}: {rumor}", significance=5
    )

    # Target now knows the rumor too
    update_relationship(world, actor.id, target.id, 1, "shared gossip")

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} gossiped about {subject.name}",
    )


def execute_investigate(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute an investigate action."""
    mystery = action.parameters.get("mystery", "something")

    record_event(
        world,
        "action",
        f"{actor.name} investigated {mystery}",
        [actor.id],
        actor.location_id,
    )

    create_memory(world, actor, f"I investigated {mystery}", significance=6)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} investigated {mystery}",
    )


def execute_observe(action: Action, actor: Agent, world: World) -> ActionResult:
    """Execute an observe action (hidden)."""
    target = world.get_agent(action.target_id)

    # This is a hidden action - no public event
    create_memory(world, actor, f"I secretly observed {target.name}", significance=4)

    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} observed {target.name}",
        data={"hidden": True},
    )


def execute_default(action: Action, actor: Agent, world: World) -> ActionResult:
    """Default executor for unhandled action types."""
    return ActionResult(
        success=True,
        action=action,
        message=f"{actor.name} performed {action.type.value}",
    )


def process_witnesses(action: Action, result: ActionResult, actor: Agent, world: World) -> None:
    """Process witnesses to an action."""
    # Skip hidden actions
    if result.data.get("hidden"):
        return

    # Get agents in the same location (excluding actor and target)
    if not actor.location_id:
        return

    witnesses = world.get_agents_at_location(actor.location_id)
    witnesses = [w for w in witnesses if w.id != actor.id and w.id != action.target_id]

    for witness in witnesses:
        # Create witness memory
        create_memory(
            world,
            witness,
            f"I saw {result.message}",
            significance=3,
            memory_type="working",
        )

        # Witnessing affects opinions
        if action.type == ActionType.HELP:
            # Witnessing help improves opinion of helper
            update_relationship(world, witness.id, actor.id, 1, "saw helping")
        elif action.type == ActionType.CONFRONT:
            # Opinion depends on existing relationships
            rel_to_target = get_relationship_score(world, witness.id, action.target_id)
            if rel_to_target < 0:
                # Witness dislikes target, approves of confrontation
                update_relationship(world, witness.id, actor.id, 1, "stood up to someone I dislike")
            else:
                # Witness likes target, disapproves
                update_relationship(world, witness.id, actor.id, -1, "was aggressive")
        elif action.type == ActionType.GIVE:
            # Witnessing generosity
            update_relationship(world, witness.id, actor.id, 1, "saw generosity")


def update_relationship(
    world: World, agent_id: str, target_id: str, score_delta: int, reason: str
) -> None:
    """Update relationship between two agents."""
    db = world.db

    rel = (
        db.query(Relationship)
        .filter(Relationship.agent_id == agent_id, Relationship.target_id == target_id)
        .first()
    )

    if not rel:
        rel = Relationship(
            agent_id=agent_id,
            target_id=target_id,
            type="acquaintance",
            score=0,
            history=json.dumps([]),
        )
        db.add(rel)

    # Update score (clamped to -10 to +10)
    rel.score = max(-10, min(10, rel.score + score_delta))

    # Update history
    history = rel.history_list
    history.append(reason)
    if len(history) > 10:
        history = history[-10:]
    rel.history_list = history

    # Update relationship type based on score
    if rel.score >= 7:
        rel.type = "close_friend"
    elif rel.score >= 4:
        rel.type = "friend"
    elif rel.score >= 1:
        rel.type = "acquaintance"
    elif rel.score >= -3:
        rel.type = "neutral"
    elif rel.score >= -6:
        rel.type = "suspicious"
    else:
        rel.type = "rival"


def get_relationship_score(world: World, agent_id: str, target_id: str) -> int:
    """Get the relationship score between two agents."""
    db = world.db
    rel = (
        db.query(Relationship)
        .filter(Relationship.agent_id == agent_id, Relationship.target_id == target_id)
        .first()
    )
    return rel.score if rel else 0


def create_memory(
    world: World,
    agent: Agent,
    content: str,
    significance: int = 5,
    memory_type: str = "working",
) -> None:
    """Create a memory for an agent."""
    memory = Memory(
        agent_id=agent.id,
        timestamp=int(time.time()),
        type=memory_type,
        content=content,
        significance=significance,
    )
    world.db.add(memory)


def record_event(
    world: World,
    event_type: str,
    summary: str,
    actors: list[str],
    location_id: str | None,
    detail: str | None = None,
    significance: int = 1,
) -> None:
    """Record an event to the database."""
    event = Event(
        timestamp=int(time.time()),
        type=event_type,
        actors=json.dumps(actors),
        location_id=location_id,
        summary=summary,
        detail=detail,
        significance=significance,
    )
    world.db.add(event)
