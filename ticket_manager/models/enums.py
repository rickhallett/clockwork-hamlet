"""Enums and constants for ticket manager."""

from enum import Enum


class TicketType(str, Enum):
    """Ticket hierarchy types."""

    EPIC = "epic"
    STORY = "story"
    TASK = "task"


class TicketStatus(str, Enum):
    """Workflow states."""

    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"
    CANCELLED = "cancelled"


class Priority(int, Enum):
    """Priority levels (lower number = higher priority)."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    TRIVIAL = 5


# Status transitions (state machine)
VALID_TRANSITIONS: dict[TicketStatus, list[TicketStatus]] = {
    TicketStatus.BACKLOG: [TicketStatus.TODO, TicketStatus.CANCELLED],
    TicketStatus.TODO: [
        TicketStatus.IN_PROGRESS,
        TicketStatus.BACKLOG,
        TicketStatus.CANCELLED,
    ],
    TicketStatus.IN_PROGRESS: [
        TicketStatus.REVIEW,
        TicketStatus.TODO,
        TicketStatus.CANCELLED,
    ],
    TicketStatus.REVIEW: [
        TicketStatus.DONE,
        TicketStatus.IN_PROGRESS,
        TicketStatus.CANCELLED,
    ],
    TicketStatus.DONE: [TicketStatus.TODO],  # Reopen
    TicketStatus.CANCELLED: [TicketStatus.BACKLOG],  # Reactivate
}

# Type hierarchy constraints (what type can be a parent)
VALID_PARENT_TYPES: dict[TicketType, TicketType | None] = {
    TicketType.EPIC: None,  # Epics have no parent
    TicketType.STORY: TicketType.EPIC,
    TicketType.TASK: TicketType.STORY,
}


def can_transition(from_status: TicketStatus, to_status: TicketStatus) -> bool:
    """Check if a status transition is valid."""
    return to_status in VALID_TRANSITIONS.get(from_status, [])


def get_valid_parent_type(ticket_type: TicketType) -> TicketType | None:
    """Get the valid parent type for a ticket type."""
    return VALID_PARENT_TYPES.get(ticket_type)


# Priority display names
PRIORITY_NAMES: dict[int, str] = {
    1: "Critical",
    2: "High",
    3: "Medium",
    4: "Low",
    5: "Trivial",
}

# Status display colors (for Rich)
STATUS_COLORS: dict[TicketStatus, str] = {
    TicketStatus.BACKLOG: "dim",
    TicketStatus.TODO: "white",
    TicketStatus.IN_PROGRESS: "cyan",
    TicketStatus.REVIEW: "yellow",
    TicketStatus.DONE: "green",
    TicketStatus.CANCELLED: "red",
}

# Priority display colors (for Rich)
PRIORITY_COLORS: dict[int, str] = {
    1: "red bold",
    2: "red",
    3: "yellow",
    4: "blue",
    5: "dim",
}

# Type display colors (for Rich)
TYPE_COLORS: dict[TicketType, str] = {
    TicketType.EPIC: "magenta bold",
    TicketType.STORY: "blue",
    TicketType.TASK: "white",
}
