"""Route registry: stores validated definitions and resolves incoming requests."""

import logging
from typing import Optional

from patchwork.loader import load_definitions_dir
from patchwork.validator import validate_definitions
from patchwork.matcher import match_route, MatchResult

logger = logging.getLogger(__name__)


class RouteConflictError(Exception):
    """Raised when two definitions share the same method + path pattern."""


class Registry:
    """Holds all active route definitions and resolves requests against them."""

    def __init__(self) -> None:
        self.routes: list[dict] = []
        self.directory: Optional[str] = None

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(self, definition: dict) -> None:
        """Add a single validated definition, raising on duplicate routes."""
        method = definition["method"]
        path = definition["path"]
        for existing in self.routes:
            if existing["method"] == method and existing["path"] == path:
                raise RouteConflictError(
                    f"Duplicate route: {method} {path}"
                )
        self.routes.append(definition)
        logger.debug("Registered route: %s %s", method, path)

    def load_definitions(self, directory: str) -> None:
        """Load, validate, and register all definitions from *directory*."""
        self.directory = directory
        raw = load_definitions_dir(directory)
        validated = validate_definitions(raw)
        for defn in validated:
            self.register(defn)
        logger.info(
            "Loaded %d definition(s) from %s", len(validated), directory
        )

    def clear(self) -> None:
        """Remove all registered routes (directory pointer is preserved)."""
        self.routes.clear()
        logger.debug("Registry cleared.")

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, method: str, path: str) -> Optional[tuple[dict, MatchResult]]:
        """Return the first matching (definition, match_result) pair or None."""
        for defn in self.routes:
            if defn["method"] != method.upper():
                continue
            result = match_route(defn["path"], path)
            if result.matched:
                return defn, result
        return None

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self.routes)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Registry(routes={len(self.routes)})"
