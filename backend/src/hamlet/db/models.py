"""SQLAlchemy models for Clockwork Hamlet."""

import json

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


class JsonColumn(Text):
    """Custom column type for JSON storage."""

    pass


def json_serializer(obj):
    """Serialize Python objects to JSON string."""
    if obj is None:
        return None
    return json.dumps(obj)


def json_deserializer(data):
    """Deserialize JSON string to Python objects."""
    if data is None:
        return None
    if isinstance(data, (dict, list)):
        return data
    return json.loads(data)


class Location(Base):
    """A location in the village."""

    __tablename__ = "locations"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    connections = Column(Text, default="[]")  # JSON array of location IDs
    objects = Column(Text, default="[]")  # JSON array of object names
    capacity = Column(Integer, default=10)

    # Relationships
    agents = relationship("Agent", back_populates="location")
    events = relationship("Event", back_populates="location")

    @property
    def connections_list(self) -> list[str]:
        return json_deserializer(self.connections) or []

    @connections_list.setter
    def connections_list(self, value: list[str]):
        self.connections = json_serializer(value)

    @property
    def objects_list(self) -> list[str]:
        return json_deserializer(self.objects) or []

    @objects_list.setter
    def objects_list(self, value: list[str]):
        self.objects = json_serializer(value)


class Agent(Base):
    """An AI agent in the village."""

    __tablename__ = "agents"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    personality_prompt = Column(Text)
    traits = Column(Text, default="{}")  # JSON object
    location_id = Column(String(50), ForeignKey("locations.id"))
    inventory = Column(Text, default="[]")  # JSON array
    mood = Column(Text, default='{"happiness": 5, "energy": 7}')  # JSON object
    state = Column(String(20), default="idle")  # idle, busy, sleeping

    # Needs (0-10 scale)
    hunger = Column(Float, default=0.0)
    energy = Column(Float, default=10.0)
    social = Column(Float, default=5.0)

    # Relationships
    location = relationship("Location", back_populates="agents")
    memories = relationship("Memory", back_populates="agent", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="agent", cascade="all, delete-orphan")
    relationships_as_source = relationship(
        "Relationship",
        foreign_keys="Relationship.agent_id",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    relationships_as_target = relationship(
        "Relationship",
        foreign_keys="Relationship.target_id",
        back_populates="target",
    )
    chat_conversations = relationship(
        "ChatConversation", back_populates="agent", cascade="all, delete-orphan"
    )

    @property
    def traits_dict(self) -> dict:
        return json_deserializer(self.traits) or {}

    @traits_dict.setter
    def traits_dict(self, value: dict):
        self.traits = json_serializer(value)

    @property
    def inventory_list(self) -> list[str]:
        return json_deserializer(self.inventory) or []

    @inventory_list.setter
    def inventory_list(self, value: list[str]):
        self.inventory = json_serializer(value)

    @property
    def mood_dict(self) -> dict:
        return json_deserializer(self.mood) or {}

    @mood_dict.setter
    def mood_dict(self, value: dict):
        self.mood = json_serializer(value)


class Relationship(Base):
    """A relationship between two agents."""

    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    target_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    type = Column(String(30), default="stranger")  # stranger, acquaintance, friend, rival, etc.
    score = Column(Integer, default=0)  # -10 to +10
    history = Column(Text, default="[]")  # JSON array of interaction summaries

    # Relationships
    agent = relationship("Agent", foreign_keys=[agent_id], back_populates="relationships_as_source")
    target = relationship(
        "Agent", foreign_keys=[target_id], back_populates="relationships_as_target"
    )

    __table_args__ = (UniqueConstraint("agent_id", "target_id", name="unique_relationship"),)

    @property
    def history_list(self) -> list[str]:
        return json_deserializer(self.history) or []

    @history_list.setter
    def history_list(self, value: list[str]):
        self.history = json_serializer(value)


class Memory(Base):
    """A memory belonging to an agent."""

    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    type = Column(String(20), default="working")  # working, recent, longterm
    content = Column(Text, nullable=False)
    significance = Column(Integer, default=5)  # 1-10
    compressed = Column(Boolean, default=False)

    # Relationships
    agent = relationship("Agent", back_populates="memories")


class Goal(Base):
    """A goal for an agent."""

    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    type = Column(String(30), nullable=False)  # eat, sleep, socialize, investigate, etc.
    description = Column(Text)
    priority = Column(Integer, default=5)  # 1-10, higher = more important
    target_id = Column(String(50))  # Optional target (agent or object ID)
    status = Column(String(20), default="active")  # active, completed, failed, abandoned
    created_at = Column(Integer, nullable=False)  # Unix timestamp
    parent_id = Column(Integer, ForeignKey("goals.id"))  # For hierarchical goals
    plan_id = Column(Integer, ForeignKey("goal_plans.id"))  # Link to long-term plan

    # Relationships
    agent = relationship("Agent", back_populates="goals")
    parent = relationship("Goal", remote_side=[id], backref="subgoals")


class Event(Base):
    """An event that occurred in the village."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Integer, nullable=False)  # Unix timestamp
    type = Column(
        String(30), nullable=False
    )  # movement, dialogue, action, relationship, discovery, system
    actors = Column(Text, default="[]")  # JSON array of agent IDs
    location_id = Column(String(50), ForeignKey("locations.id"))
    summary = Column(Text, nullable=False)  # One-line description
    detail = Column(Text)  # Full dialogue/description
    significance = Column(Integer, default=1)  # 1-3

    # Relationships
    location = relationship("Location", back_populates="events")

    @property
    def actors_list(self) -> list[str]:
        return json_deserializer(self.actors) or []

    @actors_list.setter
    def actors_list(self, value: list[str]):
        self.actors = json_serializer(value)


class Poll(Base):
    """A viewer poll."""

    __tablename__ = "polls"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question = Column(Text, nullable=False)
    options = Column(Text, nullable=False)  # JSON array of option strings
    votes = Column(Text, default="{}")  # JSON object: {option_index: vote_count}
    status = Column(String(20), default="active")  # scheduled, active, closed
    created_at = Column(Integer, nullable=False)  # Unix timestamp
    opens_at = Column(Integer)  # Unix timestamp - when poll becomes active
    closes_at = Column(Integer)  # Unix timestamp - when poll closes
    category = Column(String(50))  # Poll category for filtering
    tags = Column(Text, default="[]")  # JSON array of tag strings
    allow_multiple = Column(Boolean, default=False)  # Allow selecting multiple options

    @property
    def options_list(self) -> list[str]:
        return json_deserializer(self.options) or []

    @options_list.setter
    def options_list(self, value: list[str]):
        self.options = json_serializer(value)

    @property
    def votes_dict(self) -> dict[str, int]:
        return json_deserializer(self.votes) or {}

    @votes_dict.setter
    def votes_dict(self, value: dict[str, int]):
        self.votes = json_serializer(value)

    @property
    def tags_list(self) -> list[str]:
        return json_deserializer(self.tags) or []

    @tags_list.setter
    def tags_list(self, value: list[str]):
        self.tags = json_serializer(value)


class WorldState(Base):
    """Global world state (singleton)."""

    __tablename__ = "world_state"

    id = Column(Integer, primary_key=True, default=1)
    current_tick = Column(Integer, default=0)
    current_day = Column(Integer, default=1)
    current_hour = Column(Float, default=6.0)  # 0-24
    season = Column(String(20), default="spring")
    weather = Column(String(30), default="clear")


class LLMUsage(Base):
    """Record of LLM API usage for cost tracking."""

    __tablename__ = "llm_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Float, nullable=False)  # Unix timestamp with decimals
    model = Column(String(50), nullable=False)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)
    cached = Column(Boolean, default=False)
    agent_id = Column(String(50))  # Which agent triggered this call
    call_type = Column(String(30), default="decision")  # decision, dialogue, compression


class User(Base):
    """A user account."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(Float, nullable=False)  # Unix timestamp
    last_login = Column(Float)  # Unix timestamp

    # User preferences (stored as JSON)
    preferences = Column(Text, default="{}")

    # Relationships
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
    chat_conversations = relationship(
        "ChatConversation", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def preferences_dict(self) -> dict:
        return json_deserializer(self.preferences) or {}

    @preferences_dict.setter
    def preferences_dict(self, value: dict):
        self.preferences = json_serializer(value)


class RefreshToken(Base):
    """A refresh token for session management."""

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(Float, nullable=False)  # Unix timestamp
    expires_at = Column(Float, nullable=False)  # Unix timestamp
    revoked = Column(Boolean, default=False)
    revoked_at = Column(Float)  # Unix timestamp when revoked

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")


class ChatConversation(Base):
    """A chat conversation between a user and an agent."""

    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    created_at = Column(Float, nullable=False)  # Unix timestamp
    updated_at = Column(Float, nullable=False)  # Unix timestamp
    title = Column(String(255))  # Optional title for the conversation
    is_active = Column(Boolean, default=True)  # For soft-delete/archiving

    # Relationships
    user = relationship("User", back_populates="chat_conversations")
    agent = relationship("Agent", back_populates="chat_conversations")
    messages = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        # Index for efficient lookup of user's conversations with an agent
        # (Note: SQLite doesn't support explicit Index declarations here, but SQLAlchemy will create it)
    )


class ChatMessage(Base):
    """A single message in a chat conversation."""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "agent"
    content = Column(Text, nullable=False)
    timestamp = Column(Float, nullable=False)  # Unix timestamp

    # LLM usage tracking for agent responses
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    latency_ms = Column(Float, default=0.0)

    # Relationships
    conversation = relationship("ChatConversation", back_populates="messages")


# ============================================================================
# EMERGENT NARRATIVES MODELS (LIFE-29 through LIFE-32)
# ============================================================================


class Faction(Base):
    """A faction or alliance of agents with shared goals."""

    __tablename__ = "factions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    founder_id = Column(String(50), ForeignKey("agents.id"))
    location_id = Column(String(50), ForeignKey("locations.id"))  # Home base
    beliefs = Column(Text, default="[]")  # JSON array of core beliefs/values
    goals = Column(Text, default="[]")  # JSON array of faction goals
    treasury = Column(Float, default=0.0)  # Faction resources
    reputation = Column(Integer, default=0)  # -100 to +100
    status = Column(String(20), default="forming")  # forming, active, disbanded
    created_at = Column(Float, nullable=False)  # Unix timestamp

    # Relationships
    founder = relationship("Agent", foreign_keys=[founder_id])
    location = relationship("Location")
    memberships = relationship(
        "FactionMembership", back_populates="faction", cascade="all, delete-orphan"
    )

    @property
    def beliefs_list(self) -> list[str]:
        return json_deserializer(self.beliefs) or []

    @beliefs_list.setter
    def beliefs_list(self, value: list[str]):
        self.beliefs = json_serializer(value)

    @property
    def goals_list(self) -> list[str]:
        return json_deserializer(self.goals) or []

    @goals_list.setter
    def goals_list(self, value: list[str]):
        self.goals = json_serializer(value)


class FactionMembership(Base):
    """Membership of an agent in a faction."""

    __tablename__ = "faction_memberships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faction_id = Column(Integer, ForeignKey("factions.id"), nullable=False)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    role = Column(String(30), default="member")  # founder, leader, member, outcast
    loyalty = Column(Integer, default=50)  # 0-100
    contributions = Column(Float, default=0.0)  # Resources contributed
    joined_at = Column(Float, nullable=False)  # Unix timestamp
    left_at = Column(Float)  # Unix timestamp, null if still member

    # Relationships
    faction = relationship("Faction", back_populates="memberships")
    agent = relationship("Agent")

    __table_args__ = (
        UniqueConstraint("faction_id", "agent_id", name="unique_faction_membership"),
    )


class FactionRelationship(Base):
    """Relationship between two factions."""

    __tablename__ = "faction_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    faction_1_id = Column(Integer, ForeignKey("factions.id"), nullable=False)
    faction_2_id = Column(Integer, ForeignKey("factions.id"), nullable=False)
    type = Column(String(30), default="neutral")  # ally, enemy, neutral, competitor
    score = Column(Integer, default=0)  # -100 to +100
    history = Column(Text, default="[]")  # JSON array of diplomatic events

    # Relationships
    faction_1 = relationship("Faction", foreign_keys=[faction_1_id])
    faction_2 = relationship("Faction", foreign_keys=[faction_2_id])

    __table_args__ = (
        UniqueConstraint("faction_1_id", "faction_2_id", name="unique_faction_relationship"),
    )

    @property
    def history_list(self) -> list[str]:
        return json_deserializer(self.history) or []

    @history_list.setter
    def history_list(self, value: list[str]):
        self.history = json_serializer(value)


class GoalPlan(Base):
    """A long-term goal plan with multiple milestones (hierarchical goals)."""

    __tablename__ = "goal_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    type = Column(String(50), nullable=False)  # WEALTH, POWER, ROMANCE, KNOWLEDGE, etc.
    description = Column(Text, nullable=False)
    parent_id = Column(Integer, ForeignKey("goal_plans.id"))  # For hierarchical goals
    milestones = Column(Text, default="[]")  # JSON array of milestone objects
    dependencies = Column(Text, default="[]")  # JSON array of goal plan IDs
    progress = Column(Float, default=0.0)  # 0-100 percent
    target_agent_id = Column(String(50))  # Optional target agent
    status = Column(String(20), default="planning")  # planning, active, stalled, completed, failed
    created_at = Column(Float, nullable=False)  # Unix timestamp
    target_completion = Column(Float)  # Target completion timestamp

    # Relationships
    agent = relationship("Agent")
    parent = relationship("GoalPlan", remote_side=[id], backref="children")

    @property
    def milestones_list(self) -> list[dict]:
        return json_deserializer(self.milestones) or []

    @milestones_list.setter
    def milestones_list(self, value: list[dict]):
        self.milestones = json_serializer(value)

    @property
    def dependencies_list(self) -> list[int]:
        return json_deserializer(self.dependencies) or []

    @dependencies_list.setter
    def dependencies_list(self, value: list[int]):
        self.dependencies = json_serializer(value)


class LifeEvent(Base):
    """A significant life event (marriage, rivalry, mentorship, etc.)."""

    __tablename__ = "life_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(30), nullable=False)  # MARRIAGE, RIVALRY, MENTORSHIP, BETRAYAL, etc.
    primary_agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    secondary_agent_id = Column(String(50), ForeignKey("agents.id"))  # Optional second agent
    description = Column(Text, nullable=False)
    significance = Column(Integer, default=7)  # 1-10
    status = Column(String(20), default="active")  # pending, active, resolved, failed
    related_agents = Column(Text, default="[]")  # JSON array of other affected agent IDs
    effects = Column(Text, default="{}")  # JSON dict of effects (relationship changes, etc.)
    timestamp = Column(Float, nullable=False)  # Unix timestamp
    resolved_at = Column(Float)  # When the event concluded

    # Relationships
    primary_agent = relationship("Agent", foreign_keys=[primary_agent_id])
    secondary_agent = relationship("Agent", foreign_keys=[secondary_agent_id])

    @property
    def related_agents_list(self) -> list[str]:
        return json_deserializer(self.related_agents) or []

    @related_agents_list.setter
    def related_agents_list(self, value: list[str]):
        self.related_agents = json_serializer(value)

    @property
    def effects_dict(self) -> dict:
        return json_deserializer(self.effects) or {}

    @effects_dict.setter
    def effects_dict(self, value: dict):
        self.effects = json_serializer(value)


class NarrativeArc(Base):
    """A detected narrative arc involving one or more agents."""

    __tablename__ = "narrative_arcs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(50), nullable=False)  # LOVE_STORY, RIVALRY, MENTORSHIP, RISE_TO_POWER, etc.
    title = Column(String(200))  # Optional narrative title
    primary_agent_id = Column(String(50), ForeignKey("agents.id"), nullable=False)
    secondary_agent_id = Column(String(50), ForeignKey("agents.id"))  # Optional second protagonist
    theme = Column(Text)  # What this arc is about
    acts = Column(Text, default="[]")  # JSON array of act objects
    current_act = Column(Integer, default=0)  # 0-4: exposition, rising, climax, falling, resolution
    status = Column(String(20), default="forming")  # forming, rising_action, climax, resolution, complete
    significance = Column(Integer, default=5)  # 1-10 calculated from events
    discovered_at = Column(Float, nullable=False)  # Unix timestamp
    completed_at = Column(Float)  # When arc concluded

    # Relationships
    primary_agent = relationship("Agent", foreign_keys=[primary_agent_id])
    secondary_agent = relationship("Agent", foreign_keys=[secondary_agent_id])
    arc_events = relationship("ArcEvent", back_populates="arc", cascade="all, delete-orphan")

    @property
    def acts_list(self) -> list[dict]:
        return json_deserializer(self.acts) or []

    @acts_list.setter
    def acts_list(self, value: list[dict]):
        self.acts = json_serializer(value)


class ArcEvent(Base):
    """Junction table linking events to narrative arcs."""

    __tablename__ = "arc_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    arc_id = Column(Integer, ForeignKey("narrative_arcs.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    act_number = Column(Integer, default=0)  # Which act this event belongs to
    is_turning_point = Column(Boolean, default=False)  # Marks significant plot points
    notes = Column(Text)  # Optional context for this event in the arc

    # Relationships
    arc = relationship("NarrativeArc", back_populates="arc_events")
    event = relationship("Event")

    __table_args__ = (
        UniqueConstraint("arc_id", "event_id", name="unique_arc_event"),
    )
