"""SQLAlchemy models for ticket manager."""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Boolean,
    Table,
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""

    pass


# Association tables
ticket_tags = Table(
    "ticket_tags",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

ticket_labels = Table(
    "ticket_labels",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Integer, ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)

ticket_sprints = Table(
    "ticket_sprints",
    Base.metadata,
    Column("ticket_id", Integer, ForeignKey("tickets.id", ondelete="CASCADE"), primary_key=True),
    Column("sprint_id", Integer, ForeignKey("sprints.id", ondelete="CASCADE"), primary_key=True),
)


class Ticket(Base):
    """A ticket (Epic, Story, or Task)."""

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="backlog", index=True)
    priority: Mapped[int] = mapped_column(Integer, default=3, index=True)

    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tickets.id"), index=True)

    # Metadata
    project: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    assignee: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    reporter: Mapped[Optional[str]] = mapped_column(String(100))

    # Dates
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Estimates
    estimate_points: Mapped[Optional[int]] = mapped_column(Integer)
    estimate_hours: Mapped[Optional[float]] = mapped_column(Float)

    # Relationships
    parent: Mapped[Optional["Ticket"]] = relationship(
        "Ticket", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Ticket"]] = relationship(
        "Ticket", back_populates="parent", cascade="all, delete-orphan"
    )
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=ticket_tags, back_populates="tickets"
    )
    labels: Mapped[list["Label"]] = relationship(
        "Label", secondary=ticket_labels, back_populates="tickets"
    )
    comments: Mapped[list["Comment"]] = relationship(
        "Comment", back_populates="ticket", cascade="all, delete-orphan"
    )
    history: Mapped[list["TicketHistory"]] = relationship(
        "TicketHistory", back_populates="ticket", cascade="all, delete-orphan"
    )
    sprints: Mapped[list["Sprint"]] = relationship(
        "Sprint", secondary=ticket_sprints, back_populates="tickets"
    )

    def __repr__(self) -> str:
        return f"<Ticket {self.key}: {self.title[:30]}>"


class Tag(Base):
    """A tag for categorizing tickets."""

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", secondary=ticket_tags, back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name}>"


class Label(Base):
    """A label with color for visual categorization."""

    __tablename__ = "labels"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#808080")

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", secondary=ticket_labels, back_populates="labels"
    )

    def __repr__(self) -> str:
        return f"<Label {self.name}>"


class Comment(Base):
    """A comment on a ticket."""

    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    author: Mapped[Optional[str]] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="comments")

    def __repr__(self) -> str:
        return f"<Comment on {self.ticket_id}>"


class TicketHistory(Base):
    """Audit log for ticket changes."""

    __tablename__ = "ticket_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    field: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[Optional[str]] = mapped_column(Text)
    new_value: Mapped[Optional[str]] = mapped_column(Text)
    changed_by: Mapped[Optional[str]] = mapped_column(String(100))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="history")

    def __repr__(self) -> str:
        return f"<History {self.ticket_id}: {self.field}>"


class Context(Base):
    """A saved filter context (like Taskwarrior contexts)."""

    __tablename__ = "contexts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    filter_expression: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Context {self.name}>"


class Sprint(Base):
    """A sprint for agile planning."""

    __tablename__ = "sprints"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    project: Mapped[Optional[str]] = mapped_column(String(100))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    goal: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="planning")

    tickets: Mapped[list["Ticket"]] = relationship(
        "Ticket", secondary=ticket_sprints, back_populates="sprints"
    )

    def __repr__(self) -> str:
        return f"<Sprint {self.name}>"


class KeySequence(Base):
    """Track ticket key sequences per project."""

    __tablename__ = "key_sequences"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    last_number: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return f"<KeySequence {self.project}: {self.last_number}>"
