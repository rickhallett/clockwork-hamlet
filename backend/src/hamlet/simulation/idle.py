"""Idle behaviors for agents when they have nothing specific to do.

Instead of agents doing "nothing", they can:
- Think aloud (internal monologue visible to viewers)
- Comment on surroundings
- React to their mood/needs
- Express personality quirks
- Muse about relationships
"""

import random
from dataclasses import dataclass

from hamlet.db import Agent
from hamlet.simulation.world import AgentPerception


@dataclass
class IdleBehavior:
    """An idle behavior for an agent."""

    type: str  # thought, mutter, action, observation
    content: str
    significance: int = 1  # 1-3, for event importance


def get_idle_behavior(agent: Agent, perception: AgentPerception) -> IdleBehavior | None:
    """Generate a personality-driven idle behavior for an agent.

    Returns None if the agent should truly do nothing (rare).
    """
    traits = agent.traits_dict
    mood = agent.mood_dict

    # Gather possible behaviors with weights
    behaviors: list[tuple[IdleBehavior, int]] = []

    # === NEED-BASED THOUGHTS ===
    if agent.hunger >= 6:
        behaviors.append((
            IdleBehavior("thought", _hunger_thought(agent), 1),
            3
        ))
    if agent.energy <= 4:
        behaviors.append((
            IdleBehavior("thought", _tiredness_thought(agent), 1),
            3
        ))
    if agent.social <= 3:
        behaviors.append((
            IdleBehavior("thought", _loneliness_thought(agent), 1),
            3
        ))

    # === MOOD-BASED BEHAVIORS ===
    happiness = mood.get("happiness", 5)
    if happiness >= 8:
        behaviors.append((
            IdleBehavior("action", _happy_action(agent), 1),
            2
        ))
    elif happiness <= 3:
        behaviors.append((
            IdleBehavior("action", _unhappy_action(agent), 1),
            2
        ))

    # === TRAIT-BASED BEHAVIORS ===

    # High curiosity - observe and wonder
    if traits.get("curiosity", 5) >= 7:
        if perception.nearby_objects:
            obj = random.choice(perception.nearby_objects)
            behaviors.append((
                IdleBehavior("observation", f"{agent.name} eyes the {obj} with interest", 1),
                2
            ))
        behaviors.append((
            IdleBehavior("thought", _curious_thought(agent, perception), 1),
            2
        ))

    # Low discretion - mutter to self
    if traits.get("discretion", 5) <= 3:
        behaviors.append((
            IdleBehavior("mutter", _indiscreet_mutter(agent), 1),
            3
        ))

    # High perception - notice details
    if traits.get("perception", 5) >= 7:
        behaviors.append((
            IdleBehavior("observation", _perceptive_observation(agent, perception), 1),
            2
        ))

    # High empathy + nearby people - concern for others
    if traits.get("empathy", 5) >= 7 and perception.nearby_agents:
        other = random.choice(perception.nearby_agents)
        behaviors.append((
            IdleBehavior("thought", f"{agent.name} wonders how {other} is really doing", 1),
            2
        ))

    # Low energy - physical fidgeting
    if traits.get("energy", 5) <= 3:
        behaviors.append((
            IdleBehavior("action", f"{agent.name} stifles a yawn", 1),
            2
        ))

    # High charm - preening
    if traits.get("charm", 5) >= 7:
        behaviors.append((
            IdleBehavior("action", _charming_action(agent), 1),
            1
        ))

    # === LOCATION-BASED BEHAVIORS ===
    location_behaviors = _location_idle(agent, perception)
    for b in location_behaviors:
        behaviors.append((b, 1))

    # === UNIVERSAL IDLE BEHAVIORS ===
    behaviors.append((
        IdleBehavior("action", f"{agent.name} gazes into the distance", 1),
        1
    ))
    behaviors.append((
        IdleBehavior("action", f"{agent.name} stretches", 1),
        1
    ))

    # 10% chance to truly do nothing (silence is golden)
    if random.random() < 0.1:
        return None

    if not behaviors:
        return None

    # Weighted random selection
    options, weights = zip(*behaviors)
    return random.choices(options, weights=weights, k=1)[0]


def _hunger_thought(agent: Agent) -> str:
    """Generate a hunger-related thought."""
    thoughts = [
        f"{agent.name} thinks about food",
        f"{agent.name}'s stomach growls audibly",
        f"{agent.name} wonders what's for supper",
        f"{agent.name} dreams of fresh bread",
        f"{agent.name} contemplates the bakery's hours",
    ]
    return random.choice(thoughts)


def _tiredness_thought(agent: Agent) -> str:
    """Generate a tiredness-related thought."""
    thoughts = [
        f"{agent.name} suppresses a yawn",
        f"{agent.name} rubs tired eyes",
        f"{agent.name} longs for a soft bed",
        f"{agent.name} considers a quick nap",
        f"{agent.name}'s eyelids grow heavy",
    ]
    return random.choice(thoughts)


def _loneliness_thought(agent: Agent) -> str:
    """Generate a loneliness-related thought."""
    thoughts = [
        f"{agent.name} feels a bit isolated",
        f"{agent.name} wishes for some company",
        f"{agent.name} thinks about old friends",
        f"{agent.name} considers seeking someone out",
        f"{agent.name} sighs quietly to themselves",
    ]
    return random.choice(thoughts)


def _happy_action(agent: Agent) -> str:
    """Generate a happy behavior."""
    actions = [
        f"{agent.name} hums a cheerful tune",
        f"{agent.name} smiles to themselves",
        f"{agent.name} walks with a spring in their step",
        f"{agent.name} whistles softly",
        f"{agent.name} chuckles at a private thought",
    ]
    return random.choice(actions)


def _unhappy_action(agent: Agent) -> str:
    """Generate an unhappy behavior."""
    actions = [
        f"{agent.name} sighs heavily",
        f"{agent.name} frowns at nothing in particular",
        f"{agent.name} stares at the ground",
        f"{agent.name} fidgets restlessly",
        f"{agent.name} mutters under their breath",
    ]
    return random.choice(actions)


def _curious_thought(agent: Agent, perception: AgentPerception) -> str:
    """Generate a curiosity-driven thought."""
    if perception.nearby_objects:
        obj = random.choice(perception.nearby_objects)
        thoughts = [
            f"{agent.name} wonders about the history of the {obj}",
            f"{agent.name} considers examining the {obj} more closely",
            f"{agent.name} notices something odd about the {obj}",
        ]
    else:
        thoughts = [
            f"{agent.name} wonders what secrets this place holds",
            f"{agent.name} mentally catalogs today's observations",
            f"{agent.name} ponders the village's mysteries",
        ]
    return random.choice(thoughts)


def _indiscreet_mutter(agent: Agent) -> str:
    """Generate something an indiscreet person might mutter."""
    mutters = [
        f"{agent.name} mutters about village gossip",
        f"{agent.name} talks to themselves about recent events",
        f"{agent.name} accidentally speaks their thoughts aloud",
        f"{agent.name} mumbles something probably best kept private",
        f"{agent.name} narrates their own actions under their breath",
    ]
    return random.choice(mutters)


def _perceptive_observation(agent: Agent, perception: AgentPerception) -> str:
    """Generate a perceptive observation."""
    if perception.nearby_agents:
        other = random.choice(perception.nearby_agents)
        observations = [
            f"{agent.name} notices {other} seems distracted",
            f"{agent.name} observes {other}'s unusual demeanor",
            f"{agent.name} catches {other} glancing around nervously",
        ]
    else:
        observations = [
            f"{agent.name} notices the subtle shift in the air",
            f"{agent.name} spots something others might miss",
            f"{agent.name} takes mental note of their surroundings",
            f"{agent.name} listens to the ambient sounds",
        ]
    return random.choice(observations)


def _charming_action(agent: Agent) -> str:
    """Generate a charming person's idle action."""
    actions = [
        f"{agent.name} adjusts their appearance",
        f"{agent.name} practices a winning smile",
        f"{agent.name} smooths down their clothes",
        f"{agent.name} strikes a casual but flattering pose",
    ]
    return random.choice(actions)


def _location_idle(agent: Agent, perception: AgentPerception) -> list[IdleBehavior]:
    """Generate location-specific idle behaviors."""
    behaviors = []
    loc = perception.location_name.lower()

    if "bakery" in loc:
        behaviors.append(IdleBehavior("observation", f"{agent.name} inhales the aroma of fresh bread", 1))
    elif "tavern" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} drums fingers on the bar", 1))
        behaviors.append(IdleBehavior("observation", f"{agent.name} watches the fireplace crackle", 1))
    elif "church" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} bows their head in quiet reflection", 1))
        behaviors.append(IdleBehavior("observation", f"{agent.name} admires the stained glass", 1))
    elif "square" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} watches villagers pass by", 1))
        behaviors.append(IdleBehavior("observation", f"{agent.name} listens to the fountain", 1))
    elif "blacksmith" in loc or "forge" in loc:
        behaviors.append(IdleBehavior("observation", f"{agent.name} watches the sparks fly", 1))
    elif "garden" in loc or "farm" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} brushes dirt from their hands", 1))
        behaviors.append(IdleBehavior("observation", f"{agent.name} checks the state of the crops", 1))
    elif "inn" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} leafs through the guest book", 1))
    elif "cemetery" in loc:
        behaviors.append(IdleBehavior("action", f"{agent.name} pays silent respects", 1))
        behaviors.append(IdleBehavior("thought", f"{agent.name} reflects on mortality", 1))
    elif "forest" in loc:
        behaviors.append(IdleBehavior("observation", f"{agent.name} listens to the rustling leaves", 1))
        behaviors.append(IdleBehavior("thought", f"{agent.name} feels the forest watching back", 1))

    return behaviors
