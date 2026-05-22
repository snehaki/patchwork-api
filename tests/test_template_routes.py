"""Tests for patchwork.template_routes."""

import json
import pytest
from patchwork.template_routes import handle_template_request


def _call(method="GET", path="/_patchwork/template"):
    return handle_template_request(method, path)


def test_non_management_path_returns_none():
    assert handle_template_request("GET", "/users/1") is None


def test_non_management_prefix_returns_none():
    assert handle_template_request("GET", "/template") is None


def test_list_variables_root():
    resp = _call("GET", "/_patchwork/template")
    assert resp is not None
    assert resp["status"] == 200
    body = json.loads(resp["body"])
    assert "variables" in body
    assert isinstance(body["variables"], list)
    assert len(body["variables"]) > 0


def test_list_variables_explicit_path():
    resp = _call("GET", "/_patchwork/template/variables")
    assert resp["status"] == 200
    body = json.loads(resp["body"])
    assert "variables" in body


def test_list_variables_trailing_slash():
    resp = _call("GET", "/_patchwork/template/")
    assert resp["status"] == 200


def test_variables_contain_required_fields():
    resp = _call()
    body = json.loads(resp["body"])
    for var in body["variables"]:
        assert "placeholder" in var
        assert "description" in var


def test_variables_include_method_placeholder():
    resp = _call()
    body = json.loads(resp["body"])
    placeholders = [v["placeholder"] for v in body["variables"]]
    assert any("request.method" in p for p in placeholders)


def test_non_get_method_returns_405():
    resp = _call("POST", "/_patchwork/template")
    assert resp["status"] == 405
    body = json.loads(resp["body"])
    assert "error" in body


def test_unknown_sub_route_returns_404():
    resp = _call("GET", "/_patchwork/template/nonexistent")
    assert resp["status"] == 404
    body = json.loads(resp["body"])
    assert "error" in body


def test_content_type_is_json():
    resp = _call()
    assert resp["headers"]["Content-Type"] == "application/json"
