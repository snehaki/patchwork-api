"""Tests for patchwork.metrics_routes."""

import json
import pytest
from patchwork.metrics import reset, record
from patchwork.metrics_routes import handle_metrics_request


@pytest.fixture(autouse=True)
def clean():
    reset()
    yield
    reset()


def _call(method="GET", path="/_patchwork/metrics"):
    return handle_metrics_request(method, path)


def test_non_management_path_returns_none():
    assert handle_metrics_request("GET", "/api/users") is None


def test_non_management_prefix_returns_none():
    assert handle_metrics_request("GET", "/metrics") is None


def test_get_returns_200():
    resp = _call("GET")
    assert resp["status"] == 200


def test_get_returns_json_content_type():
    resp = _call("GET")
    assert resp["headers"]["Content-Type"] == "application/json"


def test_get_empty_snapshot():
    resp = _call("GET")
    data = json.loads(resp["body"])
    assert data == {}


def test_get_populated_snapshot():
    record("GET", "/users", 200, 0.05)
    resp = _call("GET")
    data = json.loads(resp["body"])
    assert "GET /users" in data
    assert data["GET /users"]["count"] == 1


def test_delete_resets_metrics():
    record("POST", "/items", 201, 0.1)
    resp = _call("DELETE")
    assert resp["status"] == 200
    body = json.loads(resp["body"])
    assert body["reset"] is True
    # snapshot should now be empty
    resp2 = _call("GET")
    assert json.loads(resp2["body"]) == {}


def test_post_method_returns_405():
    resp = _call("POST")
    assert resp["status"] == 405


def test_trailing_slash_still_works():
    resp = handle_metrics_request("GET", "/_patchwork/metrics/")
    assert resp["status"] == 200


def test_unknown_sub_path_returns_404():
    resp = handle_metrics_request("GET", "/_patchwork/metrics/unknown")
    assert resp["status"] == 404
