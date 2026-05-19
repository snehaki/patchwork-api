"""Rate limiting middleware for patchwork-api.

Provides a simple in-memory rate limiter that can be used as middleware
to restrict how many requests a client (by IP) can make in a time window.
"""

import time
from collections import defaultdict
from threading import Lock
from patchwork.middleware import RequestContext, ResponseContext


class RateLimitExceeded(Exception):
    """Raised when a client exceeds the allowed request rate."""


class RateLimiter:
    """Token-bucket style rate limiter keyed by client address.

    Args:
        max_requests: Maximum number of requests allowed per window.
        window_seconds: Duration of the sliding window in seconds.
    """

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def is_allowed(self, client_key: str) -> bool:
        """Return True if the request is within the rate limit, False otherwise."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            timestamps = self._buckets[client_key]
            # Evict timestamps outside the current window
            self._buckets[client_key] = [t for t in timestamps if t > cutoff]
            if len(self._buckets[client_key]) >= self.max_requests:
                return False
            self._buckets[client_key].append(now)
            return True

    def reset(self, client_key: str) -> None:
        """Clear all recorded timestamps for a given client key."""
        with self._lock:
            self._buckets.pop(client_key, None)


def make_rate_limit_middleware(limiter: RateLimiter):
    """Return a middleware function that enforces the given RateLimiter.

    When a client exceeds the limit the chain is short-circuited and a
    429 response is returned immediately.
    """

    def rate_limit_middleware(
        req: RequestContext, resp: ResponseContext, next_handler
    ) -> ResponseContext:
        client_key = req.client_address or "unknown"
        if not limiter.is_allowed(client_key):
            resp.status = 429
            resp.body = {"error": "rate limit exceeded"}
            resp.headers["Retry-After"] = str(int(limiter.window_seconds))
            return resp
        return next_handler(req, resp)

    rate_limit_middleware.__name__ = "rate_limit_middleware"
    return rate_limit_middleware
