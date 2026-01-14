"""Main CLI application entry point."""

import typer
from typing import Optional, List

from ticket_manager.cli.formatters import console, print_success, print_error
from ticket_manager.db.connection import init_db, get_session
from ticket_manager.services.ticket_service import TicketService
from ticket_manager.models.enums import TicketType, TicketStatus

app = typer.Typer(
    name="ticket",
    help="CLI ticket manager for development roadmaps",
    no_args_is_help=True,
)


# Import and register subcommands
from ticket_manager.cli import add_cmd, list_cmd, show_cmd, modify_cmd


app.add_typer(add_cmd.app, name="add", help="Add new tickets")


@app.command("init")
def init_database():
    """Initialize the ticket database."""
    try:
        init_db()
        print_success("Database initialized successfully.")
    except Exception as e:
        print_error(f"Failed to initialize database: {e}")
        raise typer.Exit(1)


@app.command("list")
def list_tickets(
    filters: Optional[List[str]] = typer.Argument(None, help="Filter expressions"),
    all: bool = typer.Option(False, "--all", "-a", help="Include done/cancelled tickets"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Filter by project"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
    assignee: Optional[str] = typer.Option(None, "--assignee", help="Filter by assignee"),
):
    """List tickets with optional filters."""
    list_cmd.list_tickets(
        filters=filters,
        include_done=all,
        project=project,
        status=status,
        ticket_type=type,
        assignee=assignee,
    )


@app.command("show")
def show_ticket(
    key: str = typer.Argument(..., help="Ticket key (e.g., PROJ-123)"),
    comments: bool = typer.Option(False, "--comments", "-c", help="Show comments"),
    history: bool = typer.Option(False, "--history", "-h", help="Show change history"),
):
    """Show detailed ticket information."""
    show_cmd.show_ticket(key, show_comments=comments, show_history=history)


@app.command("modify")
def modify_ticket(
    key: str = typer.Argument(..., help="Ticket key"),
    modifications: Optional[List[str]] = typer.Argument(None, help="Modifications (key:value)"),
):
    """Modify a ticket's fields."""
    modify_cmd.modify_ticket(key, modifications)


@app.command("start")
def start_ticket(key: str = typer.Argument(..., help="Ticket key")):
    """Start working on a ticket (move to in_progress)."""
    modify_cmd.transition_status(key, TicketStatus.IN_PROGRESS)


@app.command("done")
def done_ticket(key: str = typer.Argument(..., help="Ticket key")):
    """Mark a ticket as done."""
    modify_cmd.transition_status(key, TicketStatus.DONE)


@app.command("review")
def review_ticket(key: str = typer.Argument(..., help="Ticket key")):
    """Move a ticket to review."""
    modify_cmd.transition_status(key, TicketStatus.REVIEW)


@app.command("todo")
def todo_ticket(key: str = typer.Argument(..., help="Ticket key")):
    """Move a ticket to todo."""
    modify_cmd.transition_status(key, TicketStatus.TODO)


@app.command("delete")
def delete_ticket(
    key: str = typer.Argument(..., help="Ticket key"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
):
    """Delete a ticket."""
    from ticket_manager.cli.formatters import confirm

    with get_session() as session:
        service = TicketService(session)
        ticket = service.get_by_key(key)

        if ticket is None:
            print_error(f"Ticket not found: {key}")
            raise typer.Exit(1)

        if not force:
            if not confirm(f"Delete ticket {ticket.key} '{ticket.title}'?"):
                print_error("Cancelled.")
                raise typer.Exit(0)

        service.delete(ticket)
        print_success(f"Deleted ticket {key}")


@app.command("comment")
def add_comment(
    key: str = typer.Argument(..., help="Ticket key"),
    text: str = typer.Argument(..., help="Comment text"),
):
    """Add a comment to a ticket."""
    with get_session() as session:
        service = TicketService(session)
        ticket = service.get_by_key(key)

        if ticket is None:
            print_error(f"Ticket not found: {key}")
            raise typer.Exit(1)

        service.add_comment(ticket, text)
        print_success(f"Added comment to {key}")


if __name__ == "__main__":
    app()
