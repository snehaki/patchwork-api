"""Tests for patchwork.scenario_routes management endpoints."""

import json
import pytest

from patchwork.scenario import reset_all, register_scenario
from patchwork.scenario_routes import handle_scenario_request

_STATES = {
    "idle": {"status": 200, "body": {}},
    "busy": {"status": 503, "body": {"error": "busy"}},
}


@pytest.fixture(autouse=True)
def clean():
    reset_all()
    register_scenario("svc", _STATES, "idle")
    yield
    reset_all()


def _call(method, path, body=b""):
    result = handle_scenario_request(method, path, body)
    assert result is not None
    status, headers, raw = result
    return status, headers, json.loads(raw)


def test_non_management_path_returns_none():
    assert handle_scenario_request("GET", "/api/users", b"") is None


def test_list_all_scenarios():
    status, _, body = _call("GET", "/_patchwork/scenario/")
    assert status == 200
    assert "svc" in body["scenarios"]
    assert body["scenarios"]["svc"] == "idle"


def test_get_scenario_state():
    status, _, body = _call("GET", "/_patchwork/scenario/svc")
    assert status == 200
    assert body == {"scenario": "svc", "state": "idle"}


def test_advance_scenario():
    status, _, body = _call("POST", "/_patchwork/scenario/svc/advance")
    assert status == 200
    assert body["state"] == "busy"


def test_advance_wraps():
    _call("POST", "/_patchwork/scenario/svc/advance")  # idle -> busy
    status, _, body = _call("POST", "/_patchwork/scenario/svc/advance")  # busy -> idle
    assert body["state"] == "idle"


def test_reset_scenario():
    _call("POST", "/_patchwork/scenario/svc/advance")
    status, _, body = _call("POST", "/_patchwork/scenario/svc/reset")
    assert status == 200
    assert body["state"] == "idle"


def test_set_state_explicit():
    payload = json.dumps({"state": "busy"}).encode()
    status, _, body = _call("POST", "/_patchwork/scenario/svc/state", payload)
    assert status == 200
    assert body["state"] == "busy"


def test_set_state_missing_field_returns_400():
    payload = json.dumps({}).encode()
    status, _, body = _call("POST", "/_patchwork/scenario/svc/state", payload)
    assert status == 400
    assert "state" in body["error"]


def test_set_state_invalid_json_returns_400():
    status, _, body = _call("POST", "/_patchwork/scenario/svc/state", b"not-json")
    assert status == 400


def test_unknown_scenario_returns_404():
    status, _, body = _call("GET", "/_patchwork/scenario/ghost")
    assert status == 404
    assert "ghost" in body["error"]


def test_set_state_unknown_state_returns_400():
    payload = json.dumps({"state": "nonexistent"}).encode()
    status, _, body = _call("POST", "/_patchwork/scenario/svc/state", payload)
    assert status == 400


def test_unknown_action_returns_404():
    status, _, body = _call("POST", "/_patchwork/scenario/svc/unknown_action")
    assert status == 404
