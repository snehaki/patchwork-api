"""Management routes for inspecting the transform pipeline.

All routes live under ``/__patchwork__/transforms``.

GET  /__patchwork__/transforms
    Return a JSON list of every registered route that declares transforms,
    together with the transforms defined for that route.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from patchwork.registry import Registry

_PREFIX = "/__patchwork__/transforms"


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


def handle_transform_request(
    method: str,
    path: str,
    registry: "Registry",
) -> dict | None:
    """Return a response dict if *path* is a transform management route.

    Returns ``None`` for any path that is not under ``_PREFIX`` so the
    normal routing logic can proceed.
    """
    if not path.startswith(_PREFIX):
        return None

    if method != "GET":
        return _error(405, "Method Not Allowed")

    sub = path[len(_PREFIX):]

    if sub in ("", "/"):
        # List all routes that have at least one transform defined.
        result = []
        for defn in registry.all():
            transforms = defn.get("transforms") or []
            if transforms:
                result.append(
                    {
                        "method": defn.get("method"),
                        "path": defn.get("path"),
                        "transforms": transforms,
                    }
                )
        return _json_response(result)

    return _error(404, f"Unknown transform management path: {sub!r}")
