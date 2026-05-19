"""Build HTTP response data from a matched route definition."""

import json
from typing import Any

from patchwork.delay import apply_delay, get_response_delay


def _substitute_params(value: Any, params: dict) -> Any:
    """Recursively substitute {param} placeholders in strings."""
    if isinstance(value, str):
        return replacer(value, params)
    if isinstance(value, dict):
        return {k: _substitute_params(v, params) for k, v in value.items()}
    if isinstance(value, list):
        return [_substitute_params(item, params) for item in value]
    return value


def replacer(template: str, params: dict) -> str:
    """Replace {key} tokens in *template* using *params*.

    Unknown keys are left as-is.
    """
    def _replace(key: str) -> str:
        return str(params[key]) if key in params else "{" + key + "}"

    import re
    return re.sub(r"\{(\w+)\}", lambda m: _replace(m.group(1)), template)


def build_response(definition: dict, params: dict) -> dict:
    """Construct a response dict from a route *definition* and path *params*.

    Applies any configured delay before returning.

    Returns a dict with keys:
      - status  (int)
      - headers (dict)
      - body    (bytes)
    """
    delay = get_response_delay(definition)
    apply_delay(delay)

    status: int = definition.get("status", 200)
    headers: dict = dict(definition.get("headers", {}))
    raw_body = definition.get("body", "")

    substituted = _substitute_params(raw_body, params)

    if isinstance(substituted, (dict, list)):
        body_bytes = json.dumps(substituted).encode()
        headers.setdefault("Content-Type", "application/json")
    else:
        body_bytes = str(substituted).encode()

    return {
        "status": status,
        "headers": headers,
        "body": body_bytes,
    }
