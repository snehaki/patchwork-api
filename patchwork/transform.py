"""Response body transformation pipeline.

Allows definitions to declare a list of transforms applied to the
response body before it is sent to the client.

Supported transforms
--------------------
- ``uppercase``  – convert every string value to upper-case
- ``lowercase``  – convert every string value to lower-case
- ``wrap``       – wrap the body in ``{"data": <body>}``
- ``omit_keys``  – remove listed keys from a mapping body
"""

from __future__ import annotations

from typing import Any


class TransformError(Exception):
    """Raised when a transform definition is invalid or cannot be applied."""


_KNOWN_TRANSFORMS = {"uppercase", "lowercase", "wrap", "omit_keys"}


def parse_transforms(raw: Any) -> list[dict]:
    """Validate and normalise the *transforms* value from a definition.

    *raw* may be ``None`` (no transforms) or a list of mapping objects.
    Each mapping must contain at least a ``type`` key.
    """
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise TransformError("'transforms' must be a list")
    result: list[dict] = []
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TransformError(f"transform[{idx}] must be a mapping")
        t = item.get("type")
        if not isinstance(t, str) or t not in _KNOWN_TRANSFORMS:
            raise TransformError(
                f"transform[{idx}] has unknown type {t!r}; "
                f"must be one of {sorted(_KNOWN_TRANSFORMS)}"
            )
        result.append(dict(item))
    return result


def _apply_one(body: Any, transform: dict) -> Any:
    t = transform["type"]
    if t == "uppercase":
        return _map_strings(body, str.upper)
    if t == "lowercase":
        return _map_strings(body, str.lower)
    if t == "wrap":
        return {"data": body}
    if t == "omit_keys":
        keys = transform.get("keys", [])
        if not isinstance(body, dict):
            return body
        return {k: v for k, v in body.items() if k not in keys}
    raise TransformError(f"Unknown transform type: {t!r}")  # pragma: no cover


def _map_strings(value: Any, fn) -> Any:
    if isinstance(value, str):
        return fn(value)
    if isinstance(value, dict):
        return {k: _map_strings(v, fn) for k, v in value.items()}
    if isinstance(value, list):
        return [_map_strings(v, fn) for v in value]
    return value


def apply_transforms(body: Any, transforms: list[dict]) -> Any:
    """Apply *transforms* sequentially to *body* and return the result."""
    for t in transforms:
        body = _apply_one(body, t)
    return body
