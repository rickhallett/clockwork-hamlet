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

    # Relationships
    agent = relationship("Agent", back_populates="goals")


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
