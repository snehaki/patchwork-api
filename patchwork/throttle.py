"""Request throttling: slow down responses based on a configured delay schedule."""

from __future__ import annotations

import time
from collections import deque
from threading import Lock
from typing import Deque, Dict, Optional, Tuple


class ThrottleError(Exception):
    """Raised when a throttle configuration is invalid."""


def parse_throttle(definition: dict) -> Optional[dict]:
    """Extract and validate the ``throttle`` block from a route definition.

    Returns ``None`` when no throttle block is present.
    """
    raw = definition.get("throttle")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ThrottleError("throttle must be a mapping")

    rate = raw.get("rate")
    if rate is None:
        raise ThrottleError("throttle.rate is required")
    if not isinstance(rate, (int, float)) or isinstance(rate, bool):
        raise ThrottleError("throttle.rate must be a number (requests per second)")
    if rate <= 0:
        raise ThrottleError("throttle.rate must be greater than zero")

    burst = raw.get("burst", 1)
    if not isinstance(burst, int) or isinstance(burst, bool) or burst < 1:
        raise ThrottleError("throttle.burst must be a positive integer")

    return {"rate": float(rate), "burst": int(burst)}


class _TokenBucket:
    """Token-bucket implementation for a single key."""

    def __init__(self, rate: float, burst: int) -> None:
        self._rate = rate          # tokens per second
        self._burst = burst        # max tokens
        self._tokens: float = burst
        self._last: float = time.monotonic()
        self._lock = Lock()

    def consume(self) -> Tuple[bool, float]:
        """Try to consume one token.

        Returns ``(allowed, retry_after)`` where *retry_after* is the number
        of seconds the caller should wait when *allowed* is ``False``.
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            self._last = now
            self._tokens = min(self._burst, self._tokens + elapsed * self._rate)
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True, 0.0
            retry_after = (1.0 - self._tokens) / self._rate
            return False, retry_after


_buckets: Dict[str, _TokenBucket] = {}
_buckets_lock = Lock()


def _get_bucket(key: str, rate: float, burst: int) -> _TokenBucket:
    with _buckets_lock:
        if key not in _buckets:
            _buckets[key] = _TokenBucket(rate, burst)
        return _buckets[key]


def check_throttle(config: dict, client_ip: str, route_key: str) -> Tuple[bool, float]:
    """Check whether *client_ip* is allowed to proceed for *route_key*.

    Returns ``(allowed, retry_after_seconds)``.
    """
    key = f"{route_key}::{client_ip}"
    bucket = _get_bucket(key, config["rate"], config["burst"])
    return bucket.consume()


def reset_throttle() -> None:
    """Clear all throttle state (intended for tests)."""
    with _buckets_lock:
        _buckets.clear()
