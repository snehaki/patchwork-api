"""Query parameter filtering for matched routes."""

from __future__ import annotations

from typing import Any


class FilterError(Exception):
    """Raised when a filter definition is invalid."""


def _parse_query_string(query_string: str) -> dict[str, str]:
    """Parse a raw query string into a dict of key/value pairs."""
    if not query_string:
        return {}
    params: dict[str, str] = {}
    for part in query_string.split("&"):
        if "=" in part:
            key, _, value = part.partition("=")
            params[key.strip()] = value.strip()
        elif part.strip():
            params[part.strip()] = ""
    return params


def _match_query_filters(
    filters: dict[str, Any], query_params: dict[str, str]
) -> bool:
    """Return True if all filter key/value pairs are present in query_params.

    A filter value of None means the key must simply be present.
    A filter value of "*" matches any non-empty value.
    Otherwise the value must match exactly.
    """
    for key, expected in filters.items():
        if key not in query_params:
            return False
        actual = query_params[key]
        if expected is None:
            continue
        if expected == "*":
            if not actual:
                return False
            continue
        if str(expected) != actual:
            return False
    return True


def filter_candidates(
    candidates: list[dict[str, Any]], query_string: str
) -> dict[str, Any] | None:
    """Select the best matching candidate from a list based on query filters.

    Candidates are assumed to share the same route path and method.  Each may
    optionally carry a ``query`` dict of required query parameters.  The
    candidate with the most specific (longest) matching filter set wins.  A
    candidate without a ``query`` key acts as a catch-all fallback.

    Returns None when no candidate matches.
    """
    if not candidates:
        return None

    query_params = _parse_query_string(query_string)

    best: dict[str, Any] | None = None
    best_score: int = -1

    for candidate in candidates:
        filters = candidate.get("query")
        if filters is None:
            score = 0
        else:
            if not isinstance(filters, dict):
                raise FilterError(
                    "'query' filter must be a mapping, got "
                    f"{type(filters).__name__}"
                )
            if not _match_query_filters(filters, query_params):
                continue
            score = len(filters)

        if score > best_score:
            best_score = score
            best = candidate

    return best
