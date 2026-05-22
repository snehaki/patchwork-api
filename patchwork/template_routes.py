"""Management routes for inspecting available template variables.

Mounts under /_patchwork/template/ and is handled before normal route
matching, similar to scenario_routes.py.
"""

import json
from typing import Optional

MANAGEMENT_PREFIX = "/_patchwork/template"

_AVAILABLE_VARIABLES = [
    {"placeholder": "{{ request.method }}", "description": "HTTP method (upper-case)"},
    {"placeholder": "{{ request.path }}", "description": "Request path"},
    {"placeholder": "{{ request.params.NAME }}", "description": "URL path parameter"},
    {"placeholder": "{{ request.headers.NAME }}", "description": "Request header value"},
]


def _json_response(data, status: int = 200) -> dict:
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data),
    }


def _error(message: str, status: int = 400) -> dict:
    return _json_response({"error": message}, status)


def handle_template_request(method: str, path: str) -> Optional[dict]:
    """Return a response dict if *path* is a template management route.

    Returns *None* for all other paths so the caller can fall through to
    normal route matching.
    """
    if not path.startswith(MANAGEMENT_PREFIX):
        return None

    sub = path[len(MANAGEMENT_PREFIX):].rstrip("/")

    if method != "GET":
        return _error("method not allowed", 405)

    if sub == "" or sub == "/variables":
        return _json_response({"variables": _AVAILABLE_VARIABLES})

    return _error(f"unknown template management route: {path}", 404)
