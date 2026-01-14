"""Generate unique ticket keys (PROJECT-123 format)."""

from sqlalchemy.orm import Session

from ticket_manager.config import settings
from ticket_manager.db.models import KeySequence


def generate_key(session: Session, project: str | None = None) -> str:
    """Generate a unique ticket key.

    Args:
        session: Database session
        project: Project prefix (uses default if not provided)

    Returns:
        Unique key like "PROJ-123"
    """
    # Use provided project or fall back to default
    prefix = project or settings.default_project or settings.key_prefix

    # Normalize prefix (uppercase, no spaces)
    prefix = prefix.upper().replace(" ", "_")

    # Get or create the sequence for this project
    sequence = session.query(KeySequence).filter(KeySequence.project == prefix).first()

    if sequence is None:
        sequence = KeySequence(project=prefix, last_number=0)
        session.add(sequence)

    # Increment and return
    sequence.last_number += 1
    session.flush()  # Ensure the number is persisted

    return f"{prefix}-{sequence.last_number}"


def parse_key(key: str) -> tuple[str, int]:
    """Parse a ticket key into project and number.

    Args:
        key: Key like "PROJ-123"

    Returns:
        Tuple of (project, number)

    Raises:
        ValueError: If key format is invalid
    """
    parts = key.rsplit("-", 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid key format: {key}")

    project, number_str = parts
    try:
        number = int(number_str)
    except ValueError:
        raise ValueError(f"Invalid key format: {key}")

    return project.upper(), number


def validate_key(key: str) -> bool:
    """Check if a key has valid format.

    Args:
        key: Key to validate

    Returns:
        True if valid format
    """
    try:
        parse_key(key)
        return True
    except ValueError:
        return False
