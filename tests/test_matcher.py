"""Tests for patchwork.matcher."""

import pytest
from patchwork.matcher import match_route, MatchResult, _compile_pattern


DEFINITIONS = [
    {"method": "GET",  "path": "/users",          "status": 200, "body": []},
    {"method": "GET",  "path": "/users/{id}",      "status": 200, "body": {}},
    {"method": "POST", "path": "/users",          "status": 201, "body": {}},
    {"method": "GET",  "path": "/items/{id}/tags", "status": 200, "body": []},
]


# --- _compile_pattern ---

def test_compile_pattern_exact_path():
    p = _compile_pattern("/health")
    assert p.match("/health")
    assert not p.match("/health/extra")


def test_compile_pattern_single_param():
    p = _compile_pattern("/users/{id}")
    m = p.match("/users/42")
    assert m is not None
    assert m.group("id") == "42"


def test_compile_pattern_does_not_match_slash_in_param():
    p = _compile_pattern("/users/{id}")
    assert p.match("/users/42/extra") is None


def test_compile_pattern_multi_segment():
    p = _compile_pattern("/items/{id}/tags")
    m = p.match("/items/99/tags")
    assert m and m.group("id") == "99"


# --- match_route ---

def test_match_exact_route_returns_result():
    result = match_route(DEFINITIONS, "GET", "/users")
    assert isinstance(result, MatchResult)
    assert result.definition["path"] == "/users"
    assert result.params == {}


def test_match_parameterised_route_extracts_param():
    result = match_route(DEFINITIONS, "GET", "/users/7")
    assert result is not None
    assert result.definition["path"] == "/users/{id}"
    assert result.params == {"id": "7"}


def test_exact_match_preferred_over_parameterised():
    # /users is exact; should not fall through to /users/{id}
    result = match_route(DEFINITIONS, "GET", "/users")
    assert result.definition["path"] == "/users"


def test_match_method_is_case_insensitive():
    result = match_route(DEFINITIONS, "get", "/users")
    assert result is not None


def test_match_wrong_method_returns_none():
    result = match_route(DEFINITIONS, "DELETE", "/users")
    assert result is None


def test_match_unknown_path_returns_none():
    result = match_route(DEFINITIONS, "GET", "/nonexistent")
    assert result is None


def test_match_post_route():
    result = match_route(DEFINITIONS, "POST", "/users")
    assert result is not None
    assert result.definition["status"] == 201


def test_match_nested_parameterised_route():
    result = match_route(DEFINITIONS, "GET", "/items/5/tags")
    assert result is not None
    assert result.params == {"id": "5"}


def test_match_empty_definitions_returns_none():
    assert match_route([], "GET", "/users") is None
