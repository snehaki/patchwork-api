"""Tests for patchwork.circuit_breaker."""

import time
import pytest

from patchwork.circuit_breaker import (
    CircuitBreakerError,
    record_success,
    record_failure,
    is_allowed,
    get_state,
    reset,
    reset_all,
)


@pytest.fixture(autouse=True)
def clean():
    reset_all()
    yield
    reset_all()


def test_new_circuit_is_closed():
    assert get_state("svc") == "closed"


def test_is_allowed_when_closed():
    assert is_allowed("svc") is True


def test_failures_below_threshold_stay_closed():
    record_failure("svc", threshold=3)
    record_failure("svc", threshold=3)
    assert get_state("svc") == "closed"


def test_failures_at_threshold_open_circuit():
    for _ in range(3):
        record_failure("svc", threshold=3)
    assert get_state("svc") == "open"


def test_open_circuit_blocks_requests():
    for _ in range(3):
        record_failure("svc", threshold=3)
    assert is_allowed("svc", timeout=60.0) is False


def test_open_circuit_transitions_to_half_open_after_timeout(monkeypatch):
    for _ in range(3):
        record_failure("svc", threshold=3)
    # Simulate time passing beyond the timeout
    monkeypatch.setattr(time, "monotonic", lambda: time.monotonic.__wrapped__() + 60)
    # Use a direct approach: patch monotonic via the module
    import patchwork.circuit_breaker as cb
    original = cb.time.monotonic
    cb.time.monotonic = lambda: original() + 60
    try:
        assert is_allowed("svc", timeout=30.0) is True
        assert get_state("svc") == "half-open"
    finally:
        cb.time.monotonic = original


def test_success_resets_open_circuit():
    for _ in range(3):
        record_failure("svc", threshold=3)
    record_success("svc")
    assert get_state("svc") == "closed"
    assert is_allowed("svc") is True


def test_success_resets_failure_count():
    record_failure("svc", threshold=5)
    record_failure("svc", threshold=5)
    record_success("svc")
    # After success, two more failures should not open the circuit
    record_failure("svc", threshold=5)
    record_failure("svc", threshold=5)
    assert get_state("svc") == "closed"


def test_circuits_are_independent():
    for _ in range(3):
        record_failure("svc-a", threshold=3)
    assert get_state("svc-a") == "open"
    assert get_state("svc-b") == "closed"


def test_reset_clears_single_circuit():
    for _ in range(3):
        record_failure("svc", threshold=3)
    reset("svc")
    assert get_state("svc") == "closed"


def test_reset_unknown_key_is_noop():
    reset("nonexistent")  # should not raise


def test_reset_all_clears_everything():
    for _ in range(3):
        record_failure("svc-a", threshold=3)
        record_failure("svc-b", threshold=3)
    reset_all()
    assert get_state("svc-a") == "closed"
    assert get_state("svc-b") == "closed"
