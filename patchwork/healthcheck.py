"""Health-check endpoint support for patchwork-api.

Exposes a lightweight /__patchwork/health route that returns a JSON
summary of the server's current state (uptime, route count, etc.).
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, Optional

_START_TIME: float = time.monotonic()


class HealthCheckError(Exception):
    """Raised when the health-check handler encounters a problem."""


MANAGEMENT_PREFIX = "/__patchwork/health"


def _json_response(data: Any, status: int = 200) -> Dict[str, Any]:
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data),
    }


def _error(message: str, status: int = 400) -> Dict[str, Any]:
    return _json_response({"error": message}, status)


def uptime_seconds() -> float:
    """Return seconds elapsed since the module was first imported."""
    return round(time.monotonic() - _START_TIME, 3)


def handle_health_request(
    method: str,
    path: str,
    registry: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """Return a response dict if *path* targets the health endpoint, else None.

    Parameters
    ----------
    method:   HTTP verb (e.g. "GET").
    path:     Request path, possibly with query string stripped.
    registry: Optional Registry instance used to report route count.
    """
    if not path.rstrip("/") == MANAGEMENT_PREFIX.rstrip("/"):
        return None

    if method.upper() != "GET":
        return _error("method not allowed", 405)

    route_count: int = 0
    if registry is not None:
        try:
            route_count = len(registry.routes())
        except Exception:  # pragma: no cover
            pass

    payload = {
        "status": "ok",
        "uptime_seconds": uptime_seconds(),
        "route_count": route_count,
    }
    return _json_response(payload, 200)
