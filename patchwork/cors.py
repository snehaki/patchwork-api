"""CORS (Cross-Origin Resource Sharing) configuration and header helpers."""

from __future__ import annotations

from typing import Dict, List, Optional


class CORSError(Exception):
    """Raised when a CORS configuration is invalid."""


_DEFAULT_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
_DEFAULT_HEADERS = ["Content-Type", "Authorization"]


def parse_cors(raw: object) -> Optional[Dict]:
    """Parse a 'cors' block from a route definition.

    Returns None if *raw* is None/absent, otherwise returns a validated
    config dict with normalised keys.
    """
    if raw is None:
        return None

    if not isinstance(raw, dict):
        raise CORSError("'cors' must be a mapping")

    origins = raw.get("origins", ["*"])
    if not isinstance(origins, list) or not all(isinstance(o, str) for o in origins):
        raise CORSError("'cors.origins' must be a list of strings")
    if not origins:
        raise CORSError("'cors.origins' must not be empty")

    methods = raw.get("methods", _DEFAULT_METHODS)
    if not isinstance(methods, list) or not all(isinstance(m, str) for m in methods):
        raise CORSError("'cors.methods' must be a list of strings")

    headers = raw.get("headers", _DEFAULT_HEADERS)
    if not isinstance(headers, list) or not all(isinstance(h, str) for h in headers):
        raise CORSError("'cors.headers' must be a list of strings")

    max_age = raw.get("max_age", None)
    if max_age is not None:
        if not isinstance(max_age, (int, float)) or max_age < 0:
            raise CORSError("'cors.max_age' must be a non-negative number")

    allow_credentials = raw.get("allow_credentials", False)
    if not isinstance(allow_credentials, bool):
        raise CORSError("'cors.allow_credentials' must be a boolean")

    return {
        "origins": origins,
        "methods": [m.upper() for m in methods],
        "headers": headers,
        "max_age": float(max_age) if max_age is not None else None,
        "allow_credentials": allow_credentials,
    }


def build_cors_headers(
    config: Dict,
    request_origin: Optional[str] = None,
) -> Dict[str, str]:
    """Return a dict of CORS response headers for *config*.

    If *request_origin* is provided and matches the allowed origins (or '*' is
    allowed) the specific origin is reflected; otherwise the first allowed
    origin is used.
    """
    origins: List[str] = config["origins"]

    if "*" in origins:
        origin_value = "*"
    elif request_origin and request_origin in origins:
        origin_value = request_origin
    else:
        origin_value = origins[0]

    headers: Dict[str, str] = {
        "Access-Control-Allow-Origin": origin_value,
        "Access-Control-Allow-Methods": ", ".join(config["methods"]),
        "Access-Control-Allow-Headers": ", ".join(config["headers"]),
    }

    if config.get("allow_credentials"):
        headers["Access-Control-Allow-Credentials"] = "true"

    if config.get("max_age") is not None:
        headers["Access-Control-Max-Age"] = str(int(config["max_age"]))

    return headers
