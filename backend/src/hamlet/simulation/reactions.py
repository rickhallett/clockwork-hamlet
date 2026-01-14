"""Witness reactions to significant events.

Agents visibly react when they witness significant events like confrontations,
gossip, romantic moments, etc. Reactions are personality-driven based on
the witness's traits.
"""

import random

from hamlet.db import Agent


def generate_witness_reaction(
    witness_agent: Agent,
    event_type: str,
    actors: list[str],
    significance: int,
) -> str | None:
    """Generate a visible reaction for a witness to an event.

    Args:
        witness_agent: The agent witnessing the event
        event_type: Type of event being witnessed (e.g., 'confront', 'gossip', 'help')
        actors: Names of agents involved in the event
        significance: How significant the event is (1-10)

    Returns:
        A reaction string like "Agnes raises an eyebrow" or None if no reaction
    """
    # Low-significance events only get reactions 50% of the time
    if significance <= 3 and random.random() < 0.5:
        return None

    traits = witness_agent.traits_dict
    name = witness_agent.name

    # Get relevant traits with defaults
    empathy = traits.get("empathy", 5)
    curiosity = traits.get("curiosity", 5)
    discretion = traits.get("discretion", 5)

    # Build weighted reaction options based on personality and event type
    reactions: list[tuple[str, int]] = []

    # === HIGH EMPATHY REACTIONS ===
    # Concerned reactions to conflict
    if empathy >= 7:
        if event_type in ("confront", "avoid"):
            reactions.extend([
                (f"{name} looks concerned at the tension", 3),
                (f"{name} winces sympathetically", 3),
                (f"{name} shifts uncomfortably at the conflict", 2),
                (f"{name} frowns with worry", 2),
            ])
        elif event_type == "help":
            reactions.extend([
                (f"{name} smiles warmly at the kindness", 3),
                (f"{name} nods approvingly", 2),
            ])
        else:
            reactions.extend([
                (f"{name} watches with a thoughtful expression", 2),
            ])

    # === HIGH CURIOSITY REACTIONS ===
    # Interested reactions to secrets and gossip
    if curiosity >= 7:
        if event_type == "gossip":
            reactions.extend([
                (f"{name} leans in with obvious interest", 3),
                (f"{name} perks up at the gossip", 3),
                (f"{name} edges closer to hear better", 2),
            ])
        elif event_type == "tell":
            reactions.extend([
                (f"{name} tilts their head with curiosity", 2),
                (f"{name} listens intently", 2),
            ])
        elif event_type == "investigate":
            reactions.extend([
                (f"{name}'s eyes widen with interest", 2),
            ])
        else:
            reactions.extend([
                (f"{name} watches with keen interest", 2),
            ])

    # === LOW DISCRETION REACTIONS ===
    # Audible gasps and comments
    if discretion <= 3:
        if event_type == "confront":
            reactions.extend([
                (f"{name} gasps audibly", 4),
                (f'"{name} mutters "Oh my..." under their breath', 3),
                (f"{name} whispers excitedly to no one in particular", 2),
            ])
        elif event_type == "gossip":
            reactions.extend([
                (f"{name} barely suppresses a giggle", 3),
                (f"{name} lets out an audible 'ooh'", 3),
            ])
        elif event_type == "give":
            reactions.extend([
                (f"{name} comments 'How generous!' just loud enough to hear", 2),
            ])
        elif event_type == "help":
            reactions.extend([
                (f"{name} exclaims softly at the kindness", 2),
            ])
        else:
            reactions.extend([
                (f"{name} reacts visibly", 2),
            ])

    # === HIGH DISCRETION REACTIONS ===
    # Subtle glances
    if discretion >= 7:
        reactions.extend([
            (f"{name} glances over briefly", 2),
            (f"{name} raises an eyebrow almost imperceptibly", 2),
            (f"{name} continues what they were doing but clearly noticed", 1),
        ])

    # === NEUTRAL/DEFAULT REACTIONS ===
    # For witnesses with moderate traits
    if not reactions:
        # Add some generic reactions
        if event_type == "confront":
            reactions.extend([
                (f"{name} looks up at the commotion", 2),
                (f"{name} pauses to watch", 2),
            ])
        elif event_type == "gossip":
            reactions.extend([
                (f"{name} pretends not to listen", 2),
                (f"{name} glances over curiously", 2),
            ])
        elif event_type == "help":
            reactions.extend([
                (f"{name} notices the helpful gesture", 2),
            ])
        elif event_type == "give":
            reactions.extend([
                (f"{name} observes the exchange", 2),
            ])
        else:
            reactions.extend([
                (f"{name} glances in their direction", 2),
                (f"{name} raises an eyebrow", 2),
            ])

    # Weighted random selection
    if reactions:
        options, weights = zip(*reactions)
        return random.choices(options, weights=weights, k=1)[0]

    return None
