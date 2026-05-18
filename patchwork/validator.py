"""Validates route definition dictionaries loaded from YAML files."""

from typing import Any

REQUIRED_FIELDS = {"path", "method", "response"}
VALID_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
VALID_STATUS_CODES = range(100, 600)


class ValidationError(Exception):
    """Raised when a route definition fails validation."""


def validate_definition(definition: Any, source: str = "<unknown>") -> dict:
    """Validate a single route definition dict.

    Args:
        definition: The parsed object to validate.
        source: A label used in error messages (e.g. the file path).

    Returns:
        The validated definition dict.

    Raises:
        ValidationError: If the definition is invalid.
    """
    if not isinstance(definition, dict):
        raise ValidationError(
            f"{source}: definition must be a mapping, got {type(definition).__name__}"
        )

    missing = REQUIRED_FIELDS - definition.keys()
    if missing:
        raise ValidationError(
            f"{source}: definition missing required fields: {sorted(missing)}"
        )

    method = definition["method"]
    if not isinstance(method, str) or method.upper() not in VALID_METHODS:
        raise ValidationError(
            f"{source}: invalid method {method!r}. Must be one of {sorted(VALID_METHODS)}"
        )

    path = definition["path"]
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValidationError(
            f"{source}: 'path' must be a string starting with '/'"
        )

    response = definition["response"]
    if not isinstance(response, dict):
        raise ValidationError(
            f"{source}: 'response' must be a mapping"
        )

    status = response.get("status", 200)
    if not isinstance(status, int) or status not in VALID_STATUS_CODES:
        raise ValidationError(
            f"{source}: 'response.status' must be an integer between 100 and 599"
        )

    return definition


def validate_definitions(definitions: list, source: str = "<unknown>") -> list:
    """Validate a list of route definitions.

    Raises:
        ValidationError: If any definition is invalid.
    """
    if not isinstance(definitions, list):
        raise ValidationError(
            f"{source}: top-level value must be a list of definitions"
        )
    return [validate_definition(d, source=f"{source}[{i}]") for i, d in enumerate(definitions)]
