"""Agent voting simulation - agents vote on polls based on personality traits.

POLL-9: Implement agent voting based on traits
POLL-10: Memory creation for votes (integration)

This module provides functionality for agents to vote on polls probabilistically
based on their personality traits. Different poll categories and option keywords
map to different traits, creating emergent voting patterns that reflect
each agent's unique personality.
"""

import logging
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from sqlalchemy.orm import Session

from hamlet.db import Agent, Poll

if TYPE_CHECKING:
    from hamlet.simulation.poll_integration import on_agent_vote_sync

logger = logging.getLogger(__name__)


# Trait weights for different poll categories
# Higher weight = trait has more influence on voting behavior
CATEGORY_TRAIT_WEIGHTS: dict[str, dict[str, float]] = {
    "governance": {
        "ambition": 0.3,
        "empathy": 0.2,
        "discretion": 0.2,
        "courage": 0.15,
        "charm": 0.15,
    },
    "social": {
        "empathy": 0.35,
        "charm": 0.25,
        "discretion": 0.2,
        "curiosity": 0.2,
    },
    "exploration": {
        "curiosity": 0.35,
        "courage": 0.3,
        "energy": 0.2,
        "perception": 0.15,
    },
    "mystery": {
        "curiosity": 0.3,
        "perception": 0.25,
        "courage": 0.25,
        "discretion": 0.2,
    },
    "conflict": {
        "courage": 0.3,
        "ambition": 0.25,
        "empathy": 0.25,
        "discretion": 0.2,
    },
    "celebration": {
        "charm": 0.3,
        "energy": 0.3,
        "empathy": 0.2,
        "ambition": 0.2,
    },
}

# Default weights when category is unknown
DEFAULT_TRAIT_WEIGHTS: dict[str, float] = {
    "curiosity": 0.15,
    "empathy": 0.15,
    "ambition": 0.1,
    "discretion": 0.1,
    "energy": 0.1,
    "courage": 0.15,
    "charm": 0.15,
    "perception": 0.1,
}

# Keywords in poll options that influence trait-based voting
# Format: keyword -> (trait, positive_influence)
# positive_influence True means high trait = more likely to vote for this option
OPTION_KEYWORDS: dict[str, tuple[str, bool]] = {
    # Curiosity-related
    "investigate": ("curiosity", True),
    "explore": ("curiosity", True),
    "discover": ("curiosity", True),
    "learn": ("curiosity", True),
    "ignore": ("curiosity", False),
    "leave alone": ("curiosity", False),
    # Courage-related
    "confront": ("courage", True),
    "fight": ("courage", True),
    "brave": ("courage", True),
    "bold": ("courage", True),
    "retreat": ("courage", False),
    "avoid": ("courage", False),
    "hide": ("courage", False),
    "cautious": ("courage", False),
    # Empathy-related
    "help": ("empathy", True),
    "support": ("empathy", True),
    "comfort": ("empathy", True),
    "forgive": ("empathy", True),
    "care": ("empathy", True),
    "punish": ("empathy", False),
    # Ambition-related
    "lead": ("ambition", True),
    "compete": ("ambition", True),
    "win": ("ambition", True),
    "achieve": ("ambition", True),
    "power": ("ambition", True),
    "accept": ("ambition", False),
    "settle": ("ambition", False),
    # Discretion-related
    "secret": ("discretion", True),
    "private": ("discretion", True),
    "quiet": ("discretion", True),
    "public": ("discretion", False),
    "announce": ("discretion", False),
    "reveal": ("discretion", False),
    # Energy-related
    "active": ("energy", True),
    "energetic": ("energy", True),
    "party": ("energy", True),
    "celebrate": ("energy", True),
    "rest": ("energy", False),
    "wait": ("energy", False),
    "passive": ("energy", False),
    # Charm-related
    "persuade": ("charm", True),
    "charm": ("charm", True),
    "negotiate": ("charm", True),
    "diplomatic": ("charm", True),
    "force": ("charm", False),
    # Perception-related
    "observe": ("perception", True),
    "watch": ("perception", True),
    "notice": ("perception", True),
    "analyze": ("perception", True),
}


@dataclass
class VoteDecision:
    """Result of an agent's voting decision."""

    agent_id: str
    poll_id: int
    option_index: int
    option_text: str
    confidence: float  # 0-1, how strongly they felt about this choice


def get_trait_weights(category: str | None) -> dict[str, float]:
    """Get trait weights for a poll category.

    Args:
        category: Poll category (e.g., "governance", "social", "exploration")

    Returns:
        Dictionary mapping trait names to their influence weights
    """
    if category and category.lower() in CATEGORY_TRAIT_WEIGHTS:
        return CATEGORY_TRAIT_WEIGHTS[category.lower()]
    return DEFAULT_TRAIT_WEIGHTS


def analyze_option_text(option_text: str) -> list[tuple[str, bool]]:
    """Analyze option text for keywords that influence voting.

    Args:
        option_text: The text of a poll option

    Returns:
        List of (trait, positive_influence) tuples found in the text
    """
    text_lower = option_text.lower()
    influences = []

    for keyword, (trait, positive) in OPTION_KEYWORDS.items():
        if keyword in text_lower:
            influences.append((trait, positive))

    return influences


def calculate_option_score(
    agent: Agent,
    option_text: str,
    trait_weights: dict[str, float],
) -> float:
    """Calculate an agent's affinity score for a poll option.

    The score combines:
    1. Category-based trait influence (general polling tendencies)
    2. Keyword-based trait influence (specific option appeal)

    Args:
        agent: The agent voting
        option_text: Text of the poll option
        trait_weights: Weights for traits based on poll category

    Returns:
        Score from 0-1 indicating affinity for this option
    """
    traits = agent.traits_dict

    # Base score from category trait weights
    # Normalized trait values (1-10) to 0-1 range
    base_score = 0.0
    for trait, weight in trait_weights.items():
        trait_value = traits.get(trait, 5) / 10.0  # Normalize to 0-1
        base_score += trait_value * weight

    # Adjust based on keywords in the option
    keyword_influences = analyze_option_text(option_text)
    keyword_adjustment = 0.0

    for trait, positive in keyword_influences:
        trait_value = traits.get(trait, 5) / 10.0
        if positive:
            # High trait = bonus for this option
            keyword_adjustment += (trait_value - 0.5) * 0.15
        else:
            # High trait = penalty for this option
            keyword_adjustment -= (trait_value - 0.5) * 0.15

    # Combine scores (base has more weight)
    final_score = base_score * 0.7 + (0.5 + keyword_adjustment) * 0.3

    # Clamp to valid range
    return max(0.0, min(1.0, final_score))


def calculate_vote_probabilities(
    agent: Agent,
    poll: Poll,
) -> list[float]:
    """Calculate probability distribution over poll options for an agent.

    Args:
        agent: The agent who will vote
        poll: The poll to vote on

    Returns:
        List of probabilities for each option (sums to 1.0)
    """
    options = poll.options_list
    if not options:
        return []

    trait_weights = get_trait_weights(poll.category)

    # Calculate raw scores for each option
    scores = [
        calculate_option_score(agent, option, trait_weights) for option in options
    ]

    # Add small random noise for variety (agents aren't perfectly predictable)
    noise_factor = 0.1
    scores = [s + random.uniform(-noise_factor, noise_factor) for s in scores]
    scores = [max(0.01, s) for s in scores]  # Ensure positive

    # Normalize to probabilities
    total = sum(scores)
    if total == 0:
        # Equal probability if all scores are 0
        return [1.0 / len(options)] * len(options)

    return [s / total for s in scores]


def decide_vote(agent: Agent, poll: Poll) -> VoteDecision:
    """Have an agent decide how to vote on a poll.

    The decision is probabilistic based on the agent's personality traits.
    Agents with certain traits are more likely to vote for options that
    align with those traits.

    Args:
        agent: The agent voting
        poll: The poll to vote on

    Returns:
        VoteDecision with the chosen option and confidence level
    """
    options = poll.options_list
    if not options:
        raise ValueError(f"Poll {poll.id} has no options")

    # Calculate probabilities
    probabilities = calculate_vote_probabilities(agent, poll)

    # Make weighted random choice
    chosen_index = random.choices(range(len(options)), weights=probabilities, k=1)[0]
    chosen_prob = probabilities[chosen_index]

    # Confidence is how strongly they preferred this option
    # High if they had a clear preference, low if options were similar
    max_prob = max(probabilities)
    avg_prob = 1.0 / len(options)
    confidence = min(1.0, (max_prob - avg_prob) / avg_prob) if max_prob > avg_prob else 0.0

    return VoteDecision(
        agent_id=agent.id,
        poll_id=poll.id,
        option_index=chosen_index,
        option_text=options[chosen_index],
        confidence=confidence,
    )


def process_agent_votes(
    db: Session,
    poll: Poll,
    agents: list[Agent] | None = None,
    create_memories: bool = True,
) -> tuple[list[VoteDecision], dict[str, int]]:
    """Process voting for all (or specified) agents on a poll.

    Each agent votes based on their personality traits. The votes are
    recorded in the poll's votes dictionary.

    POLL-10: When create_memories is True, also creates memories for each vote.

    Args:
        db: Database session
        poll: The poll to vote on
        agents: Optional list of specific agents to vote. If None, all agents vote.
        create_memories: Whether to create memories for votes (POLL-10)

    Returns:
        Tuple of (list of VoteDecision objects, dict mapping agent_id to option_index)
    """
    if poll.status != "active":
        logger.warning(f"Poll {poll.id} is not active, skipping agent voting")
        return [], {}

    if agents is None:
        agents = db.query(Agent).all()

    decisions: list[VoteDecision] = []
    agent_votes: dict[str, int] = {}  # Track what each agent voted for
    votes = poll.votes_dict

    # Import here to avoid circular imports
    if create_memories:
        from hamlet.simulation.poll_integration import on_agent_vote_sync

    for agent in agents:
        try:
            decision = decide_vote(agent, poll)
            decisions.append(decision)
            agent_votes[agent.id] = decision.option_index

            # Update vote count
            option_key = str(decision.option_index)
            votes[option_key] = votes.get(option_key, 0) + 1

            # POLL-10: Create memory for this vote
            if create_memories:
                on_agent_vote_sync(agent, decision, poll, db)

            logger.info(
                f"Agent {agent.name} voted for option {decision.option_index} "
                f"({decision.option_text}) with confidence {decision.confidence:.2f}"
            )
        except Exception as e:
            logger.error(f"Failed to process vote for agent {agent.id}: {e}")

    # Save updated votes
    poll.votes_dict = votes
    db.commit()

    return decisions, agent_votes


def get_voting_summary(decisions: list[VoteDecision]) -> dict:
    """Generate a summary of voting decisions.

    Args:
        decisions: List of voting decisions

    Returns:
        Summary dictionary with vote counts and analysis
    """
    if not decisions:
        return {"total_votes": 0, "option_counts": {}, "avg_confidence": 0.0}

    option_counts: dict[str, int] = {}
    total_confidence = 0.0

    for decision in decisions:
        option_counts[decision.option_text] = option_counts.get(decision.option_text, 0) + 1
        total_confidence += decision.confidence

    return {
        "total_votes": len(decisions),
        "option_counts": option_counts,
        "avg_confidence": total_confidence / len(decisions),
        "winning_option": max(option_counts, key=option_counts.get) if option_counts else None,
    }
