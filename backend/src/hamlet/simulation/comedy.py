"""Situational comedy detection for absurd situations.

Detects when events create comedic or absurd situations and generates
appropriate humorous reactions for witty witnesses (high charm/curiosity).
"""

import random
from dataclasses import dataclass

from hamlet.db import Agent, Relationship


@dataclass
class AbsurdSituation:
    """Represents a detected absurd/comedic situation."""

    situation_type: str
    description: str
    comedy_level: int  # 1-10, how funny is this situation


def detect_absurd_situation(
    event_type: str,
    actor: Agent,
    target: Agent | None,
    relationship: Relationship | None,
    context: dict | None = None,
) -> AbsurdSituation | None:
    """Detect if an event creates an absurd or comedic situation.

    Args:
        event_type: Type of action/event (e.g., 'help', 'confront', 'give')
        actor: The agent performing the action
        target: The target agent (if social action)
        relationship: The relationship between actor and target
        context: Additional context about the situation

    Returns:
        An AbsurdSituation if the situation is comedic, None otherwise
    """
    context = context or {}

    # === RIVALS BEING NICE ===
    # When enemies/rivals help each other or give gifts
    if relationship and relationship.score <= -5:
        if event_type == "help":
            return AbsurdSituation(
                situation_type="rivals_helping",
                description=f"{actor.name} is helping their nemesis {target.name}",
                comedy_level=8,
            )
        elif event_type == "give":
            return AbsurdSituation(
                situation_type="rivals_generous",
                description=f"{actor.name} is giving a gift to {target.name}, whom they despise",
                comedy_level=7,
            )
        elif event_type == "greet":
            return AbsurdSituation(
                situation_type="rivals_civil",
                description=f"{actor.name} is being polite to their rival {target.name}",
                comedy_level=5,
            )

    # === FRIENDS FIGHTING ===
    # When close friends have confrontations
    if relationship and relationship.score >= 7:
        if event_type == "confront":
            return AbsurdSituation(
                situation_type="friends_fighting",
                description=f"Best friends {actor.name} and {target.name} are having a confrontation",
                comedy_level=7,
            )
        elif event_type == "avoid":
            return AbsurdSituation(
                situation_type="friends_avoiding",
                description=f"{actor.name} is avoiding their close friend {target.name}",
                comedy_level=6,
            )
        elif event_type == "gossip":
            # Gossiping about a friend to someone else
            subject_id = context.get("subject_id")
            if subject_id and target:
                return AbsurdSituation(
                    situation_type="friends_gossiping",
                    description=f"{actor.name} is spreading gossip about their friend",
                    comedy_level=6,
                )

    # === AWKWARD TIMING ===
    # Greeting someone you just saw
    if event_type == "greet" and context.get("just_greeted"):
        return AbsurdSituation(
            situation_type="repeated_greeting",
            description=f"{actor.name} is greeting {target.name} again after just seeing them",
            comedy_level=5,
        )

    # === INVESTIGATING THE OBVIOUS ===
    if event_type == "investigate":
        mystery = context.get("mystery", "")
        obvious_things = ["weather", "sun", "sky", "ground", "nothing", "air"]
        if any(obvious in mystery.lower() for obvious in obvious_things):
            return AbsurdSituation(
                situation_type="investigating_obvious",
                description=f"{actor.name} is seriously investigating '{mystery}'",
                comedy_level=7,
            )

    # === TALKING WHEN ALONE ===
    if event_type == "talk" and context.get("alone"):
        return AbsurdSituation(
            situation_type="talking_alone",
            description=f"{actor.name} appears to be talking to themselves",
            comedy_level=6,
        )

    # === SLEEPING AT WRONG TIME ===
    if event_type == "sleep":
        # Check just_woke_up first (higher comedy value)
        if context.get("just_woke_up"):
            return AbsurdSituation(
                situation_type="sleep_immediately",
                description=f"{actor.name} just woke up and is going back to sleep",
                comedy_level=8,
            )
        hour = context.get("hour", 12)
        if 8 <= hour <= 18:  # Sleeping during the day
            return AbsurdSituation(
                situation_type="day_sleeper",
                description=f"{actor.name} is going to sleep in the middle of the day",
                comedy_level=5,
            )

    # === FAILED ROMANTIC GESTURE ===
    if event_type in ("give", "help", "confess") and context.get("romantic_intent"):
        if relationship and relationship.score <= 0:
            return AbsurdSituation(
                situation_type="awkward_romance",
                description=f"{actor.name} is making romantic advances to someone uninterested",
                comedy_level=7,
            )

    # === EXCESSIVE EXAMINING ===
    if event_type == "examine" and context.get("examined_before"):
        target_obj = context.get("target_object", "something")
        return AbsurdSituation(
            situation_type="over_examining",
            description=f"{actor.name} is examining the {target_obj} yet again",
            comedy_level=4,
        )

    return None


def generate_witty_reaction(
    witness: Agent,
    situation: AbsurdSituation,
    actors: list[str],
) -> str | None:
    """Generate a humorous reaction for a witty witness to an absurd situation.

    Only generates reactions for agents with high charm (>=7) or high curiosity (>=7).

    Args:
        witness: The agent witnessing the absurd situation
        situation: The detected absurd situation
        actors: Names of the agents involved

    Returns:
        A witty reaction string, or None if witness isn't witty enough
    """
    traits = witness.traits_dict
    charm = traits.get("charm", 5)
    curiosity = traits.get("curiosity", 5)
    name = witness.name

    # Only witty agents react humorously
    if charm < 7 and curiosity < 7:
        return None

    # Lower comedy situations need higher wit to notice
    if situation.comedy_level < 5 and charm < 8 and curiosity < 8:
        return None

    # Build reaction options based on situation type and witness traits
    reactions: list[tuple[str, int]] = []

    # === RIVALS BEING NICE ===
    if situation.situation_type == "rivals_helping":
        if charm >= 8:
            reactions.extend([
                (f"{name} stifles a laugh at the unlikely alliance", 4),
                (f'{name} mutters "Did I just see that?" with an amused smirk', 3),
                (f"{name}'s eyebrows shoot up in theatrical surprise", 3),
            ])
        if curiosity >= 8:
            reactions.extend([
                (f"{name} watches with fascinated disbelief", 3),
                (f"{name} leans in, clearly thinking 'this should be good'", 3),
            ])
        reactions.extend([
            (f"{name} does a visible double-take", 3),
            (f"{name} bites their lip to keep from smiling", 2),
        ])

    elif situation.situation_type == "rivals_generous":
        if charm >= 8:
            reactions.extend([
                (f'{name} whispers "The apocalypse must be near"', 4),
                (f"{name} pretends to check for a hidden camera", 3),
            ])
        reactions.extend([
            (f"{name} blinks several times in disbelief", 3),
            (f"{name} exchanges a knowing look with no one", 2),
        ])

    elif situation.situation_type == "rivals_civil":
        reactions.extend([
            (f"{name} raises an eyebrow at the forced politeness", 3),
            (f"{name} watches the awkward exchange with mild amusement", 2),
        ])

    # === FRIENDS FIGHTING ===
    elif situation.situation_type == "friends_fighting":
        if charm >= 8:
            reactions.extend([
                (f'{name} stage-whispers "Trouble in paradise"', 4),
                (f"{name} settles in as if watching theater", 3),
            ])
        if curiosity >= 8:
            reactions.extend([
                (f"{name} edges closer with undisguised interest", 3),
            ])
        reactions.extend([
            (f"{name} winces at the unexpected drama", 3),
            (f"{name} looks around to see if others are seeing this too", 2),
        ])

    elif situation.situation_type == "friends_avoiding":
        reactions.extend([
            (f"{name} notices the awkward dodge with amusement", 3),
            (f"{name} suppresses a knowing smile", 2),
        ])

    # === INVESTIGATING THE OBVIOUS ===
    elif situation.situation_type == "investigating_obvious":
        if charm >= 8:
            reactions.extend([
                (f'{name} mutters "Ah yes, the great mystery of..." with a smirk', 4),
                (f"{name} adopts an exaggerated look of scholarly interest", 3),
            ])
        if curiosity >= 8:
            reactions.extend([
                (f"{name} wonders aloud what profound discovery awaits", 3),
            ])
        reactions.extend([
            (f"{name} watches with bemused curiosity", 2),
        ])

    # === TALKING ALONE ===
    elif situation.situation_type == "talking_alone":
        if charm >= 8:
            reactions.extend([
                (f"{name} glances around for the invisible conversation partner", 4),
                (f'{name} nods along as if following the solo conversation', 3),
            ])
        reactions.extend([
            (f"{name} politely pretends not to notice", 2),
            (f"{name} gives them some extra space", 2),
        ])

    # === SLEEP TIMING ===
    elif situation.situation_type == "day_sleeper":
        if charm >= 8:
            reactions.extend([
                (f'{name} quips "Rough night?" under their breath', 4),
            ])
        reactions.extend([
            (f"{name} glances at the sun, then back at the sleeper", 3),
        ])

    elif situation.situation_type == "sleep_immediately":
        if charm >= 8:
            reactions.extend([
                (f'{name} whispers "That was a quick day"', 4),
                (f"{name} checks if they missed something", 3),
            ])
        reactions.extend([
            (f"{name} does a comedic double-take", 3),
        ])

    # === AWKWARD ROMANCE ===
    elif situation.situation_type == "awkward_romance":
        if charm >= 8:
            reactions.extend([
                (f"{name} winces sympathetically at the attempt", 4),
                (f'{name} mutters "Oh no..." with secondhand embarrassment', 3),
            ])
        reactions.extend([
            (f"{name} suddenly finds something else very interesting to look at", 3),
        ])

    # === REPEATED GREETING ===
    elif situation.situation_type == "repeated_greeting":
        if charm >= 8:
            reactions.extend([
                (f'{name} thinks "Didn\'t they just...?" with a smile', 3),
            ])
        reactions.extend([
            (f"{name} suppresses a small smile at the repetition", 2),
        ])

    # === OVER EXAMINING ===
    elif situation.situation_type == "over_examining":
        if curiosity >= 8:
            reactions.extend([
                (f"{name} wonders what secrets the object might yet reveal", 3),
            ])
        reactions.extend([
            (f"{name} glances at the well-examined object with amusement", 2),
        ])

    # === GOSSIPING ABOUT FRIENDS ===
    elif situation.situation_type == "friends_gossiping":
        if charm >= 8:
            reactions.extend([
                (f'{name} mentally files this under "interesting"', 3),
                (f"{name} raises an eyebrow at the betrayal", 3),
            ])
        reactions.extend([
            (f"{name} pretends very hard not to have heard that", 2),
        ])

    # Default fallback for any absurd situation
    if not reactions:
        if charm >= 7:
            reactions.append((f"{name} smirks at the absurdity", 2))
        if curiosity >= 7:
            reactions.append((f"{name} watches with amused interest", 2))

    # Weighted random selection
    if reactions:
        options, weights = zip(*reactions)
        return random.choices(options, weights=weights, k=1)[0]

    return None


def is_witty_agent(agent: Agent) -> bool:
    """Check if an agent is witty enough to make humorous observations.

    An agent is considered witty if they have high charm (>=7) or
    high curiosity (>=7).

    Args:
        agent: The agent to check

    Returns:
        True if the agent is witty, False otherwise
    """
    traits = agent.traits_dict
    charm = traits.get("charm", 5)
    curiosity = traits.get("curiosity", 5)
    return charm >= 7 or curiosity >= 7
