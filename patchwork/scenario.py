"""Scenario (stateful session) support for patchwork-api.

Allows a definition to declare a ``scenario`` block so that successive
calls to the same route can return different responses depending on which
"state" is currently active for a given client key.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class ScenarioError(Exception):
    """Raised when a scenario definition or transition is invalid."""


# scenario_name -> {state_name -> response_dict}
_registry: Dict[str, Dict[str, Any]] = {}
# scenario_name -> current state name
_state: Dict[str, str] = {}


def register_scenario(name: str, states: Dict[str, Any], initial: str) -> None:
    """Register a named scenario with its states and initial state."""
    if not states:
        raise ScenarioError(f"Scenario '{name}' must define at least one state.")
    if initial not in states:
        raise ScenarioError(
            f"Initial state '{initial}' not found in scenario '{name}'."
        )
    _registry[name] = states
    _state[name] = initial


def get_current_response(name: str) -> Optional[Dict[str, Any]]:
    """Return the response dict for the current state of *name*."""
    if name not in _registry:
        return None
    current = _state[name]
    return _registry[name].get(current)


def advance_scenario(name: str) -> str:
    """Advance *name* to the next state (wraps around). Returns new state."""
    if name not in _registry:
        raise ScenarioError(f"Unknown scenario '{name}'.")
    states: List[str] = list(_registry[name].keys())
    idx = states.index(_state[name])
    _state[name] = states[(idx + 1) % len(states)]
    return _state[name]


def set_state(name: str, state: str) -> None:
    """Explicitly set the active state for *name*."""
    if name not in _registry:
        raise ScenarioError(f"Unknown scenario '{name}'.")
    if state not in _registry[name]:
        raise ScenarioError(
            f"State '{state}' not found in scenario '{name}'."
        )
    _state[name] = state


def reset_scenario(name: str) -> None:
    """Reset *name* to its initial state (first key)."""
    if name not in _registry:
        raise ScenarioError(f"Unknown scenario '{name}'.")
    _state[name] = next(iter(_registry[name]))


def reset_all() -> None:
    """Clear every registered scenario (useful between tests)."""
    _registry.clear()
    _state.clear()


def parse_scenario_block(definition: Dict[str, Any]) -> Optional[str]:
    """Extract and register the scenario block from a route *definition*.

    Returns the scenario name if one was found, otherwise ``None``.
    """
    block = definition.get("scenario")
    if block is None:
        return None
    name: str = block.get("name", "")
    if not name:
        raise ScenarioError("Scenario block must include a 'name' field.")
    states: Dict[str, Any] = block.get("states", {})
    initial: str = block.get("initial", next(iter(states), ""))
    register_scenario(name, states, initial)
    return name
