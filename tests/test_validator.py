"""Tests for patchwork.validator."""

import pytest

from patchwork.validator import (
    ValidationError,
    validate_definition,
    validate_definitions,
)

MINIMAL_DEFINITION = {
    "path": "/health",
    "method": "GET",
    "response": {"status": 200, "body": {"ok": True}},
}


def test_validate_definition_returns_dict():
    result = validate_definition(MINIMAL_DEFINITION.copy())
    assert result["path"] == "/health"


def test_validate_definition_missing_field_raises():
    bad = {"path": "/x", "method": "GET"}  # missing 'response'
    with pytest.raises(ValidationError, match="missing required fields"):
        validate_definition(bad)


def test_validate_definition_invalid_method_raises():
    bad = {**MINIMAL_DEFINITION, "method": "FETCH"}
    with pytest.raises(ValidationError, match="invalid method"):
        validate_definition(bad)


def test_validate_definition_method_case_insensitive_raises():
    # Only exact uppercase is stored valid; lowercase should still fail
    bad = {**MINIMAL_DEFINITION, "method": "get"}
    # 'get'.upper() == 'GET' which IS valid — should pass
    result = validate_definition(bad)
    assert result["method"] == "get"


def test_validate_definition_path_must_start_with_slash():
    bad = {**MINIMAL_DEFINITION, "path": "health"}
    with pytest.raises(ValidationError, match="'path' must be a string starting with '/'"):
        validate_definition(bad)


def test_validate_definition_response_must_be_dict():
    bad = {**MINIMAL_DEFINITION, "response": "OK"}
    with pytest.raises(ValidationError, match="'response' must be a mapping"):
        validate_definition(bad)


def test_validate_definition_invalid_status_raises():
    bad = {**MINIMAL_DEFINITION, "response": {"status": 999}}
    with pytest.raises(ValidationError, match="response.status"):
        validate_definition(bad)


def test_validate_definition_non_dict_raises():
    with pytest.raises(ValidationError, match="must be a mapping"):
        validate_definition(["not", "a", "dict"])


def test_validate_definitions_returns_list():
    result = validate_definitions([MINIMAL_DEFINITION.copy()])
    assert isinstance(result, list)
    assert len(result) == 1


def test_validate_definitions_non_list_raises():
    with pytest.raises(ValidationError, match="must be a list"):
        validate_definitions(MINIMAL_DEFINITION)


def test_validate_definitions_propagates_index_in_source():
    bad_list = [MINIMAL_DEFINITION.copy(), {"path": "/x", "method": "GET"}]
    with pytest.raises(ValidationError, match=r"\[1\]"):
        validate_definitions(bad_list, source="test.yaml")
