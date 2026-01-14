"""Show command for displaying ticket details."""

import typer

from ticket_manager.cli.formatters import print_ticket_detail, print_error
from ticket_manager.db.connection import get_session
from ticket_manager.services.ticket_service import TicketService


def show_ticket(
    key: str,
    show_comments: bool = False,
    show_history: bool = False,
) -> None:
    """Show detailed information for a ticket."""
    with get_session() as session:
        service = TicketService(session)
        ticket = service.get_by_key(key)

        if ticket is None:
            print_error(f"Ticket not found: {key}")
            raise typer.Exit(1)

        comments = None
        history = None

        if show_comments:
            comments = service.get_comments(ticket)

        if show_history:
            history = service.get_history(ticket)

        print_ticket_detail(ticket, comments=comments, history=history)
