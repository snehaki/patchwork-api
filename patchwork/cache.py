"""Simple in-memory response cache with TTL support."""

import time
from typing import Any, Dict, Optional, Tuple


class CacheError(Exception):
    """Raised when cache configuration is invalid."""


_store: Dict[str, Tuple[Any, float]] = {}


def parse_cache(definition: dict) -> Optional[float]:
    """Extract and validate the cache TTL (in seconds) from a route definition.

    Returns None if caching is not configured.
    Raises CacheError for invalid values.
    """
    raw = definition.get("cache")
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise CacheError(
            f"'cache' must be a non-negative number (seconds), got {raw!r}"
        )
    ttl = float(raw)
    if ttl < 0:
        raise CacheError(
            f"'cache' TTL must be >= 0, got {ttl}"
        )
    return ttl


def make_key(method: str, path: str, query: str = "") -> str:
    """Build a cache key from request components."""
    return f"{method.upper()}:{path}:{query}"


def get(key: str) -> Optional[Any]:
    """Return cached value if present and not expired, else None."""
    entry = _store.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.monotonic() > expires_at:
        del _store[key]
        return None
    return value


def put(key: str, value: Any, ttl: float) -> None:
    """Store a value in the cache with the given TTL."""
    if ttl <= 0:
        return
    _store[key] = (value, time.monotonic() + ttl)


def invalidate(key: str) -> None:
    """Remove a single entry from the cache."""
    _store.pop(key, None)


def clear() -> None:
    """Remove all entries from the cache."""
    _store.clear()


def size() -> int:
    """Return the number of entries currently in the cache (including expired)."""
    return len(_store)
