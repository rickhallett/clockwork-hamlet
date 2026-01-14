"""Modify command for updating tickets."""

import typer
from typing import Optional, List

from ticket_manager.cli.formatters import print_success, print_error
from ticket_manager.db.connection import get_session
from ticket_manager.services.ticket_service import TicketService
from ticket_manager.models.enums import TicketStatus
from ticket_manager.filters.date_parser import parse_date_value


def modify_ticket(key: str, modifications: Optional[List[str]] = None) -> None:
    """Apply modifications to a ticket."""
    if not modifications:
        print_error("No modifications provided")
        raise typer.Exit(1)

    with get_session() as session:
        service = TicketService(session)
        ticket = service.get_by_key(key)

        if ticket is None:
            print_error(f"Ticket not found: {key}")
            raise typer.Exit(1)

        # Parse modifications
        updates = {}
        add_tags = []
        remove_tags = []

        for mod in modifications:
            # Tag syntax: +tag or -tag
            if mod.startswith("+"):
                add_tags.append(mod[1:])
                continue
            elif mod.startswith("-") and ":" not in mod:
                remove_tags.append(mod[1:])
                continue

            # Key:value syntax
            if ":" not in mod:
                print_error(f"Invalid modification format: {mod}")
                raise typer.Exit(1)

            field, value = mod.split(":", 1)
            field = field.lower()

            # Map field names
            field_mapping = {
                "title": "title",
                "desc": "description",
                "description": "description",
                "status": "status",
                "priority": "priority",
                "pri": "priority",
                "assignee": "assignee",
                "due": "due_date",
                "due_date": "due_date",
                "points": "estimate_points",
                "hours": "estimate_hours",
            }

            if field not in field_mapping:
                print_error(f"Unknown field: {field}")
                raise typer.Exit(1)

            mapped_field = field_mapping[field]

            # Parse value based on field type
            if mapped_field == "priority":
                try:
                    value = int(value)
                    if not 1 <= value <= 5:
                        raise ValueError()
                except ValueError:
                    print_error("Priority must be 1-5")
                    raise typer.Exit(1)

            elif mapped_field == "status":
                try:
                    value = TicketStatus(value)
                except ValueError:
                    valid = ", ".join(s.value for s in TicketStatus)
                    print_error(f"Invalid status. Valid values: {valid}")
                    raise typer.Exit(1)

            elif mapped_field == "due_date":
                try:
                    value = parse_date_value(value)
                except ValueError as e:
                    print_error(f"Invalid date: {e}")
                    raise typer.Exit(1)

            elif mapped_field == "estimate_points":
                try:
                    value = int(value)
                except ValueError:
                    print_error("Points must be an integer")
                    raise typer.Exit(1)

            elif mapped_field == "estimate_hours":
                try:
                    value = float(value)
                except ValueError:
                    print_error("Hours must be a number")
                    raise typer.Exit(1)

            updates[mapped_field] = value

        try:
            # Apply updates
            service.update(ticket, **updates)

            # Handle tags
            for tag in add_tags:
                service.add_tag(ticket, tag)
            for tag in remove_tags:
                service.remove_tag(ticket, tag)

            print_success(f"Updated ticket {key}")

        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)


def transition_status(key: str, new_status: TicketStatus) -> None:
    """Transition a ticket to a new status."""
    with get_session() as session:
        service = TicketService(session)
        ticket = service.get_by_key(key)

        if ticket is None:
            print_error(f"Ticket not found: {key}")
            raise typer.Exit(1)

        try:
            service.transition_status(ticket, new_status)
            print_success(f"{key} → {new_status.value}")
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
