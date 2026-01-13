"""Action type definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionCategory(Enum):
    """Categories of actions."""

    SOLO = "solo"
    SOCIAL = "social"
    SPECIAL = "special"


class ActionType(Enum):
    """All available action types."""

    # Solo actions
    MOVE = "move"
    EXAMINE = "examine"
    TAKE = "take"
    DROP = "drop"
    USE = "use"
    WAIT = "wait"
    SLEEP = "sleep"
    WORK = "work"

    # Social actions
    GREET = "greet"
    TALK = "talk"
    ASK = "ask"
    TELL = "tell"
    GIVE = "give"
    HELP = "help"
    CONFRONT = "confront"
    AVOID = "avoid"

    # Special actions
    INVESTIGATE = "investigate"
    GOSSIP = "gossip"
    SCHEME = "scheme"
    CONFESS = "confess"
    OBSERVE = "observe"


# Map action types to categories
ACTION_CATEGORIES = {
    ActionType.MOVE: ActionCategory.SOLO,
    ActionType.EXAMINE: ActionCategory.SOLO,
    ActionType.TAKE: ActionCategory.SOLO,
    ActionType.DROP: ActionCategory.SOLO,
    ActionType.USE: ActionCategory.SOLO,
    ActionType.WAIT: ActionCategory.SOLO,
    ActionType.SLEEP: ActionCategory.SOLO,
    ActionType.WORK: ActionCategory.SOLO,
    ActionType.GREET: ActionCategory.SOCIAL,
    ActionType.TALK: ActionCategory.SOCIAL,
    ActionType.ASK: ActionCategory.SOCIAL,
    ActionType.TELL: ActionCategory.SOCIAL,
    ActionType.GIVE: ActionCategory.SOCIAL,
    ActionType.HELP: ActionCategory.SOCIAL,
    ActionType.CONFRONT: ActionCategory.SOCIAL,
    ActionType.AVOID: ActionCategory.SOCIAL,
    ActionType.INVESTIGATE: ActionCategory.SPECIAL,
    ActionType.GOSSIP: ActionCategory.SPECIAL,
    ActionType.SCHEME: ActionCategory.SPECIAL,
    ActionType.CONFESS: ActionCategory.SPECIAL,
    ActionType.OBSERVE: ActionCategory.SPECIAL,
}


@dataclass
class Action:
    """Base action class."""

    type: ActionType
    actor_id: str
    target_id: str | None = None
    target_object: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)

    @property
    def category(self) -> ActionCategory:
        """Get the action category."""
        return ACTION_CATEGORIES[self.type]

    @property
    def is_social(self) -> bool:
        """Check if this is a social action."""
        return self.category == ActionCategory.SOCIAL

    def __str__(self) -> str:
        if self.target_id:
            return f"{self.type.value}({self.actor_id} -> {self.target_id})"
        elif self.target_object:
            return f"{self.type.value}({self.actor_id} -> {self.target_object})"
        else:
            return f"{self.type.value}({self.actor_id})"


@dataclass
class ActionResult:
    """Result of an action execution."""

    success: bool
    action: Action
    message: str
    reason: str | None = None
    data: dict[str, Any] = field(default_factory=dict)


# Convenience constructors for common actions
def Move(actor_id: str, destination: str) -> Action:
    """Create a move action."""
    return Action(type=ActionType.MOVE, actor_id=actor_id, target_id=destination)


def Examine(actor_id: str, target: str) -> Action:
    """Create an examine action."""
    return Action(type=ActionType.EXAMINE, actor_id=actor_id, target_object=target)


def Take(actor_id: str, item: str) -> Action:
    """Create a take action."""
    return Action(type=ActionType.TAKE, actor_id=actor_id, target_object=item)


def Drop(actor_id: str, item: str) -> Action:
    """Create a drop action."""
    return Action(type=ActionType.DROP, actor_id=actor_id, target_object=item)


def Wait(actor_id: str) -> Action:
    """Create a wait action."""
    return Action(type=ActionType.WAIT, actor_id=actor_id)


def Sleep(actor_id: str) -> Action:
    """Create a sleep action."""
    return Action(type=ActionType.SLEEP, actor_id=actor_id)


def Work(actor_id: str, job_type: str = "default") -> Action:
    """Create a work action."""
    return Action(type=ActionType.WORK, actor_id=actor_id, parameters={"job_type": job_type})


def Greet(actor_id: str, target_id: str) -> Action:
    """Create a greet action."""
    return Action(type=ActionType.GREET, actor_id=actor_id, target_id=target_id)


def Talk(actor_id: str, target_id: str, topic: str = "") -> Action:
    """Create a talk action."""
    return Action(
        type=ActionType.TALK, actor_id=actor_id, target_id=target_id, parameters={"topic": topic}
    )


def Ask(actor_id: str, target_id: str, question: str) -> Action:
    """Create an ask action."""
    return Action(
        type=ActionType.ASK,
        actor_id=actor_id,
        target_id=target_id,
        parameters={"question": question},
    )


def Tell(actor_id: str, target_id: str, information: str) -> Action:
    """Create a tell action."""
    return Action(
        type=ActionType.TELL,
        actor_id=actor_id,
        target_id=target_id,
        parameters={"information": information},
    )


def Give(actor_id: str, target_id: str, item: str) -> Action:
    """Create a give action."""
    return Action(type=ActionType.GIVE, actor_id=actor_id, target_id=target_id, target_object=item)


def Help(actor_id: str, target_id: str, task: str = "") -> Action:
    """Create a help action."""
    return Action(
        type=ActionType.HELP, actor_id=actor_id, target_id=target_id, parameters={"task": task}
    )


def Confront(actor_id: str, target_id: str, accusation: str = "") -> Action:
    """Create a confront action."""
    return Action(
        type=ActionType.CONFRONT,
        actor_id=actor_id,
        target_id=target_id,
        parameters={"accusation": accusation},
    )


def Avoid(actor_id: str, target_id: str) -> Action:
    """Create an avoid action."""
    return Action(type=ActionType.AVOID, actor_id=actor_id, target_id=target_id)


def Gossip(actor_id: str, target_id: str, subject_id: str, rumor: str = "") -> Action:
    """Create a gossip action."""
    return Action(
        type=ActionType.GOSSIP,
        actor_id=actor_id,
        target_id=target_id,
        parameters={"subject_id": subject_id, "rumor": rumor},
    )


def Investigate(actor_id: str, mystery: str) -> Action:
    """Create an investigate action."""
    return Action(type=ActionType.INVESTIGATE, actor_id=actor_id, parameters={"mystery": mystery})


def Observe(actor_id: str, target_id: str) -> Action:
    """Create an observe action (hidden)."""
    return Action(type=ActionType.OBSERVE, actor_id=actor_id, target_id=target_id)
