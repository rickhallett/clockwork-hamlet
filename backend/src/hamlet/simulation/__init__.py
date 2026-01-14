"""Simulation module."""

from hamlet.simulation.dramatic import (
    CHARACTER_SECRETS,
    ConflictEvent,
    ConflictStage,
    RomanceEvent,
    RomanceStage,
    SecretRevelation,
    SecretType,
    VillageEvent,
    VillageEventType,
    cascade_village_event_effects,
    check_conflict_escalation,
    check_random_village_event,
    check_romantic_progression,
    check_secret_discovery,
    generate_conflict_escalation_dialogue,
    generate_romance_dialogue,
    generate_secret_reaction,
    get_conflict_stage,
    get_romance_stage,
    process_conflict_aftermath,
    process_romance_aftermath,
    spread_secret,
    trigger_village_event,
)
from hamlet.simulation.engine import SimulationEngine, run_simulation
from hamlet.simulation.events import EventBus, EventType, SimulationEvent, event_bus
from hamlet.simulation.world import AgentPerception, World, WorldSnapshot

__all__ = [
    # Engine
    "SimulationEngine",
    "run_simulation",
    # Events
    "EventBus",
    "EventType",
    "SimulationEvent",
    "event_bus",
    # World
    "World",
    "WorldSnapshot",
    "AgentPerception",
    # Dramatic Events (LIFE-26 to LIFE-29)
    "ConflictStage",
    "ConflictEvent",
    "SecretType",
    "SecretRevelation",
    "RomanceStage",
    "RomanceEvent",
    "VillageEventType",
    "VillageEvent",
    "CHARACTER_SECRETS",
    # Conflict escalation (LIFE-26)
    "get_conflict_stage",
    "check_conflict_escalation",
    "generate_conflict_escalation_dialogue",
    "process_conflict_aftermath",
    # Secret revelation (LIFE-27)
    "check_secret_discovery",
    "spread_secret",
    "generate_secret_reaction",
    # Romantic progression (LIFE-28)
    "get_romance_stage",
    "check_romantic_progression",
    "generate_romance_dialogue",
    "process_romance_aftermath",
    # Village events (LIFE-29)
    "trigger_village_event",
    "check_random_village_event",
    "cascade_village_event_effects",
]
