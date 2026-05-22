"""Response body templating using Jinja2-style {{ variable }} syntax.

Supports injecting request metadata (method, path, headers, params)
into response bodies defined in YAML fixtures.
"""

import re
from typing import Any

_TEMPLATE_RE = re.compile(r"\{\{\s*([\w.]+)\s*\}\}")


class TemplateError(Exception):
    """Raised when a template cannot be rendered."""


def _resolve_dotted(key: str, context: dict) -> Any:
    """Resolve a dotted key like 'request.method' from a nested context dict."""
    parts = key.split(".")
    value = context
    for part in parts:
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def render_template(text: str, context: dict) -> str:
    """Replace {{ key }} placeholders in *text* using *context*.

    Unknown keys are left unchanged.  Non-string values are converted with
    str() before substitution.
    """
    if not isinstance(text, str):
        raise TemplateError(f"render_template expects a str, got {type(text).__name__}")

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        value = _resolve_dotted(key, context)
        if value is None:
            return match.group(0)  # leave unchanged
        return str(value)

    return _TEMPLATE_RE.sub(replacer, text)


def render_value(value: Any, context: dict) -> Any:
    """Recursively render templates in *value* (str, dict, or list)."""
    if isinstance(value, str):
        return render_template(value, context)
    if isinstance(value, dict):
        return {k: render_value(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [render_value(item, context) for item in value]
    return value


def build_template_context(method: str, path: str, headers: dict, params: dict) -> dict:
    """Build the context dict passed to render_value."""
    return {
        "request": {
            "method": method.upper(),
            "path": path,
            "headers": headers,
            "params": params,
        }
    }
