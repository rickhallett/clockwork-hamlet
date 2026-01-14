"""Parse filter expressions like 'status:todo', '+urgent', 'due.before:1w'."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import re

from sqlalchemy.orm import Session, Query

from ticket_manager.db.models import Ticket, Tag
from ticket_manager.filters.date_parser import parse_date_value


class FilterOperator(str, Enum):
    """Filter comparison operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not"
    CONTAINS = "contains"
    BEFORE = "before"
    AFTER = "after"
    HAS_TAG = "has_tag"
    NOT_TAG = "not_tag"


@dataclass
class FilterExpression:
    """A parsed filter expression."""
    field: str
    operator: FilterOperator
    value: str


def parse_filter(filter_str: str) -> FilterExpression:
    """Parse a single filter expression.

    Supported formats:
        - "status:todo" -> status equals todo
        - "status.not:done" -> status not equals done
        - "due.before:1w" -> due_date before 1 week
        - "due.after:today" -> due_date after today
        - "title.contains:bug" -> title contains bug
        - "+urgent" -> has tag urgent
        - "-wontfix" -> does not have tag wontfix
        - "project:ACME" -> project equals ACME

    Args:
        filter_str: Filter string to parse

    Returns:
        Parsed FilterExpression

    Raises:
        ValueError: If format is invalid
    """
    filter_str = filter_str.strip()

    # Tag syntax: +tag or -tag
    if filter_str.startswith("+"):
        return FilterExpression("tag", FilterOperator.HAS_TAG, filter_str[1:])
    if filter_str.startswith("-") and ":" not in filter_str:
        return FilterExpression("tag", FilterOperator.NOT_TAG, filter_str[1:])

    # Modifier syntax: field.modifier:value
    modifier_match = re.match(r"^(\w+)\.(\w+):(.+)$", filter_str)
    if modifier_match:
        field, modifier, value = modifier_match.groups()

        modifier_mapping = {
            "not": FilterOperator.NOT_EQUALS,
            "contains": FilterOperator.CONTAINS,
            "has": FilterOperator.CONTAINS,
            "before": FilterOperator.BEFORE,
            "after": FilterOperator.AFTER,
            "is": FilterOperator.EQUALS,
            "equals": FilterOperator.EQUALS,
        }

        if modifier not in modifier_mapping:
            raise ValueError(f"Unknown modifier: {modifier}")

        return FilterExpression(field, modifier_mapping[modifier], value)

    # Simple syntax: field:value
    simple_match = re.match(r"^(\w+):(.+)$", filter_str)
    if simple_match:
        field, value = simple_match.groups()
        return FilterExpression(field, FilterOperator.EQUALS, value)

    raise ValueError(f"Invalid filter format: {filter_str}")


def parse_filters(filters: List[str]) -> List[FilterExpression]:
    """Parse multiple filter expressions.

    Args:
        filters: List of filter strings

    Returns:
        List of parsed FilterExpressions
    """
    return [parse_filter(f) for f in filters]


def apply_filters(query: Query, filters: List[FilterExpression], session: Session) -> Query:
    """Apply filter expressions to a SQLAlchemy query.

    Args:
        query: Base query
        filters: List of filter expressions
        session: Database session

    Returns:
        Modified query with filters applied
    """
    for expr in filters:
        query = apply_filter(query, expr, session)
    return query


def apply_filter(query: Query, expr: FilterExpression, session: Session) -> Query:
    """Apply a single filter expression to a query.

    Args:
        query: Base query
        expr: Filter expression
        session: Database session

    Returns:
        Modified query
    """
    field = expr.field.lower()
    value = expr.value

    # Map field aliases
    field_mapping = {
        "type": "type",
        "status": "status",
        "priority": "priority",
        "pri": "priority",
        "project": "project",
        "proj": "project",
        "assignee": "assignee",
        "reporter": "reporter",
        "title": "title",
        "description": "description",
        "desc": "description",
        "due": "due_date",
        "due_date": "due_date",
        "created": "created_at",
        "created_at": "created_at",
        "updated": "updated_at",
        "updated_at": "updated_at",
        "parent": "parent_id",
        "points": "estimate_points",
        "hours": "estimate_hours",
    }

    # Handle tag filters
    if expr.operator == FilterOperator.HAS_TAG:
        tag = session.query(Tag).filter(Tag.name == value.lower()).first()
        if tag:
            query = query.filter(Ticket.tags.contains(tag))
        else:
            # Tag doesn't exist, no matches
            query = query.filter(False)
        return query

    if expr.operator == FilterOperator.NOT_TAG:
        tag = session.query(Tag).filter(Tag.name == value.lower()).first()
        if tag:
            query = query.filter(~Ticket.tags.contains(tag))
        return query

    # Map field name
    if field not in field_mapping and field != "tag":
        raise ValueError(f"Unknown field: {field}")

    mapped_field = field_mapping.get(field, field)
    column = getattr(Ticket, mapped_field, None)

    if column is None:
        raise ValueError(f"Unknown field: {field}")

    # Apply operator
    if expr.operator == FilterOperator.EQUALS:
        # Handle special cases
        if mapped_field == "priority":
            # Support comma-separated values: priority:1,2
            if "," in value:
                values = [int(v) for v in value.split(",")]
                return query.filter(column.in_(values))
            return query.filter(column == int(value))

        if mapped_field == "project":
            return query.filter(column == value.upper())

        return query.filter(column == value)

    elif expr.operator == FilterOperator.NOT_EQUALS:
        if mapped_field == "priority":
            return query.filter(column != int(value))
        if mapped_field == "project":
            return query.filter(column != value.upper())
        return query.filter(column != value)

    elif expr.operator == FilterOperator.CONTAINS:
        return query.filter(column.ilike(f"%{value}%"))

    elif expr.operator == FilterOperator.BEFORE:
        if mapped_field in ("due_date", "created_at", "updated_at"):
            date_value = parse_date_value(value)
            return query.filter(column < date_value)
        if mapped_field == "priority":
            return query.filter(column < int(value))
        raise ValueError(f"Cannot use 'before' with field: {field}")

    elif expr.operator == FilterOperator.AFTER:
        if mapped_field in ("due_date", "created_at", "updated_at"):
            date_value = parse_date_value(value)
            return query.filter(column > date_value)
        if mapped_field == "priority":
            return query.filter(column > int(value))
        raise ValueError(f"Cannot use 'after' with field: {field}")

    return query
