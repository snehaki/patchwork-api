"""In-memory registry that stores and looks up validated route definitions."""

from __future__ import annotations

from typing import Iterator

from patchwork.validator import validate_definitions, ValidationError  # noqa: F401


class RouteConflictError(Exception):
    """Raised when two definitions share the same method + path combination."""


class Registry:
    """Holds all loaded route definitions and provides lookup helpers."""

    def __init__(self) -> None:
        # Keyed by (METHOD, path) tuples for O(1) lookup
        self._routes: dict[tuple[str, str], dict] = {}

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, definition: dict, *, allow_override: bool = False) -> None:
        """Add a single validated definition to the registry.

        Args:
            definition: A validated route definition dict.
            allow_override: When True, silently replace conflicting entries.

        Raises:
            RouteConflictError: If the route already exists and allow_override is False.
        """
        key = (definition["method"].upper(), definition["path"])
        if key in self._routes and not allow_override:
            raise RouteConflictError(
                f"Route {key[0]} {key[1]} is already registered."
            )
        self._routes[key] = definition

    def load_definitions(
        self, definitions: list, source: str = "<unknown>", *, allow_override: bool = False
    ) -> int:
        """Validate and register a list of definitions.

        Returns:
            Number of routes successfully registered.
        """
        validated = validate_definitions(definitions, source=source)
        for defn in validated:
            self.register(defn, allow_override=allow_override)
        return len(validated)

    def clear(self) -> None:
        """Remove all registered routes."""
        self._routes.clear()

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def lookup(self, method: str, path: str) -> dict | None:
        """Return the matching definition or None."""
        return self._routes.get((method.upper(), path))

    def __len__(self) -> int:
        return len(self._routes)

    def __iter__(self) -> Iterator[dict]:
        return iter(self._routes.values())
