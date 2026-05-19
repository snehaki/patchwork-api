import json
import pytest
from patchwork.responder import build_response, _substitute_params


# ---------------------------------------------------------------------------
# _substitute_params
# ---------------------------------------------------------------------------

def test_substitute_params_plain_string():
    result = _substitute_params("hello {name}", {"name": "world"})
    assert result == "hello world"


def test_substitute_params_missing_key_left_unchanged():
    result = _substitute_params("{missing}", {})
    assert result == "{missing}"


def test_substitute_params_nested_dict():
    template = {"id": "{id}", "label": "item"}
    result = _substitute_params(template, {"id": "42"})
    assert result == {"id": "42", "label": "item"}


def test_substitute_params_list():
    template = ["{a}", "{b}"]
    result = _substitute_params(template, {"a": "x", "b": "y"})
    assert result == ["x", "y"]


def test_substitute_params_non_string_passthrough():
    assert _substitute_params(123, {}) == 123
    assert _substitute_params(None, {}) is None
    assert _substitute_params(True, {}) is True


# ---------------------------------------------------------------------------
# build_response
# ---------------------------------------------------------------------------

def test_build_response_default_status():
    defn = {"method": "GET", "path": "/ping", "body": "pong"}
    resp = build_response(defn, {})
    assert resp["status"] == 200


def test_build_response_custom_status():
    defn = {"method": "POST", "path": "/items", "status": 201, "body": "created"}
    resp = build_response(defn, {})
    assert resp["status"] == 201


def test_build_response_string_body_is_bytes():
    defn = {"method": "GET", "path": "/hi", "body": "hello"}
    resp = build_response(defn, {})
    assert isinstance(resp["body"], bytes)
    assert resp["body"] == b"hello"


def test_build_response_dict_body_is_json_bytes():
    defn = {"method": "GET", "path": "/data", "body": {"key": "value"}}
    resp = build_response(defn, {})
    parsed = json.loads(resp["body"])
    assert parsed == {"key": "value"}


def test_build_response_dict_body_sets_json_content_type():
    defn = {"method": "GET", "path": "/data", "body": {"k": "v"}}
    resp = build_response(defn, {})
    assert resp["headers"]["Content-Type"] == "application/json"


def test_build_response_string_body_sets_text_content_type():
    defn = {"method": "GET", "path": "/hi", "body": "hi"}
    resp = build_response(defn, {})
    assert resp["headers"]["Content-Type"] == "text/plain"


def test_build_response_custom_header_preserved():
    defn = {
        "method": "GET",
        "path": "/secure",
        "body": "",
        "headers": {"X-Token": "abc123"},
    }
    resp = build_response(defn, {})
    assert resp["headers"]["X-Token"] == "abc123"


def test_build_response_custom_content_type_not_overridden():
    defn = {
        "method": "GET",
        "path": "/xml",
        "body": "<root/>",
        "headers": {"Content-Type": "application/xml"},
    }
    resp = build_response(defn, {})
    assert resp["headers"]["Content-Type"] == "application/xml"


def test_build_response_substitutes_path_params():
    defn = {"method": "GET", "path": "/users/{id}", "body": {"id": "{id}"}}
    resp = build_response(defn, {"id": "7"})
    parsed = json.loads(resp["body"])
    assert parsed == {"id": "7"}


def test_build_response_empty_body():
    defn = {"method": "DELETE", "path": "/items/1", "status": 204, "body": ""}
    resp = build_response(defn, {})
    assert resp["body"] == b""
