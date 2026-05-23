"""Request metrics collection: counts, latencies, and status code tracking."""

import time
import threading
from collections import defaultdict
from typing import Dict, Optional


class MetricsError(Exception):
    pass


_lock = threading.Lock()
_data: Dict[str, dict] = {}  # keyed by "METHOD /path"


def _key(method: str, path: str) -> str:
    return f"{method.upper()} {path}"


def record(method: str, path: str, status: int, elapsed: float) -> None:
    """Record a completed request."""
    if elapsed < 0:
        raise MetricsError(f"elapsed must be non-negative, got {elapsed}")
    k = _key(method, path)
    with _lock:
        if k not in _data:
            _data[k] = {"count": 0, "total_ms": 0.0, "statuses": defaultdict(int)}
        entry = _data[k]
        entry["count"] += 1
        entry["total_ms"] += elapsed * 1000
        entry["statuses"][str(status)] += 1


def snapshot() -> dict:
    """Return a copy of all collected metrics."""
    with _lock:
        result = {}
        for k, v in _data.items():
            result[k] = {
                "count": v["count"],
                "total_ms": round(v["total_ms"], 3),
                "avg_ms": round(v["total_ms"] / v["count"], 3) if v["count"] else 0.0,
                "statuses": dict(v["statuses"]),
            }
        return result


def reset() -> None:
    """Clear all recorded metrics (useful for testing)."""
    with _lock:
        _data.clear()


class Timer:
    """Context manager that records a request's elapsed time on exit."""

    def __init__(self, method: str, path: str):
        self.method = method
        self.path = path
        self._start: Optional[float] = None
        self.status: int = 200

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *_) -> None:
        elapsed = time.perf_counter() - self._start
        record(self.method, self.path, self.status, elapsed)
