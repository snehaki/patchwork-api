"""Tests for patchwork.transform_routes."""

from unittest.mock import MagicMock

from patchwork.transform_routes import handle_transform_request


def _registry(*definitions):
    reg = MagicMock()
    reg.all.return_value = list(definitions)
    return reg


def _call(method="GET", path="/__patchwork__/transforms", registry=None):
    if registry is None:
        registry = _registry()
    return handle_transform_request(method, path, registry)


# ---------------------------------------------------------------------------
# Routing guard
# ---------------------------------------------------------------------------

def test_non_management_path_returns_none():
    assert _call(path="/api/users") is None


def test_non_management_prefix_returns_none():
    assert _call(path="/transforms") is None


# ---------------------------------------------------------------------------
# Method guard
# ---------------------------------------------------------------------------

def test_non_get_method_returns_405():
    resp = _call(method="POST")
    assert resp["status"] == 405


# ---------------------------------------------------------------------------
# List endpoint
# ---------------------------------------------------------------------------

def test_list_returns_200():
    resp = _call()
    assert resp["status"] == 200


def test_list_content_type_json():
    resp = _call()
    assert resp["headers"]["Content-Type"] == "application/json"


def test_list_empty_when_no_transforms():
    import json
    reg = _registry(
        {"method": "GET", "path": "/ping", "status": 200},
    )
    resp = _call(registry=reg)
    assert json.loads(resp["body"]) == []


def test_list_includes_routes_with_transforms():
    import json
    transforms = [{"type": "wrap"}]
    reg = _registry(
        {"method": "GET", "path": "/users", "transforms": transforms},
        {"method": "POST", "path": "/items", "transforms": []},
    )
    resp = _call(registry=reg)
    data = json.loads(resp["body"])
    assert len(data) == 1
    assert data[0]["path"] == "/users"
    assert data[0]["transforms"] == transforms


def test_list_skips_routes_without_transforms_key():
    import json
    reg = _registry(
        {"method": "GET", "path": "/health"},
    )
    resp = _call(registry=reg)
    assert json.loads(resp["body"]) == []


def test_list_trailing_slash_also_works():
    resp = _call(path="/__patchwork__/transforms/")
    assert resp["status"] == 200


# ---------------------------------------------------------------------------
# Unknown sub-path
# ---------------------------------------------------------------------------

def test_unknown_subpath_returns_404():
    resp = _call(path="/__patchwork__/transforms/unknown")
    assert resp["status"] == 404
