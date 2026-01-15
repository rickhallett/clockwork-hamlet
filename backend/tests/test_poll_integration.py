"""Tests for poll-simulation integration (POLL-8 and POLL-10).

POLL-8: Poll results trigger reactive goals
POLL-10: Memory creation for votes
"""

import time

import pytest
from sqlalchemy.orm import Session

from hamlet.db import Agent, Goal, Memory, Poll
from hamlet.goals.types import GoalType
from hamlet.memory.types import MemoryType
from hamlet.simulation.poll_integration import (
    PollResult,
    create_poll_reactive_goals,
    create_poll_result_memories,
    create_vote_memory,
    get_poll_result,
    on_agent_vote_sync,
    on_poll_closed,
)
from hamlet.simulation.polls import VoteDecision, decide_vote, process_agent_votes


@pytest.fixture
def sample_agent(db: Session) -> Agent:
    """Create a sample agent for testing."""
    agent = Agent(
        id="test-agent-1",
        name="Test Agent",
        personality_prompt="A test agent",
        location_id="town_square",
        state="idle",
        hunger=5,
        energy=7,
        social=5,
    )
    agent.traits_dict = {
        "curiosity": 7,
        "empathy": 6,
        "ambition": 8,
        "discretion": 4,  # Low discretion = likely to gossip
        "energy": 7,
        "courage": 6,
        "charm": 7,
        "perception": 5,
    }
    db.add(agent)
    db.commit()
    return agent


@pytest.fixture
def sample_agents(db: Session) -> list[Agent]:
    """Create multiple sample agents for testing."""
    agents = []
    trait_configs = [
        {"ambition": 8, "empathy": 3, "discretion": 3, "energy": 8, "courage": 7},  # Ambitious, low empathy
        {"ambition": 4, "empathy": 8, "discretion": 7, "energy": 5, "courage": 4},  # Empathetic, reserved
        {"ambition": 5, "empathy": 5, "discretion": 2, "energy": 6, "courage": 8},  # Low discretion = gossip
    ]

    for i, traits in enumerate(trait_configs):
        agent = Agent(
            id=f"test-agent-{i+1}",
            name=f"Test Agent {i+1}",
            personality_prompt=f"Test agent {i+1}",
            location_id="town_square",
            state="idle",
            hunger=5,
            energy=7,
            social=5,
        )
        full_traits = {
            "curiosity": 5,
            "empathy": 5,
            "ambition": 5,
            "discretion": 5,
            "energy": 5,
            "courage": 5,
            "charm": 5,
            "perception": 5,
        }
        full_traits.update(traits)
        agent.traits_dict = full_traits
        db.add(agent)
        agents.append(agent)

    db.commit()
    return agents


@pytest.fixture
def sample_poll(db: Session) -> Poll:
    """Create a sample poll for testing."""
    poll = Poll(
        question="Should we investigate the mysterious cave?",
        status="active",
        category="exploration",
        created_at=int(time.time()),
    )
    poll.options_list = [
        "Yes, explore the cave",
        "No, it's too dangerous",
        "Send scouts first",
    ]
    poll.votes_dict = {}
    poll.tags_list = ["mystery", "exploration"]
    db.add(poll)
    db.commit()
    return poll


@pytest.fixture
def governance_poll(db: Session) -> Poll:
    """Create a governance poll for testing."""
    poll = Poll(
        question="Who should lead the village council?",
        status="active",
        category="governance",
        created_at=int(time.time()),
    )
    poll.options_list = [
        "Elder Marcus - the wise leader",
        "Young Ada - the innovative thinker",
        "Merchant Finn - the pragmatic choice",
    ]
    poll.votes_dict = {}
    poll.tags_list = ["governance", "leadership"]
    db.add(poll)
    db.commit()
    return poll


class TestPollResult:
    """Tests for get_poll_result function."""

    def test_get_poll_result_basic(self, db: Session, sample_poll: Poll):
        """Test extracting result from a poll."""
        # Set up votes
        sample_poll.votes_dict = {"0": 5, "1": 3, "2": 2}
        db.commit()

        result = get_poll_result(sample_poll)

        assert result.poll_id == sample_poll.id
        assert result.question == sample_poll.question
        assert result.winning_option == "Yes, explore the cave"
        assert result.winning_index == 0
        assert result.total_votes == 10
        assert result.category == "exploration"

    def test_get_poll_result_tie(self, db: Session, sample_poll: Poll):
        """Test result when there's a tie (first wins)."""
        sample_poll.votes_dict = {"0": 5, "1": 5, "2": 2}
        db.commit()

        result = get_poll_result(sample_poll)

        # First option with max votes wins
        assert result.winning_index == 0


class TestVoteMemoryCreation:
    """Tests for POLL-10: Memory creation when agents vote."""

    def test_create_vote_memory_high_confidence(
        self, db: Session, sample_agent: Agent, sample_poll: Poll
    ):
        """Test memory creation for a confident vote."""
        decision = VoteDecision(
            agent_id=sample_agent.id,
            poll_id=sample_poll.id,
            option_index=0,
            option_text="Yes, explore the cave",
            confidence=0.85,
        )

        create_vote_memory(sample_agent, decision, sample_poll, db)

        # Check memory was created
        memories = (
            db.query(Memory)
            .filter(Memory.agent_id == sample_agent.id)
            .all()
        )
        assert len(memories) == 1

        memory = memories[0]
        assert "strongly voted" in memory.content
        assert "Yes, explore the cave" in memory.content
        assert sample_poll.question in memory.content
        assert memory.significance == 6  # High confidence = significant

    def test_create_vote_memory_low_confidence(
        self, db: Session, sample_agent: Agent, sample_poll: Poll
    ):
        """Test memory creation for a hesitant vote."""
        decision = VoteDecision(
            agent_id=sample_agent.id,
            poll_id=sample_poll.id,
            option_index=1,
            option_text="No, it's too dangerous",
            confidence=0.2,
        )

        create_vote_memory(sample_agent, decision, sample_poll, db)

        memories = (
            db.query(Memory)
            .filter(Memory.agent_id == sample_agent.id)
            .all()
        )
        assert len(memories) == 1

        memory = memories[0]
        assert "hesitantly" in memory.content
        assert memory.significance == 4  # Low confidence = less significant

    def test_on_agent_vote_sync_creates_memory(
        self, db: Session, sample_agent: Agent, sample_poll: Poll
    ):
        """Test the sync vote handler creates memory."""
        decision = decide_vote(sample_agent, sample_poll)

        on_agent_vote_sync(sample_agent, decision, sample_poll, db)

        memories = (
            db.query(Memory)
            .filter(Memory.agent_id == sample_agent.id)
            .all()
        )
        assert len(memories) == 1
        assert decision.option_text in memories[0].content


class TestPollResultMemories:
    """Tests for POLL-10: Memory creation when polls close."""

    def test_create_poll_result_memories_winner(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test memory creation for agents who voted for winning option."""
        result = PollResult(
            poll_id=sample_poll.id,
            question=sample_poll.question,
            winning_option="Yes, explore the cave",
            winning_index=0,
            total_votes=10,
            vote_counts={"Yes, explore the cave": 5, "No, it's too dangerous": 3, "Send scouts first": 2},
            category="exploration",
        )

        # Agent 0 voted for the winner
        agent_votes = {sample_agents[0].id: 0, sample_agents[1].id: 1, sample_agents[2].id: 0}

        create_poll_result_memories(sample_agents, result, agent_votes, db)

        # Check winner memory
        winner_memories = (
            db.query(Memory)
            .filter(Memory.agent_id == sample_agents[0].id)
            .all()
        )
        assert len(winner_memories) == 1
        assert "My choice" in winner_memories[0].content
        assert "won" in winner_memories[0].content
        assert winner_memories[0].significance == 7  # Winners feel significant

        # Check loser memory
        loser_memories = (
            db.query(Memory)
            .filter(Memory.agent_id == sample_agents[1].id)
            .all()
        )
        assert len(loser_memories) == 1
        assert "I had voted for" in loser_memories[0].content
        assert loser_memories[0].significance == 6  # Still notable


class TestReactiveGoalCreation:
    """Tests for POLL-8: Poll results trigger reactive goals."""

    def test_create_celebration_goals_for_winners(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that winners with high energy/charm get celebration goals."""
        result = PollResult(
            poll_id=sample_poll.id,
            question=sample_poll.question,
            winning_option="Yes, explore the cave",
            winning_index=0,
            total_votes=10,
            vote_counts={"Yes, explore the cave": 5, "No, it's too dangerous": 3, "Send scouts first": 2},
            category="exploration",
        )

        # Agent 0 has high energy (8) and voted for winner
        agent_votes = {sample_agents[0].id: 0, sample_agents[1].id: 1}

        goals = create_poll_reactive_goals(sample_agents, result, agent_votes, db)

        # Check for celebration goal
        celebration_goals = [g for g in goals if g.type == GoalType.CELEBRATE_POLL_WIN.value]
        assert len(celebration_goals) >= 1

        # Find agent 0's celebration goal
        agent0_celebration = [g for g in celebration_goals if g.agent_id == sample_agents[0].id]
        assert len(agent0_celebration) == 1
        assert "Celebrate" in agent0_celebration[0].description

    def test_create_discussion_goals_for_ambitious_losers(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that ambitious losers want to discuss the result."""
        result = PollResult(
            poll_id=sample_poll.id,
            question=sample_poll.question,
            winning_option="No, it's too dangerous",
            winning_index=1,
            total_votes=10,
            vote_counts={"Yes, explore the cave": 3, "No, it's too dangerous": 5, "Send scouts first": 2},
            category="exploration",
        )

        # Agent 0 has high ambition (8), low empathy (3) and voted for option 0 (loser)
        agent_votes = {sample_agents[0].id: 0}

        goals = create_poll_reactive_goals(sample_agents, result, agent_votes, db)

        # Check for discussion goal
        discuss_goals = [
            g for g in goals
            if g.type == GoalType.DISCUSS_POLL_RESULT.value
            and g.agent_id == sample_agents[0].id
        ]
        assert len(discuss_goals) == 1
        assert "discuss" in discuss_goals[0].description.lower()

    def test_create_gossip_goals_for_low_discretion(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that agents with low discretion want to share the news."""
        result = PollResult(
            poll_id=sample_poll.id,
            question=sample_poll.question,
            winning_option="Yes, explore the cave",
            winning_index=0,
            total_votes=10,
            vote_counts={"Yes, explore the cave": 5, "No, it's too dangerous": 3, "Send scouts first": 2},
            category="exploration",
        )

        # Agent 2 has low discretion (2)
        agent_votes = {sample_agents[2].id: 0}

        goals = create_poll_reactive_goals(sample_agents, result, agent_votes, db)

        # Check for gossip goal
        gossip_goals = [
            g for g in goals
            if g.type == GoalType.SHARE_GOSSIP.value
            and g.agent_id == sample_agents[2].id
        ]
        assert len(gossip_goals) == 1
        assert "Share news" in gossip_goals[0].description

    def test_create_implementation_goals_for_governance(
        self, db: Session, sample_agents: list[Agent], governance_poll: Poll
    ):
        """Test that governance polls create implementation goals."""
        result = PollResult(
            poll_id=governance_poll.id,
            question=governance_poll.question,
            winning_option="Elder Marcus - the wise leader",
            winning_index=0,
            total_votes=10,
            vote_counts={"Elder Marcus - the wise leader": 5, "Young Ada - the innovative thinker": 3, "Merchant Finn - the pragmatic choice": 2},
            category="governance",
        )

        # Agent 0 has high ambition (8), agent 2 has high courage (8)
        agent_votes = {}

        goals = create_poll_reactive_goals(sample_agents, result, agent_votes, db)

        # Check for implementation goals
        impl_goals = [g for g in goals if g.type == GoalType.IMPLEMENT_POLL_DECISION.value]
        assert len(impl_goals) >= 1

        # Should be from agents with high ambition or courage
        impl_agent_ids = [g.agent_id for g in impl_goals]
        assert sample_agents[0].id in impl_agent_ids or sample_agents[2].id in impl_agent_ids


class TestProcessAgentVotesWithMemories:
    """Tests for process_agent_votes with memory creation."""

    def test_process_agent_votes_creates_memories(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that bulk voting creates memories for all agents."""
        decisions, agent_votes = process_agent_votes(
            db, sample_poll, sample_agents, create_memories=True
        )

        # Check decisions
        assert len(decisions) == len(sample_agents)

        # Check agent_votes mapping
        assert len(agent_votes) == len(sample_agents)
        for agent in sample_agents:
            assert agent.id in agent_votes

        # Check memories were created
        for agent in sample_agents:
            memories = (
                db.query(Memory)
                .filter(Memory.agent_id == agent.id)
                .all()
            )
            assert len(memories) == 1
            assert "voted for" in memories[0].content

    def test_process_agent_votes_without_memories(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that bulk voting can skip memory creation."""
        decisions, agent_votes = process_agent_votes(
            db, sample_poll, sample_agents, create_memories=False
        )

        # Check decisions still work
        assert len(decisions) == len(sample_agents)

        # Check no memories were created
        for agent in sample_agents:
            memories = (
                db.query(Memory)
                .filter(Memory.agent_id == agent.id)
                .all()
            )
            assert len(memories) == 0


class TestOnPollClosed:
    """Tests for the full poll closure integration."""

    @pytest.mark.asyncio
    async def test_on_poll_closed_creates_memories_and_goals(
        self, db: Session, sample_agents: list[Agent], sample_poll: Poll
    ):
        """Test that poll closure creates memories and goals."""
        # Set up votes and close the poll
        sample_poll.votes_dict = {"0": 2, "1": 1}
        sample_poll.status = "closed"
        db.commit()

        agent_votes = {
            sample_agents[0].id: 0,
            sample_agents[1].id: 1,
            sample_agents[2].id: 0,
        }

        result = await on_poll_closed(sample_poll, db, agent_votes)

        # Verify result
        assert result.winning_index == 0
        assert result.winning_option == "Yes, explore the cave"

        # Check memories were created for all agents
        all_memories = db.query(Memory).all()
        assert len(all_memories) >= len(sample_agents)

        # Check goals were created
        all_goals = (
            db.query(Goal)
            .filter(Goal.status == "active")
            .all()
        )
        assert len(all_goals) >= 1

        # Verify goal types are poll-related
        goal_types = [g.type for g in all_goals]
        poll_goal_types = [
            GoalType.DISCUSS_POLL_RESULT.value,
            GoalType.CELEBRATE_POLL_WIN.value,
            GoalType.ACCEPT_POLL_LOSS.value,
            GoalType.SHARE_GOSSIP.value,
            GoalType.IMPLEMENT_POLL_DECISION.value,
        ]
        assert any(gt in poll_goal_types for gt in goal_types)


class TestGoalTypeIntegration:
    """Tests for the new poll-related goal types."""

    def test_poll_goal_types_exist(self):
        """Test that poll-related goal types are defined."""
        assert hasattr(GoalType, "DISCUSS_POLL_RESULT")
        assert hasattr(GoalType, "CELEBRATE_POLL_WIN")
        assert hasattr(GoalType, "ACCEPT_POLL_LOSS")
        assert hasattr(GoalType, "IMPLEMENT_POLL_DECISION")

    def test_poll_goals_are_reactive(self):
        """Test that poll goals are categorized as reactive."""
        from hamlet.goals.types import REACTIVE

        assert GoalType.DISCUSS_POLL_RESULT in REACTIVE
        assert GoalType.CELEBRATE_POLL_WIN in REACTIVE
        assert GoalType.ACCEPT_POLL_LOSS in REACTIVE
        assert GoalType.IMPLEMENT_POLL_DECISION in REACTIVE
