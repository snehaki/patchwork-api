"""Management route handler for /_patchwork/metrics."""

import json
from typing import Optional

from patchwork.metrics import snapshot, reset

_PREFIX = "/_patchwork/metrics"


def _json_response(data) -> dict:
    return {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data),
    }


def _error(status: int, message: str) -> dict:
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


def handle_metrics_request(method: str, path: str, body: bytes = b"") -> Optional[dict]:
    """Return a response dict if path is a metrics management route, else None."""
    if not path.startswith(_PREFIX):
        return None

    sub = path[len(_PREFIX):].rstrip("/") or "/"

    if sub == "/" or sub == "":
        if method == "GET":
            return _json_response(snapshot())
        if method == "DELETE":
            reset()
            return _json_response({"reset": True})
        return _error(405, f"Method {method} not allowed")

    return _error(404, f"Unknown metrics sub-path: {sub}")
