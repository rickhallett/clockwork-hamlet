"""Life events system for agent milestones (marriage, rivalries, mentorship)."""

from hamlet.life_events.consequences import LifeEventConsequences
from hamlet.life_events.generator import LifeEventGenerator
from hamlet.life_events.types import (
    LifeEventStatus,
    LifeEventType,
)

__all__ = [
    "LifeEventConsequences",
    "LifeEventGenerator",
    "LifeEventStatus",
    "LifeEventType",
]
