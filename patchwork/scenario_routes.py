"""Built-in HTTP management routes for controlling scenarios at runtime.

These are registered automatically by the server when scenario support is
enabled. All paths are prefixed with ``/_patchwork/scenario/``.
"""

from __future__ import annotations

import json
from typing import Any, Dict, Optional, Tuple

from patchwork.scenario import (
    ScenarioError,
    advance_scenario,
    reset_scenario,
    set_state,
    _state as _current_states,
    _registry as _scenario_registry,
)

_PREFIX = "/_patchwork/scenario/"


def _json_response(
    body: Any, status: int = 200
) -> Tuple[int, Dict[str, str], bytes]:
    payload = json.dumps(body).encode()
    return status, {"Content-Type": "application/json"}, payload


def _error(message: str, status: int = 400) -> Tuple[int, Dict[str, str], bytes]:
    return _json_response({"error": message}, status)


def handle_scenario_request(
    method: str, path: str, body: bytes
) -> Optional[Tuple[int, Dict[str, str], bytes]]:
    """Dispatch a management request.

    Returns ``(status, headers, body)`` if the path is a management route,
    otherwise returns ``None`` so the caller can fall through to normal
    route matching.
    """
    if not path.startswith(_PREFIX):
        return None

    tail = path[len(_PREFIX):].strip("/")
    parts = tail.split("/", 1)
    name = parts[0]
    action = parts[1] if len(parts) > 1 else ""

    if not name:
        if method == "GET":
            return _json_response(
                {"scenarios": {n: _current_states[n] for n in _scenario_registry}}
            )
        return _error("Method not allowed", 405)

    if name not in _scenario_registry:
        return _error(f"Unknown scenario '{name}'", 404)

    if action == "advance" and method == "POST":
        try:
            new_state = advance_scenario(name)
            return _json_response({"scenario": name, "state": new_state})
        except ScenarioError as exc:
            return _error(str(exc))

    if action == "reset" and method == "POST":
        reset_scenario(name)
        return _json_response({"scenario": name, "state": _current_states[name]})

    if action == "state" and method == "POST":
        try:
            data = json.loads(body) if body else {}
        except json.JSONDecodeError:
            return _error("Invalid JSON body")
        state = data.get("state", "")
        if not state:
            return _error("'state' field is required")
        try:
            set_state(name, state)
            return _json_response({"scenario": name, "state": state})
        except ScenarioError as exc:
            return _error(str(exc))

    if action == "" and method == "GET":
        return _json_response(
            {"scenario": name, "state": _current_states[name]}
        )

    return _error("Not found", 404)
