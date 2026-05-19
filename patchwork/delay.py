"""Response delay simulation for patchwork-api."""

import time
from typing import Optional


class DelayError(Exception):
    """Raised when delay configuration is invalid."""


def parse_delay(value) -> Optional[float]:
    """Parse and validate a delay value (in seconds).

    Accepts int, float, or None. Raises DelayError for negative or
    non-numeric values.
    """
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise DelayError(
            f"delay must be a number (int or float), got {type(value).__name__!r}"
        )
    if value < 0:
        raise DelayError(f"delay must be >= 0, got {value}")
    return float(value)


def apply_delay(seconds: Optional[float]) -> None:
    """Block for the given number of seconds, if any."""
    if seconds and seconds > 0:
        time.sleep(seconds)


def get_response_delay(definition: dict) -> Optional[float]:
    """Extract and validate the 'delay' field from a response definition.

    Returns None if no delay is specified.
    Raises DelayError if the value is present but invalid.
    """
    raw = definition.get("delay")
    return parse_delay(raw)
