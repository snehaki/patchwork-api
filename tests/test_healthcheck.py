"""Tests for patchwork.healthcheck."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from patchwork.healthcheck import (
    MANAGEMENT_PREFIX,
    handle_health_request,
    uptime_seconds,
)


# ---------------------------------------------------------------------------
# uptime_seconds
# ---------------------------------------------------------------------------

def test_uptime_seconds_is_non_negative():
    assert uptime_seconds() >= 0.0


def test_uptime_seconds_is_float():
    assert isinstance(uptime_seconds(), float)


# ---------------------------------------------------------------------------
# handle_health_request — path matching
# ---------------------------------------------------------------------------

def test_non_management_path_returns_none():
    result = handle_health_request("GET", "/api/users")
    assert result is None


def test_non_management_prefix_returns_none():
    result = handle_health_request("GET", "/__patchwork/other")
    assert result is None


def test_exact_management_path_returns_response():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    assert result is not None


def test_trailing_slash_is_accepted():
    result = handle_health_request("GET", MANAGEMENT_PREFIX + "/")
    assert result is not None


# ---------------------------------------------------------------------------
# handle_health_request — method guard
# ---------------------------------------------------------------------------

def test_post_returns_405():
    result = handle_health_request("POST", MANAGEMENT_PREFIX)
    assert result["status"] == 405


def test_delete_returns_405():
    result = handle_health_request("DELETE", MANAGEMENT_PREFIX)
    assert result["status"] == 405


# ---------------------------------------------------------------------------
# handle_health_request — response shape
# ---------------------------------------------------------------------------

def test_get_returns_200():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    assert result["status"] == 200


def test_response_content_type_is_json():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    assert result["headers"]["Content-Type"] == "application/json"


def test_response_body_has_status_ok():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    body = json.loads(result["body"])
    assert body["status"] == "ok"


def test_response_body_has_uptime():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    body = json.loads(result["body"])
    assert "uptime_seconds" in body
    assert body["uptime_seconds"] >= 0.0


def test_response_body_has_route_count_zero_without_registry():
    result = handle_health_request("GET", MANAGEMENT_PREFIX)
    body = json.loads(result["body"])
    assert body["route_count"] == 0


def test_response_body_route_count_uses_registry():
    mock_registry = MagicMock()
    mock_registry.routes.return_value = ["route1", "route2", "route3"]
    result = handle_health_request("GET", MANAGEMENT_PREFIX, registry=mock_registry)
    body = json.loads(result["body"])
    assert body["route_count"] == 3
