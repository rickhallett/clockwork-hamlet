"""Spontaneous greetings when agents arrive at a location.

When an agent arrives at a location where other agents are present,
they may make a relationship-aware comment based on their personality.
"""

import random

from hamlet.db import Agent
from hamlet.simulation.world import AgentPerception


def generate_arrival_comment(
    agent: Agent, others: list[Agent], perception: AgentPerception
) -> str | None:
    """Generate a relationship-aware greeting when arriving at a location.

    Args:
        agent: The agent who just arrived
        others: List of other agents already at the location
        perception: The arriving agent's perception of the location

    Returns:
        A greeting/comment string, or None if the agent stays silent
    """
    # 30% chance to say nothing
    if random.random() < 0.3:
        return None

    if not others:
        return None

    traits = agent.traits_dict
    charm = traits.get("charm", 5)

    # Build relationship map for the arriving agent
    relationships = {}
    for rel in agent.relationships_as_source:
        relationships[rel.target_id] = {
            "type": rel.type,
            "score": rel.score,
        }

    # Find the most significant person to greet
    # Priority: friends > acquaintances > strangers > rivals
    friends = []
    acquaintances = []
    strangers = []
    rivals = []

    for other in others:
        rel = relationships.get(other.id)
        if rel:
            rel_type = rel["type"]
            if rel_type == "friend" or rel["score"] >= 5:
                friends.append(other)
            elif rel_type == "rival" or rel["score"] <= -5:
                rivals.append(other)
            elif rel_type == "acquaintance":
                acquaintances.append(other)
            else:
                strangers.append(other)
        else:
            strangers.append(other)

    # Select who to greet and how
    if friends:
        target = random.choice(friends)
        return _friendly_greeting(agent, target, charm)
    elif rivals:
        target = random.choice(rivals)
        return _rival_acknowledgment(agent, target, charm)
    elif acquaintances:
        target = random.choice(acquaintances)
        return _acquaintance_greeting(agent, target, charm)
    elif strangers:
        target = random.choice(strangers)
        return _stranger_greeting(agent, target, charm, perception)
    else:
        return None


def _friendly_greeting(agent: Agent, friend: Agent, charm: int) -> str:
    """Generate a warm greeting for a friend."""
    if charm >= 7:
        # High charm - warm and effusive
        greetings = [
            f'{agent.name} beams at {friend.name}: "Ah, just the person I was hoping to see!"',
            f'{agent.name} greets {friend.name} warmly: "What a pleasant surprise!"',
            f'{agent.name} waves enthusiastically at {friend.name}: "There you are!"',
            f'{agent.name} smiles broadly at {friend.name}: "Always a pleasure, my friend!"',
        ]
    elif charm >= 4:
        # Average charm - friendly but measured
        greetings = [
            f'{agent.name} nods at {friend.name}: "Good to see you."',
            f'{agent.name} greets {friend.name}: "Hello there, friend."',
            f'{agent.name} waves at {friend.name}: "Fancy meeting you here."',
        ]
    else:
        # Low charm - awkward but genuine
        greetings = [
            f"{agent.name} gives {friend.name} an awkward but sincere wave",
            f'{agent.name} mumbles at {friend.name}: "Oh, um, hello..."',
            f"{agent.name} nods stiffly but with warmth at {friend.name}",
        ]
    return random.choice(greetings)


def _rival_acknowledgment(agent: Agent, rival: Agent, charm: int) -> str:
    """Generate a cold acknowledgment for a rival."""
    if charm >= 7:
        # High charm - icy politeness
        acknowledgments = [
            f'{agent.name} regards {rival.name} coolly: "Ah. You\'re here."',
            f"{agent.name} offers {rival.name} a thin, polite smile",
            f'{agent.name} nods curtly at {rival.name}: "Good day."',
        ]
    elif charm >= 4:
        # Average charm - barely civil
        acknowledgments = [
            f"{agent.name} barely acknowledges {rival.name} with a glance",
            f'{agent.name} mutters at {rival.name}: "Oh. It\'s you."',
            f"{agent.name} gives {rival.name} a pointed look",
        ]
    else:
        # Low charm - openly awkward hostility
        acknowledgments = [
            f"{agent.name} stiffens upon seeing {rival.name}",
            f"{agent.name} avoids eye contact with {rival.name}",
            f"{agent.name} grimaces slightly at the sight of {rival.name}",
        ]
    return random.choice(acknowledgments)


def _acquaintance_greeting(agent: Agent, acquaintance: Agent, charm: int) -> str:
    """Generate a casual greeting for an acquaintance."""
    if charm >= 7:
        greetings = [
            f'{agent.name} greets {acquaintance.name} pleasantly: "Hello!"',
            f'{agent.name} smiles at {acquaintance.name}: "Nice to see you."',
            f'{agent.name} tips their head at {acquaintance.name}: "Good day to you."',
        ]
    elif charm >= 4:
        greetings = [
            f"{agent.name} nods at {acquaintance.name}",
            f'{agent.name} acknowledges {acquaintance.name}: "Hello."',
            f"{agent.name} offers {acquaintance.name} a brief wave",
        ]
    else:
        greetings = [
            f"{agent.name} gives {acquaintance.name} an uncertain nod",
            f'{agent.name} mutters a greeting to {acquaintance.name}',
            f"{agent.name} glances awkwardly at {acquaintance.name}",
        ]
    return random.choice(greetings)


def _stranger_greeting(
    agent: Agent, stranger: Agent, charm: int, perception: AgentPerception
) -> str:
    """Generate a greeting for a stranger, possibly location-aware."""
    location = perception.location_name.lower()

    # Location-specific greetings for high charm
    if charm >= 7:
        if "tavern" in location:
            greetings = [
                f'{agent.name} calls out to the room: "Good evening, everyone!"',
                f'{agent.name} surveys the tavern and nods: "A fine gathering tonight."',
            ]
        elif "church" in location:
            greetings = [
                f"{agent.name} enters quietly and nods respectfully to those present",
                f'{agent.name} whispers a soft: "Blessings upon you all."',
            ]
        elif "square" in location or "market" in location:
            greetings = [
                f'{agent.name} waves to the assembled crowd: "Lovely day, isn\'t it?"',
                f"{agent.name} greets the gathered villagers with a warm smile",
            ]
        else:
            greetings = [
                f'{agent.name} announces their arrival: "Hello there!"',
                f'{agent.name} greets {stranger.name} with a friendly: "Good day!"',
            ]
    elif charm >= 4:
        greetings = [
            f"{agent.name} nods at {stranger.name} upon entering",
            f'{agent.name} offers a polite: "Hello."',
            f"{agent.name} acknowledges the others present",
        ]
    else:
        # Low charm - awkward entrance
        greetings = [
            f"{agent.name} shuffles in without making eye contact",
            f"{agent.name} enters hesitantly, avoiding attention",
            f'{agent.name} mumbles something that might be: "Hello..."',
        ]
    return random.choice(greetings)
