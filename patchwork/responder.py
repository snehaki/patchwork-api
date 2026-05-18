"""Build HTTP responses from a matched route definition.

The responder takes a MatchResult (or a raw definition dict) and
produces the status code, headers, and JSON-encoded body that the
server should send back to the client.
"""

import json
from typing import Tuple

from patchwork.matcher import MatchResult


DEFAULT_CONTENT_TYPE = "application/json"


def build_response(
    match: MatchResult,
) -> Tuple[int, dict, bytes]:
    """Return (status_code, headers, body_bytes) for a matched definition.

    Path parameters extracted during matching are substituted into string
    values inside the body using Python str.format_map so that definitions
    can reference {id} etc. in their response bodies.
    """
    defn = match.definition
    params = match.params

    status: int = int(defn.get("status", 200))

    # Merge default headers with any declared in the definition
    headers: dict = {"Content-Type": DEFAULT_CONTENT_TYPE}
    for key, value in defn.get("headers", {}).items():
        headers[key] = str(value)

    raw_body = defn.get("body", {})
    resolved_body = _substitute_params(raw_body, params)

    body_bytes: bytes = json.dumps(resolved_body, indent=2).encode("utf-8")
    headers["Content-Length"] = str(len(body_bytes))

    return status, headers, body_bytes


def _substitute_params(obj, params: dict):
    """Recursively replace {param} placeholders in string values."""
    if isinstance(obj, str):
        try:
            return obj.format_map(params)
        except (KeyError, ValueError):
            return obj
    if isinstance(obj, dict):
        return {k: _substitute_params(v, params) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_params(item, params) for item in obj]
    return obj
