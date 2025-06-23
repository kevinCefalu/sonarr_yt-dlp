"""Date and time utilities."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Union, Any


logger = logging.getLogger(__name__)


def apply_time_offset(base_date: datetime, offset: Dict[str, Any]) -> datetime:
    """Apply time offset to a datetime object.

    Args:
        base_date: The base datetime to modify.
        offset: Dictionary containing offset values (weeks, days, hours, minutes).

    Returns:
        Modified datetime with offset applied.
    """
    if not offset:
        return base_date

    try:
        weeks = int(offset.get('weeks', 0))
        days = int(offset.get('days', 0))
        hours = int(offset.get('hours', 0))
        minutes = int(offset.get('minutes', 0))

        delta = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes)
        result = base_date + delta

        if delta != timedelta():
            logger.debug("Applied offset to %s: %s -> %s",
                        base_date, delta, result)

        return result

    except (ValueError, TypeError) as e:
        logger.error("Invalid offset values %s: %s", offset, e)
        return base_date


def parse_air_date(date_string: str) -> datetime:
    """Parse air date string from Sonarr API.

    Args:
        date_string: Date string in ISO format.

    Returns:
        Parsed datetime object.

    Raises:
        ValueError: If date string cannot be parsed.
    """
    try:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as e:
        logger.error("Failed to parse date '%s': %s", date_string, e)
        raise
