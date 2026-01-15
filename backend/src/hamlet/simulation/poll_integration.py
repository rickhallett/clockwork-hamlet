"""Poll-simulation integration for POLL-8 and POLL-10.

POLL-8: Poll results trigger reactive goals (winning option creates agent goals)
POLL-10: Memory creation for votes (agents remember what they voted for)

This module integrates the polling system with the agent simulation:
- Creates memories when agents vote
- Creates memories when polls close
- Creates reactive goals based on poll results
- Publishes simulation events for poll lifecycle
"""

import logging
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from hamlet.db import Agent, Goal, Poll
from hamlet.goals.generation import generate_reactive_goal
from hamlet.goals.types import CATEGORY_BASE_PRIORITY, GoalCategory, GoalType
from hamlet.memory.manager import add_memory
from hamlet.memory.types import MemoryType
from hamlet.simulation.events import EventType, SimulationEvent, event_bus
from hamlet.simulation.polls import VoteDecision, get_voting_summary

logger = logging.getLogger(__name__)


@dataclass
class PollResult:
    """Result of a closed poll."""

    poll_id: int
    question: str
    winning_option: str
    winning_index: int
    total_votes: int
    vote_counts: dict[str, int]
    category: str | None


def get_poll_result(poll: Poll) -> PollResult:
    """Extract the result from a closed poll.

    Args:
        poll: The closed poll

    Returns:
        PollResult with winning option and vote breakdown
    """
    options = poll.options_list
    votes = poll.votes_dict

    # Find the winning option (most votes)
    max_votes = 0
    winning_index = 0
    for idx_str, count in votes.items():
        if count > max_votes:
            max_votes = count
            winning_index = int(idx_str)

    # Build vote counts by option text
    vote_counts = {}
    for idx_str, count in votes.items():
        idx = int(idx_str)
        if idx < len(options):
            vote_counts[options[idx]] = count

    total_votes = sum(votes.values())

    return PollResult(
        poll_id=poll.id,
        question=poll.question,
        winning_option=options[winning_index] if options else "",
        winning_index=winning_index,
        total_votes=total_votes,
        vote_counts=vote_counts,
        category=poll.category,
    )


def create_vote_memory(
    agent: Agent,
    decision: VoteDecision,
    poll: Poll,
    db: Session,
) -> None:
    """Create a memory for an agent's vote (POLL-10).

    The memory captures what the agent voted for and how confident
    they felt about their choice. This allows agents to discuss
    and reference their voting decisions later.

    Args:
        agent: The agent who voted
        decision: The vote decision with option and confidence
        poll: The poll that was voted on
        db: Database session
    """
    # Determine memory significance based on confidence
    # High confidence = stronger opinion = more significant memory
    if decision.confidence >= 0.7:
        significance = 6  # Strong opinion, memorable
    elif decision.confidence >= 0.4:
        significance = 5  # Moderate opinion
    else:
        significance = 4  # Mild preference

    # Create descriptive memory content
    confidence_desc = ""
    if decision.confidence >= 0.8:
        confidence_desc = "strongly"
    elif decision.confidence >= 0.5:
        confidence_desc = "confidently"
    elif decision.confidence >= 0.3:
        confidence_desc = ""
    else:
        confidence_desc = "hesitantly"

    if confidence_desc:
        content = (
            f"I {confidence_desc} voted for '{decision.option_text}' "
            f"on the poll: \"{poll.question}\""
        )
    else:
        content = (
            f"I voted for '{decision.option_text}' "
            f"on the poll: \"{poll.question}\""
        )

    add_memory(
        agent_id=agent.id,
        content=content,
        db=db,
        memory_type=MemoryType.WORKING,
        significance=significance,
        event_type="action",
    )

    logger.info(f"Created vote memory for {agent.name}: {content}")


def create_poll_result_memories(
    agents: list[Agent],
    result: PollResult,
    agent_votes: dict[str, int],
    db: Session,
) -> None:
    """Create memories for all agents about the poll result (POLL-10).

    Each agent remembers the poll result and whether their choice won.

    Args:
        agents: All agents who should remember the result
        result: The poll result
        agent_votes: Map of agent_id -> option_index they voted for
        db: Database session
    """
    for agent in agents:
        # Check if this agent voted and if they won
        voted_option = agent_votes.get(agent.id)

        if voted_option is not None:
            # Agent participated in the poll
            if voted_option == result.winning_index:
                content = (
                    f"The poll \"{result.question}\" concluded. "
                    f"My choice '{result.winning_option}' won with "
                    f"{result.vote_counts.get(result.winning_option, 0)} votes!"
                )
                significance = 7  # Winning feels significant
            else:
                # Find what they voted for
                options = list(result.vote_counts.keys())
                their_choice = options[voted_option] if voted_option < len(options) else "unknown"
                content = (
                    f"The poll \"{result.question}\" concluded. "
                    f"'{result.winning_option}' won. "
                    f"I had voted for '{their_choice}'."
                )
                significance = 6  # Losing is still notable
        else:
            # Agent didn't vote - still aware of the result
            content = (
                f"The poll \"{result.question}\" concluded. "
                f"'{result.winning_option}' won with {result.total_votes} total votes."
            )
            significance = 5  # Less personally relevant

        add_memory(
            agent_id=agent.id,
            content=content,
            db=db,
            memory_type=MemoryType.WORKING,
            significance=significance,
            event_type="discovery",
        )

    logger.info(f"Created poll result memories for {len(agents)} agents")


def create_poll_reactive_goals(
    agents: list[Agent],
    result: PollResult,
    agent_votes: dict[str, int],
    db: Session,
) -> list[Goal]:
    """Create reactive goals for agents based on poll results (POLL-8).

    Different goals are created based on:
    - Whether the agent's choice won or lost
    - The poll category (governance, social, etc.)
    - The agent's personality traits

    Args:
        agents: All agents
        result: The poll result
        agent_votes: Map of agent_id -> option_index they voted for
        db: Database session

    Returns:
        List of created goals
    """
    created_goals = []
    now = int(time.time())

    for agent in agents:
        voted_option = agent_votes.get(agent.id)
        traits = agent.traits_dict

        # Base priority for poll-related goals
        base_priority = CATEGORY_BASE_PRIORITY[GoalCategory.REACTIVE]

        if voted_option is not None:
            agent_won = voted_option == result.winning_index

            if agent_won:
                # Create celebration goal for winners with high energy/charm
                if traits.get("energy", 5) >= 6 or traits.get("charm", 5) >= 6:
                    goal = Goal(
                        agent_id=agent.id,
                        type=GoalType.CELEBRATE_POLL_WIN.value,
                        description=(
                            f"Celebrate that '{result.winning_option}' "
                            f"won the poll about \"{result.question}\""
                        ),
                        priority=base_priority + 1,
                        status="active",
                        created_at=now,
                    )
                    db.add(goal)
                    created_goals.append(goal)
            else:
                # Create acceptance goal for losers with high empathy
                # Or confrontation if they have high ambition and low empathy
                if traits.get("ambition", 5) >= 7 and traits.get("empathy", 5) < 5:
                    # Ambitious agents might want to discuss/debate the result
                    goal = Goal(
                        agent_id=agent.id,
                        type=GoalType.DISCUSS_POLL_RESULT.value,
                        description=(
                            f"Discuss the poll result - why did "
                            f"'{result.winning_option}' win?"
                        ),
                        priority=base_priority + 2,  # Higher priority for debate
                        status="active",
                        created_at=now,
                    )
                    db.add(goal)
                    created_goals.append(goal)
                elif traits.get("empathy", 5) >= 5:
                    # Empathetic agents accept the result gracefully
                    goal = Goal(
                        agent_id=agent.id,
                        type=GoalType.ACCEPT_POLL_LOSS.value,
                        description=(
                            f"Accept that '{result.winning_option}' won "
                            f"the poll, even though I voted differently"
                        ),
                        priority=base_priority,
                        status="active",
                        created_at=now,
                    )
                    db.add(goal)
                    created_goals.append(goal)

        # Create implementation goals for governance/action-oriented polls
        # Only for a subset of agents (leaders, ambitious ones)
        if result.category in ("governance", "conflict", "exploration"):
            if traits.get("ambition", 5) >= 7 or traits.get("courage", 5) >= 7:
                goal = Goal(
                    agent_id=agent.id,
                    type=GoalType.IMPLEMENT_POLL_DECISION.value,
                    description=(
                        f"Help implement the decision: '{result.winning_option}'"
                    ),
                    priority=base_priority + 2,
                    status="active",
                    created_at=now,
                )
                db.add(goal)
                created_goals.append(goal)

        # Create gossip goals for agents with low discretion
        if traits.get("discretion", 5) <= 4:
            goal = Goal(
                agent_id=agent.id,
                type=GoalType.SHARE_GOSSIP.value,
                description=(
                    f"Share news about the poll result - "
                    f"'{result.winning_option}' won!"
                ),
                priority=base_priority,
                status="active",
                created_at=now,
            )
            db.add(goal)
            created_goals.append(goal)

    db.commit()
    logger.info(f"Created {len(created_goals)} reactive goals from poll result")
    return created_goals


async def publish_poll_closed_event(
    result: PollResult,
    agent_votes: dict[str, int],
) -> None:
    """Publish a simulation event for poll closure.

    Args:
        result: The poll result
        agent_votes: Map of agent_id -> option_index (for actors list)
    """
    event = SimulationEvent(
        type=EventType.POLL,
        summary=(
            f"Poll closed: \"{result.question}\" - "
            f"'{result.winning_option}' wins with "
            f"{result.vote_counts.get(result.winning_option, 0)} votes"
        ),
        timestamp=int(time.time()),
        actors=list(agent_votes.keys()),  # All agents who voted
        significance=2,  # Notable event
        data={
            "poll_id": result.poll_id,
            "question": result.question,
            "winning_option": result.winning_option,
            "winning_index": result.winning_index,
            "total_votes": result.total_votes,
            "vote_counts": result.vote_counts,
            "category": result.category,
        },
    )
    await event_bus.publish(event)
    logger.info(f"Published poll closed event for poll {result.poll_id}")


async def publish_agent_voted_event(
    agent: Agent,
    decision: VoteDecision,
    poll: Poll,
) -> None:
    """Publish a simulation event when an agent votes.

    Args:
        agent: The agent who voted
        decision: Their voting decision
        poll: The poll they voted on
    """
    confidence_desc = ""
    if decision.confidence >= 0.7:
        confidence_desc = "confidently "
    elif decision.confidence <= 0.3:
        confidence_desc = "hesitantly "

    event = SimulationEvent(
        type=EventType.POLL,
        summary=(
            f"{agent.name} {confidence_desc}voted for "
            f"'{decision.option_text}'"
        ),
        timestamp=int(time.time()),
        actors=[agent.id],
        significance=1,  # Minor event
        data={
            "poll_id": poll.id,
            "agent_id": agent.id,
            "option_index": decision.option_index,
            "option_text": decision.option_text,
            "confidence": decision.confidence,
        },
    )
    await event_bus.publish(event)


async def on_poll_closed(
    poll: Poll,
    db: Session,
    agent_votes: dict[str, int] | None = None,
) -> PollResult:
    """Handle poll closure - create memories, goals, and events.

    This is the main entry point called when a poll closes.
    It orchestrates POLL-8 and POLL-10 functionality.

    Args:
        poll: The poll that just closed
        db: Database session
        agent_votes: Optional pre-computed map of agent_id -> option_index.
                     If None, we can't create personalized memories.

    Returns:
        The poll result
    """
    logger.info(f"Processing poll closure for poll {poll.id}: {poll.question}")

    # Get the result
    result = get_poll_result(poll)

    # Get all agents
    agents = db.query(Agent).all()

    # If we don't have agent_votes, create empty dict (no personalized memories)
    if agent_votes is None:
        agent_votes = {}
        logger.warning(
            "No agent_votes provided for poll closure - "
            "personalized memories will be limited"
        )

    # POLL-10: Create memories for all agents about the result
    create_poll_result_memories(agents, result, agent_votes, db)

    # POLL-8: Create reactive goals based on the result
    create_poll_reactive_goals(agents, result, agent_votes, db)

    # Publish simulation event
    await publish_poll_closed_event(result, agent_votes)

    return result


def on_agent_vote_sync(
    agent: Agent,
    decision: VoteDecision,
    poll: Poll,
    db: Session,
) -> None:
    """Synchronous handler for when an agent votes (POLL-10).

    Creates a memory for the vote. Use this when you can't await.

    Args:
        agent: The agent who voted
        decision: Their voting decision
        poll: The poll they voted on
        db: Database session
    """
    create_vote_memory(agent, decision, poll, db)


async def on_agent_vote(
    agent: Agent,
    decision: VoteDecision,
    poll: Poll,
    db: Session,
) -> None:
    """Async handler for when an agent votes (POLL-10).

    Creates a memory and publishes an event.

    Args:
        agent: The agent who voted
        decision: Their voting decision
        poll: The poll they voted on
        db: Database session
    """
    # Create the memory (POLL-10)
    create_vote_memory(agent, decision, poll, db)

    # Publish event
    await publish_agent_voted_event(agent, decision, poll)
