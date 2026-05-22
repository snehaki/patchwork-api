"""Tests for patchwork.scenario."""

import pytest

import patchwork.scenario as scenario
from patchwork.scenario import (
    ScenarioError,
    advance_scenario,
    get_current_response,
    parse_scenario_block,
    register_scenario,
    reset_all,
    reset_scenario,
    set_state,
)


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure a clean scenario registry for every test."""
    reset_all()
    yield
    reset_all()


_STATES = {
    "empty": {"status": 200, "body": {"items": []}},
    "one_item": {"status": 200, "body": {"items": [1]}},
    "two_items": {"status": 200, "body": {"items": [1, 2]}},
}


def test_register_and_get_initial_state():
    register_scenario("cart", _STATES, "empty")
    resp = get_current_response("cart")
    assert resp["body"] == {"items": []}


def test_advance_moves_to_next_state():
    register_scenario("cart", _STATES, "empty")
    new_state = advance_scenario("cart")
    assert new_state == "one_item"
    assert get_current_response("cart")["body"] == {"items": [1]}


def test_advance_wraps_around():
    register_scenario("cart", _STATES, "two_items")
    new_state = advance_scenario("cart")
    assert new_state == "empty"


def test_set_state_changes_response():
    register_scenario("cart", _STATES, "empty")
    set_state("cart", "two_items")
    assert get_current_response("cart")["body"] == {"items": [1, 2]}


def test_set_state_unknown_state_raises():
    register_scenario("cart", _STATES, "empty")
    with pytest.raises(ScenarioError, match="State 'missing'"):
        set_state("cart", "missing")


def test_reset_scenario_goes_back_to_first_key():
    register_scenario("cart", _STATES, "empty")
    advance_scenario("cart")
    advance_scenario("cart")
    reset_scenario("cart")
    assert get_current_response("cart")["body"] == {"items": []}


def test_get_current_response_unknown_scenario_returns_none():
    assert get_current_response("nonexistent") is None


def test_advance_unknown_scenario_raises():
    with pytest.raises(ScenarioError, match="Unknown scenario"):
        advance_scenario("ghost")


def test_register_empty_states_raises():
    with pytest.raises(ScenarioError, match="at least one state"):
        register_scenario("bad", {}, "start")


def test_register_missing_initial_raises():
    with pytest.raises(ScenarioError, match="Initial state"):
        register_scenario("bad", {"a": {}}, "z")


def test_parse_scenario_block_registers_scenario():
    defn = {
        "scenario": {
            "name": "login",
            "initial": "logged_out",
            "states": {
                "logged_out": {"status": 401},
                "logged_in": {"status": 200},
            },
        }
    }
    name = parse_scenario_block(defn)
    assert name == "login"
    assert get_current_response("login")["status"] == 401


def test_parse_scenario_block_no_block_returns_none():
    assert parse_scenario_block({"method": "GET", "path": "/x"}) is None


def test_parse_scenario_block_missing_name_raises():
    defn = {"scenario": {"states": {"a": {}}, "initial": "a"}}
    with pytest.raises(ScenarioError, match="'name' field"):
        parse_scenario_block(defn)
