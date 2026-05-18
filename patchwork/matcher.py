"""Route matching logic for patchwork-api.

Supports exact path matching and simple path parameter extraction
using {param} syntax in route definitions.
"""

import re
from typing import Optional


class MatchResult:
    """Holds the result of a successful route match."""

    def __init__(self, definition: dict, params: dict):
        self.definition = definition
        self.params = params

    def __repr__(self):
        return f"MatchResult(path={self.definition.get('path')!r}, params={self.params!r})"


def _compile_pattern(path: str) -> re.Pattern:
    """Convert a route path with {param} placeholders into a regex pattern."""
    escaped = re.escape(path)
    # Replace escaped \{param\} with a named capture group
    pattern = re.sub(r"\\\{(\w+)\\\}", r"(?P<\1>[^/]+)", escaped)
    return re.compile(f"^{pattern}$")


def match_route(
    definitions: list,
    method: str,
    path: str,
) -> Optional[MatchResult]:
    """Find the first definition that matches the given method and path.

    Exact matches are preferred over parameterised matches.
    Returns None if no definition matches.
    """
    method = method.upper()
    parameterised_candidates = []

    for defn in definitions:
        if defn.get("method", "").upper() != method:
            continue

        route_path = defn.get("path", "")

        # Exact match — return immediately
        if route_path == path:
            return MatchResult(defn, {})

        # Parameterised match — collect for later
        if "{" in route_path:
            pattern = _compile_pattern(route_path)
            m = pattern.match(path)
            if m:
                parameterised_candidates.append((defn, m.groupdict()))

    if parameterised_candidates:
        defn, params = parameterised_candidates[0]
        return MatchResult(defn, params)

    return None
