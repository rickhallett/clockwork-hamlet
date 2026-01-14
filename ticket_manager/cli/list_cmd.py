"""List command for displaying tickets."""

import typer
from typing import Optional, List

from sqlalchemy.orm import joinedload

from ticket_manager.cli.formatters import print_ticket_table, print_error
from ticket_manager.db.connection import get_session
from ticket_manager.db.models import Ticket
from ticket_manager.models.enums import TicketStatus
from ticket_manager.filters.parser import parse_filters, apply_filters


def list_tickets(
    filters: Optional[List[str]] = None,
    include_done: bool = False,
    project: Optional[str] = None,
    status: Optional[str] = None,
    ticket_type: Optional[str] = None,
    assignee: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> None:
    """List tickets with filtering."""
    with get_session() as session:
        query = session.query(Ticket).options(
            joinedload(Ticket.tags),
            joinedload(Ticket.labels),
        )

        # Apply basic filters from options
        if project:
            query = query.filter(Ticket.project == project.upper())
        if status:
            query = query.filter(Ticket.status == status)
        if ticket_type:
            query = query.filter(Ticket.type == ticket_type)
        if assignee:
            query = query.filter(Ticket.assignee == assignee)

        # Exclude done/cancelled unless requested
        if not include_done:
            query = query.filter(
                Ticket.status.notin_([TicketStatus.DONE.value, TicketStatus.CANCELLED.value])
            )

        # Parse and apply filter expressions
        if filters:
            try:
                filter_exprs = parse_filters(filters)
                query = apply_filters(query, filter_exprs, session)
            except ValueError as e:
                print_error(f"Invalid filter: {e}")
                raise typer.Exit(1)

        # Order by priority, then creation date
        query = query.order_by(Ticket.priority, Ticket.created_at.desc())

        tickets = query.all()
        print_ticket_table(tickets, columns)
