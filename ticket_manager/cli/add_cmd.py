"""Add command for creating new tickets."""

import typer
from typing import Optional, List
from datetime import date

from ticket_manager.cli.formatters import print_success, print_error
from ticket_manager.db.connection import get_session
from ticket_manager.services.ticket_service import TicketService
from ticket_manager.models.enums import TicketType
from ticket_manager.filters.date_parser import parse_date_value

app = typer.Typer(help="Add new tickets")


@app.command("epic")
def add_epic(
    title: str = typer.Argument(..., help="Epic title"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project code"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description"),
    priority: int = typer.Option(3, "--priority", "-P", help="Priority (1-5)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
    due: Optional[str] = typer.Option(None, "--due", help="Due date"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    points: Optional[int] = typer.Option(None, "--points", help="Story points"),
):
    """Create a new epic."""
    _create_ticket(
        title=title,
        ticket_type=TicketType.EPIC,
        project=project,
        description=description,
        priority=priority,
        assignee=assignee,
        due=due,
        tags=tags,
        points=points,
    )


@app.command("story")
def add_story(
    title: str = typer.Argument(..., help="Story title"),
    epic: Optional[str] = typer.Option(None, "--epic", "-e", help="Parent epic key"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project code"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description"),
    priority: int = typer.Option(3, "--priority", "-P", help="Priority (1-5)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
    due: Optional[str] = typer.Option(None, "--due", help="Due date"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    points: Optional[int] = typer.Option(None, "--points", help="Story points"),
):
    """Create a new story."""
    _create_ticket(
        title=title,
        ticket_type=TicketType.STORY,
        parent_key=epic,
        project=project,
        description=description,
        priority=priority,
        assignee=assignee,
        due=due,
        tags=tags,
        points=points,
    )


@app.command("task")
def add_task(
    title: str = typer.Argument(..., help="Task title"),
    story: Optional[str] = typer.Option(None, "--story", "-s", help="Parent story key"),
    project: Optional[str] = typer.Option(None, "--project", "-p", help="Project code"),
    description: Optional[str] = typer.Option(None, "--desc", "-d", help="Description"),
    priority: int = typer.Option(3, "--priority", "-P", help="Priority (1-5)"),
    assignee: Optional[str] = typer.Option(None, "--assignee", "-a", help="Assignee"),
    due: Optional[str] = typer.Option(None, "--due", help="Due date"),
    tags: Optional[List[str]] = typer.Option(None, "--tag", "-t", help="Tags"),
    hours: Optional[float] = typer.Option(None, "--hours", help="Time estimate in hours"),
):
    """Create a new task."""
    _create_ticket(
        title=title,
        ticket_type=TicketType.TASK,
        parent_key=story,
        project=project,
        description=description,
        priority=priority,
        assignee=assignee,
        due=due,
        tags=tags,
        hours=hours,
    )


def _create_ticket(
    title: str,
    ticket_type: TicketType,
    parent_key: Optional[str] = None,
    project: Optional[str] = None,
    description: Optional[str] = None,
    priority: int = 3,
    assignee: Optional[str] = None,
    due: Optional[str] = None,
    tags: Optional[List[str]] = None,
    points: Optional[int] = None,
    hours: Optional[float] = None,
) -> None:
    """Create a ticket of the specified type."""
    # Parse due date if provided
    due_date = None
    if due:
        try:
            due_date = parse_date_value(due)
        except ValueError as e:
            print_error(f"Invalid due date: {e}")
            raise typer.Exit(1)

    # Validate priority
    if not 1 <= priority <= 5:
        print_error("Priority must be between 1 and 5")
        raise typer.Exit(1)

    with get_session() as session:
        service = TicketService(session)

        try:
            ticket = service.create(
                title=title,
                ticket_type=ticket_type,
                description=description,
                project=project,
                parent_key=parent_key,
                assignee=assignee,
                priority=priority,
                due_date=due_date,
                estimate_points=points,
                estimate_hours=hours,
                tags=tags,
            )
            print_success(f"Created {ticket_type.value} {ticket.key}: {title}")

        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
