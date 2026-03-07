"""Human-friendly duration parsing utilities."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

_PATTERN = re.compile(r"^(?P<value>\d+)(?P<unit>[mhdw])$")

_UNIT_TO_SECONDS: dict[str, int] = {
    "m": 60,
    "h": 3600,
    "d": 86400,
    "w": 604800,
}


def parse_since(value: str) -> datetime:
    """
    Parse a human duration string into an aware datetime.

    Accepted formats:
        30m   → 30 minutes ago
        2h    → 2 hours ago
        1d    → 1 day ago
        1w    → 1 week ago

    Raises ValueError for unrecognised formats.
    """
    match = _PATTERN.match(value.strip().lower())
    if not match:
        raise ValueError(
            f"Cannot parse duration '{value}'. "
            "Expected format: <number><unit> where unit is m, h, d, or w. "
            "Examples: 30m, 2h, 1d, 1w."
        )
    amount = int(match.group("value"))
    unit = match.group("unit")
    delta = timedelta(seconds=amount * _UNIT_TO_SECONDS[unit])
    return datetime.now(tz=UTC) - delta
