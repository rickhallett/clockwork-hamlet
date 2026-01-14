"""Output formatting for CLI using Rich."""

from datetime import date, datetime
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from ticket_manager.db.models import Ticket, Comment, TicketHistory
from ticket_manager.models.enums import (
    TicketStatus,
    TicketType,
    STATUS_COLORS,
    PRIORITY_COLORS,
    TYPE_COLORS,
    PRIORITY_NAMES,
)


console = Console()


def format_status(status: str) -> Text:
    """Format a status with color."""
    try:
        status_enum = TicketStatus(status)
        color = STATUS_COLORS.get(status_enum, "white")
    except ValueError:
        color = "white"
    return Text(status, style=color)


def format_priority(priority: int) -> Text:
    """Format a priority with color."""
    color = PRIORITY_COLORS.get(priority, "white")
    name = PRIORITY_NAMES.get(priority, str(priority))
    return Text(f"P{priority}", style=color)


def format_type(ticket_type: str) -> Text:
    """Format a ticket type with color."""
    try:
        type_enum = TicketType(ticket_type)
        color = TYPE_COLORS.get(type_enum, "white")
    except ValueError:
        color = "white"
    return Text(ticket_type.upper()[:1], style=color)


def format_date(d: date | datetime | None) -> str:
    """Format a date for display."""
    if d is None:
        return "-"
    if isinstance(d, datetime):
        d = d.date()
    today = date.today()
    delta = (d - today).days

    if delta == 0:
        return "today"
    elif delta == 1:
        return "tomorrow"
    elif delta == -1:
        return "yesterday"
    elif -7 <= delta < 0:
        return f"{-delta}d ago"
    elif 0 < delta <= 7:
        return f"in {delta}d"
    else:
        return d.strftime("%Y-%m-%d")


def print_ticket_table(tickets: list[Ticket], columns: list[str] | None = None) -> None:
    """Print tickets in a table format."""
    if not tickets:
        console.print("[dim]No tickets found.[/dim]")
        return

    if columns is None:
        columns = ["key", "type", "title", "status", "priority", "assignee"]

    table = Table(show_header=True, header_style="bold")

    # Add columns
    col_configs = {
        "key": ("Key", {}),
        "type": ("T", {"justify": "center"}),
        "title": ("Title", {"max_width": 50}),
        "status": ("Status", {}),
        "priority": ("Pri", {"justify": "center"}),
        "assignee": ("Assignee", {}),
        "project": ("Project", {}),
        "due_date": ("Due", {}),
        "created_at": ("Created", {}),
        "tags": ("Tags", {}),
    }

    for col in columns:
        name, kwargs = col_configs.get(col, (col.title(), {}))
        table.add_column(name, **kwargs)

    # Add rows
    for ticket in tickets:
        row = []
        for col in columns:
            if col == "key":
                row.append(Text(ticket.key, style="cyan"))
            elif col == "type":
                row.append(format_type(ticket.type))
            elif col == "title":
                title = ticket.title
                if len(title) > 50:
                    title = title[:47] + "..."
                row.append(title)
            elif col == "status":
                row.append(format_status(ticket.status))
            elif col == "priority":
                row.append(format_priority(ticket.priority))
            elif col == "assignee":
                row.append(ticket.assignee or "-")
            elif col == "project":
                row.append(ticket.project or "-")
            elif col == "due_date":
                row.append(format_date(ticket.due_date))
            elif col == "created_at":
                row.append(format_date(ticket.created_at))
            elif col == "tags":
                tags = ", ".join(f"+{t.name}" for t in ticket.tags)
                row.append(Text(tags, style="dim") if tags else "-")
            else:
                row.append(str(getattr(ticket, col, "-")))

        table.add_row(*row)

    console.print(table)


def print_ticket_detail(
    ticket: Ticket,
    comments: list[Comment] | None = None,
    history: list[TicketHistory] | None = None,
) -> None:
    """Print detailed ticket information."""
    # Header with key and title
    header = Text()
    header.append(f"[{ticket.key}] ", style="cyan bold")
    header.append(ticket.title, style="bold")

    # Type and status badges
    type_text = format_type(ticket.type)
    status_text = format_status(ticket.status)

    # Main info table
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Field", style="dim")
    info_table.add_column("Value")

    info_table.add_row("Type", type_text)
    info_table.add_row("Status", status_text)
    info_table.add_row("Priority", format_priority(ticket.priority))
    info_table.add_row("Project", ticket.project or "-")
    info_table.add_row("Assignee", ticket.assignee or "-")
    info_table.add_row("Reporter", ticket.reporter or "-")
    info_table.add_row("Due Date", format_date(ticket.due_date))
    info_table.add_row("Created", format_date(ticket.created_at))
    info_table.add_row("Updated", format_date(ticket.updated_at))

    if ticket.estimate_points:
        info_table.add_row("Points", str(ticket.estimate_points))
    if ticket.estimate_hours:
        info_table.add_row("Hours", str(ticket.estimate_hours))

    # Tags and labels
    if ticket.tags:
        tags = " ".join(f"+{t.name}" for t in ticket.tags)
        info_table.add_row("Tags", Text(tags, style="blue"))
    if ticket.labels:
        labels = " ".join(l.name for l in ticket.labels)
        info_table.add_row("Labels", labels)

    # Parent/children
    if ticket.parent:
        info_table.add_row("Parent", Text(ticket.parent.key, style="cyan"))
    if ticket.children:
        children = ", ".join(c.key for c in ticket.children)
        info_table.add_row("Children", Text(children, style="cyan"))

    console.print(Panel(header, expand=False))
    console.print(info_table)

    # Description
    if ticket.description:
        console.print()
        console.print("[bold]Description[/bold]")
        console.print(Panel(ticket.description, border_style="dim"))

    # Comments
    if comments:
        console.print()
        console.print(f"[bold]Comments ({len(comments)})[/bold]")
        for comment in comments:
            author = comment.author or "anonymous"
            time = format_date(comment.created_at)
            console.print(f"[dim]{author} - {time}[/dim]")
            console.print(f"  {comment.content}")
            console.print()

    # History
    if history:
        console.print()
        console.print(f"[bold]History ({len(history)})[/bold]")
        hist_table = Table(show_header=True, header_style="dim")
        hist_table.add_column("When")
        hist_table.add_column("Field")
        hist_table.add_column("Change")
        hist_table.add_column("By")

        for h in history[:10]:  # Last 10 changes
            change = f"{h.old_value or '-'} → {h.new_value or '-'}"
            hist_table.add_row(
                format_date(h.changed_at),
                h.field,
                change,
                h.changed_by or "-",
            )

        console.print(hist_table)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]✗[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]![/yellow] {message}")


def confirm(message: str) -> bool:
    """Ask for confirmation."""
    response = console.input(f"{message} [y/N]: ")
    return response.lower() in ("y", "yes")
