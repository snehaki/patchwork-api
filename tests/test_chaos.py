"""Tests for patchwork.chaos."""

import random
import pytest

from patchwork.chaos import ChaosError, parse_chaos, apply_chaos


# ---------------------------------------------------------------------------
# parse_chaos
# ---------------------------------------------------------------------------

def test_parse_chaos_none_when_absent():
    assert parse_chaos({}) is None


def test_parse_chaos_not_a_mapping_raises():
    with pytest.raises(ChaosError, match="mapping"):
        parse_chaos({"chaos": "bad"})


def test_parse_chaos_invalid_probability_type_raises():
    with pytest.raises(ChaosError, match="number"):
        parse_chaos({"chaos": {"probability": "high"}})


def test_parse_chaos_probability_out_of_range_raises():
    with pytest.raises(ChaosError, match="between"):
        parse_chaos({"chaos": {"probability": 1.5}})


def test_parse_chaos_invalid_fault_raises():
    with pytest.raises(ChaosError, match="fault"):
        parse_chaos({"chaos": {"fault": "explode"}})


def test_parse_chaos_default_error_fault():
    result = parse_chaos({"chaos": {"probability": 0.5}})
    assert result == {"probability": 0.5, "fault": "error", "status": 500, "body": "chaos fault injected"}


def test_parse_chaos_custom_error_fault():
    result = parse_chaos({"chaos": {"fault": "error", "status": 503, "body": "gone"}})
    assert result["status"] == 503
    assert result["body"] == "gone"


def test_parse_chaos_delay_fault():
    result = parse_chaos({"chaos": {"fault": "delay", "seconds": 2.5}})
    assert result == {"probability": 1.0, "fault": "delay", "seconds": 2.5}


def test_parse_chaos_delay_negative_seconds_raises():
    with pytest.raises(ChaosError, match="non-negative"):
        parse_chaos({"chaos": {"fault": "delay", "seconds": -1}})


def test_parse_chaos_empty_fault():
    result = parse_chaos({"chaos": {"fault": "empty"}})
    assert result == {"probability": 1.0, "fault": "empty"}


# ---------------------------------------------------------------------------
# apply_chaos
# ---------------------------------------------------------------------------

def test_apply_chaos_none_config_returns_none():
    assert apply_chaos(None) is None


def test_apply_chaos_probability_zero_never_fires():
    cfg = parse_chaos({"chaos": {"probability": 0.0}})
    for _ in range(20):
        assert apply_chaos(cfg) is None


def test_apply_chaos_probability_one_always_fires():
    cfg = parse_chaos({"chaos": {"probability": 1.0, "fault": "empty"}})
    assert apply_chaos(cfg) == {"fault": "empty"}


def test_apply_chaos_error_action():
    cfg = {"probability": 1.0, "fault": "error", "status": 503, "body": "oops"}
    result = apply_chaos(cfg)
    assert result == {"fault": "error", "status": 503, "body": "oops"}


def test_apply_chaos_delay_action():
    cfg = {"probability": 1.0, "fault": "delay", "seconds": 1.5}
    result = apply_chaos(cfg)
    assert result == {"fault": "delay", "seconds": 1.5}


def test_apply_chaos_uses_provided_rng():
    """A seeded RNG that always returns 0.9 should not fire at probability 0.5."""
    class HighRNG:
        def random(self):
            return 0.9

    cfg = {"probability": 0.5, "fault": "empty"}
    assert apply_chaos(cfg, rng=HighRNG()) is None


def test_apply_chaos_rng_that_fires():
    class LowRNG:
        def random(self):
            return 0.1

    cfg = {"probability": 0.5, "fault": "empty"}
    assert apply_chaos(cfg, rng=LowRNG()) == {"fault": "empty"}
