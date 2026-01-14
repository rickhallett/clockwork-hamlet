"""Parse date values like 'today', 'tomorrow', '1w', etc."""

from datetime import date, timedelta
import re


def parse_date_value(value: str) -> date:
    """Parse a date value.

    Supported formats:
        - today, tomorrow, yesterday
        - ISO format: 2024-01-15
        - Relative: 1d, 2w, 3m (days, weeks, months)
        - Named: eow (end of week), eom (end of month), eoy (end of year)
        - Weekdays: mon, tue, wed, thu, fri, sat, sun

    Args:
        value: Date string to parse

    Returns:
        Parsed date

    Raises:
        ValueError: If format is not recognized
    """
    value = value.lower().strip()
    today = date.today()

    # Named dates
    if value == "today":
        return today
    elif value == "tomorrow":
        return today + timedelta(days=1)
    elif value == "yesterday":
        return today - timedelta(days=1)

    # End of period
    if value == "eow":  # End of week (Friday)
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0 and today.weekday() != 4:
            days_until_friday = 7
        return today + timedelta(days=days_until_friday)

    elif value == "eom":  # End of month
        if today.month == 12:
            return date(today.year + 1, 1, 1) - timedelta(days=1)
        return date(today.year, today.month + 1, 1) - timedelta(days=1)

    elif value == "eoy":  # End of year
        return date(today.year, 12, 31)

    # Start of period
    if value == "sow":  # Start of week (Monday)
        days_since_monday = today.weekday()
        return today - timedelta(days=days_since_monday) + timedelta(days=7)

    elif value == "som":  # Start of next month
        if today.month == 12:
            return date(today.year + 1, 1, 1)
        return date(today.year, today.month + 1, 1)

    # Weekday names (next occurrence)
    weekdays = {
        "mon": 0, "monday": 0,
        "tue": 1, "tuesday": 1,
        "wed": 2, "wednesday": 2,
        "thu": 3, "thursday": 3,
        "fri": 4, "friday": 4,
        "sat": 5, "saturday": 5,
        "sun": 6, "sunday": 6,
    }
    if value in weekdays:
        target_day = weekdays[value]
        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)

    # Relative dates: 1d, 2w, 3m
    relative_match = re.match(r"^(\d+)(d|w|m|y)$", value)
    if relative_match:
        amount = int(relative_match.group(1))
        unit = relative_match.group(2)

        if unit == "d":
            return today + timedelta(days=amount)
        elif unit == "w":
            return today + timedelta(weeks=amount)
        elif unit == "m":
            # Add months (approximate)
            new_month = today.month + amount
            new_year = today.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            # Handle day overflow (e.g., Jan 31 + 1m)
            try:
                return date(new_year, new_month, today.day)
            except ValueError:
                # Day doesn't exist in target month, use last day
                if new_month == 12:
                    return date(new_year + 1, 1, 1) - timedelta(days=1)
                return date(new_year, new_month + 1, 1) - timedelta(days=1)
        elif unit == "y":
            try:
                return date(today.year + amount, today.month, today.day)
            except ValueError:
                # Feb 29 in non-leap year
                return date(today.year + amount, today.month, 28)

    # ISO format: 2024-01-15
    try:
        return date.fromisoformat(value)
    except ValueError:
        pass

    # Slash format: 1/15/2024 or 15/1/2024
    slash_match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", value)
    if slash_match:
        # Try both MM/DD/YYYY and DD/MM/YYYY
        g1, g2, year = int(slash_match.group(1)), int(slash_match.group(2)), int(slash_match.group(3))
        try:
            return date(year, g1, g2)  # MM/DD/YYYY
        except ValueError:
            try:
                return date(year, g2, g1)  # DD/MM/YYYY
            except ValueError:
                pass

    raise ValueError(f"Unable to parse date: {value}")


def format_relative_date(d: date) -> str:
    """Format a date relative to today.

    Args:
        d: Date to format

    Returns:
        Human-readable relative date string
    """
    today = date.today()
    delta = (d - today).days

    if delta == 0:
        return "today"
    elif delta == 1:
        return "tomorrow"
    elif delta == -1:
        return "yesterday"
    elif -7 <= delta < 0:
        return f"{-delta} days ago"
    elif 0 < delta <= 7:
        return f"in {delta} days"
    elif delta < 0:
        weeks = (-delta) // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} ago"
    else:
        weeks = delta // 7
        return f"in {weeks} week{'s' if weeks > 1 else ''}"
