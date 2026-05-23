"""Circuit breaker for proxy upstream failures."""

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


class CircuitBreakerError(Exception):
    """Raised when a circuit is open and the request is rejected."""


_STATES = ("closed", "open", "half-open")


@dataclass
class _Circuit:
    failures: int = 0
    opened_at: Optional[float] = None
    state: str = "closed"


# Module-level registry: key -> _Circuit
_circuits: Dict[str, _Circuit] = {}


def _get(key: str) -> _Circuit:
    if key not in _circuits:
        _circuits[key] = _Circuit()
    return _circuits[key]


def record_success(key: str) -> None:
    """Record a successful call; reset the circuit to closed."""
    c = _get(key)
    c.failures = 0
    c.opened_at = None
    c.state = "closed"


def record_failure(key: str, threshold: int = 3) -> None:
    """Record a failed call; open the circuit when threshold is reached."""
    c = _get(key)
    c.failures += 1
    if c.failures >= threshold and c.state == "closed":
        c.state = "open"
        c.opened_at = time.monotonic()


def is_allowed(key: str, timeout: float = 30.0) -> bool:
    """Return True if a request is allowed through.

    A closed circuit always allows requests.  An open circuit blocks
    requests until *timeout* seconds have elapsed, after which it
    transitions to half-open and allows one probe request through.
    """
    c = _get(key)
    if c.state == "closed":
        return True
    if c.state == "open":
        if c.opened_at is not None and (time.monotonic() - c.opened_at) >= timeout:
            c.state = "half-open"
            return True
        return False
    # half-open: allow exactly one probe
    return True


def get_state(key: str) -> str:
    """Return the current state string for *key*."""
    return _get(key).state


def reset(key: str) -> None:
    """Fully reset the circuit for *key*."""
    _circuits.pop(key, None)


def reset_all() -> None:
    """Reset every circuit (useful in tests)."""
    _circuits.clear()
