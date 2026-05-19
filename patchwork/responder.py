import json
import re
from typing import Any


def _substitute_params(template: Any, params: dict) -> Any:
    """Recursively substitute path parameters in response body values."""
    if isinstance(template, str):
        def replacer(match):
            key = match.group(1)
            return str(params.get(key, match.group(0)))
        return re.sub(r"\{(\w+)\}", replacer, template)
    if isinstance(template, dict):
        return {k: _substitute_params(v, params) for k, v in template.items()}
    if isinstance(template, list):
        return [_substitute_params(item, params) for item in template]
    return template


def build_response(definition: dict, params: dict) -> dict:
    """Build a response dict from a route definition and matched path params.

    Returns a dict with keys:
      - status  (int)
      - headers (dict)
      - body    (bytes)
    """
    status: int = definition.get("status", 200)

    raw_body = definition.get("body", "")
    substituted = _substitute_params(raw_body, params)

    headers: dict = dict(definition.get("headers", {}))

    if isinstance(substituted, (dict, list)):
        body_bytes = json.dumps(substituted, indent=2).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")
    else:
        body_str = str(substituted) if substituted is not None else ""
        body_bytes = body_str.encode("utf-8")
        headers.setdefault("Content-Type", "text/plain")

    return {
        "status": status,
        "headers": headers,
        "body": body_bytes,
    }
