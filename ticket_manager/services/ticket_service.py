"""CRUD operations for tickets."""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from ticket_manager.db.models import Ticket, Tag, Label, Comment, TicketHistory
from ticket_manager.models.enums import (
    TicketType,
    TicketStatus,
    can_transition,
    get_valid_parent_type,
)
from ticket_manager.services.key_generator import generate_key


class TicketService:
    """Service for ticket CRUD operations."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        title: str,
        ticket_type: TicketType = TicketType.TASK,
        description: str | None = None,
        project: str | None = None,
        parent_key: str | None = None,
        assignee: str | None = None,
        reporter: str | None = None,
        priority: int = 3,
        due_date=None,
        estimate_points: int | None = None,
        estimate_hours: float | None = None,
        tags: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Create a new ticket."""
        # Resolve parent if provided
        parent = None
        if parent_key:
            parent = self.get_by_key(parent_key)
            if parent is None:
                raise ValueError(f"Parent ticket not found: {parent_key}")

            # Validate parent type
            valid_parent_type = get_valid_parent_type(ticket_type)
            if valid_parent_type is not None:
                parent_type = TicketType(parent.type)
                if parent_type != valid_parent_type:
                    raise ValueError(
                        f"{ticket_type.value} must have {valid_parent_type.value} as parent, "
                        f"not {parent_type.value}"
                    )

            # Inherit project from parent if not specified
            if project is None:
                project = parent.project

        # Generate unique key
        key = generate_key(self.session, project)

        # Create the ticket
        ticket = Ticket(
            key=key,
            type=ticket_type.value,
            title=title,
            description=description,
            status=TicketStatus.BACKLOG.value,
            priority=priority,
            project=project,
            parent_id=parent.id if parent else None,
            assignee=assignee,
            reporter=reporter,
            due_date=due_date,
            estimate_points=estimate_points,
            estimate_hours=estimate_hours,
        )

        self.session.add(ticket)
        self.session.flush()  # Get the ID

        # Add tags
        if tags:
            for tag_name in tags:
                self._add_tag(ticket, tag_name)

        # Add labels
        if labels:
            for label_name in labels:
                self._add_label(ticket, label_name)

        # Record creation in history
        self._record_history(ticket, "created", None, "true")

        return ticket

    def get_by_key(self, key: str) -> Ticket | None:
        """Get a ticket by its key."""
        return (
            self.session.query(Ticket)
            .options(joinedload(Ticket.tags), joinedload(Ticket.labels))
            .filter(Ticket.key == key.upper())
            .first()
        )

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        """Get a ticket by its ID."""
        return (
            self.session.query(Ticket)
            .options(joinedload(Ticket.tags), joinedload(Ticket.labels))
            .filter(Ticket.id == ticket_id)
            .first()
        )

    def list_all(self, include_done: bool = False) -> list[Ticket]:
        """List all tickets."""
        query = self.session.query(Ticket).options(
            joinedload(Ticket.tags), joinedload(Ticket.labels)
        )
        if not include_done:
            query = query.filter(
                Ticket.status.notin_([TicketStatus.DONE.value, TicketStatus.CANCELLED.value])
            )
        return query.order_by(Ticket.priority, Ticket.created_at.desc()).all()

    def update(
        self,
        ticket: Ticket,
        title: str | None = None,
        description: str | None = None,
        status: TicketStatus | None = None,
        priority: int | None = None,
        assignee: str | None = None,
        due_date=None,
        estimate_points: int | None = None,
        estimate_hours: float | None = None,
        changed_by: str | None = None,
    ) -> Ticket:
        """Update a ticket's fields."""
        updates = {
            "title": title,
            "description": description,
            "priority": priority,
            "assignee": assignee,
            "due_date": due_date,
            "estimate_points": estimate_points,
            "estimate_hours": estimate_hours,
        }

        for field, value in updates.items():
            if value is not None:
                old_value = getattr(ticket, field)
                if old_value != value:
                    setattr(ticket, field, value)
                    self._record_history(ticket, field, str(old_value), str(value), changed_by)

        # Handle status transition separately (with validation)
        if status is not None and status.value != ticket.status:
            self.transition_status(ticket, status, changed_by)

        ticket.updated_at = datetime.utcnow()
        return ticket

    def transition_status(
        self, ticket: Ticket, new_status: TicketStatus, changed_by: str | None = None
    ) -> Ticket:
        """Transition a ticket to a new status."""
        old_status = TicketStatus(ticket.status)

        if not can_transition(old_status, new_status):
            raise ValueError(
                f"Cannot transition from {old_status.value} to {new_status.value}"
            )

        old_value = ticket.status
        ticket.status = new_status.value

        # Record timestamps for specific transitions
        if new_status == TicketStatus.IN_PROGRESS and ticket.started_at is None:
            ticket.started_at = datetime.utcnow()
        elif new_status == TicketStatus.DONE:
            ticket.completed_at = datetime.utcnow()

        self._record_history(ticket, "status", old_value, new_status.value, changed_by)
        ticket.updated_at = datetime.utcnow()

        return ticket

    def delete(self, ticket: Ticket) -> None:
        """Delete a ticket."""
        self.session.delete(ticket)

    def add_comment(
        self, ticket: Ticket, content: str, author: str | None = None
    ) -> Comment:
        """Add a comment to a ticket."""
        comment = Comment(
            ticket_id=ticket.id,
            author=author,
            content=content,
        )
        self.session.add(comment)
        ticket.updated_at = datetime.utcnow()
        return comment

    def get_comments(self, ticket: Ticket) -> list[Comment]:
        """Get all comments for a ticket."""
        return (
            self.session.query(Comment)
            .filter(Comment.ticket_id == ticket.id)
            .order_by(Comment.created_at)
            .all()
        )

    def get_history(self, ticket: Ticket) -> list[TicketHistory]:
        """Get the change history for a ticket."""
        return (
            self.session.query(TicketHistory)
            .filter(TicketHistory.ticket_id == ticket.id)
            .order_by(TicketHistory.changed_at.desc())
            .all()
        )

    def add_tag(self, ticket: Ticket, tag_name: str) -> None:
        """Add a tag to a ticket."""
        self._add_tag(ticket, tag_name)
        ticket.updated_at = datetime.utcnow()

    def remove_tag(self, ticket: Ticket, tag_name: str) -> None:
        """Remove a tag from a ticket."""
        tag = self.session.query(Tag).filter(Tag.name == tag_name.lower()).first()
        if tag and tag in ticket.tags:
            ticket.tags.remove(tag)
            ticket.updated_at = datetime.utcnow()

    def _add_tag(self, ticket: Ticket, tag_name: str) -> Tag:
        """Add or get a tag and associate with ticket."""
        tag_name = tag_name.lower().strip()
        tag = self.session.query(Tag).filter(Tag.name == tag_name).first()
        if tag is None:
            tag = Tag(name=tag_name)
            self.session.add(tag)
        if tag not in ticket.tags:
            ticket.tags.append(tag)
        return tag

    def _add_label(self, ticket: Ticket, label_name: str, color: str = "#808080") -> Label:
        """Add or get a label and associate with ticket."""
        label_name = label_name.strip()
        label = self.session.query(Label).filter(Label.name == label_name).first()
        if label is None:
            label = Label(name=label_name, color=color)
            self.session.add(label)
        if label not in ticket.labels:
            ticket.labels.append(label)
        return label

    def _record_history(
        self,
        ticket: Ticket,
        field: str,
        old_value: str | None,
        new_value: str | None,
        changed_by: str | None = None,
    ) -> TicketHistory:
        """Record a change in ticket history."""
        history = TicketHistory(
            ticket_id=ticket.id,
            field=field,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
        )
        self.session.add(history)
        return history
