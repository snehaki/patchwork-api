"""Tests for patchwork.delay module."""

import time
import pytest

from patchwork.delay import DelayError, apply_delay, get_response_delay, parse_delay


# --- parse_delay ---

def test_parse_delay_none_returns_none():
    assert parse_delay(None) is None


def test_parse_delay_int_returns_float():
    result = parse_delay(2)
    assert result == 2.0
    assert isinstance(result, float)


def test_parse_delay_float_returns_float():
    result = parse_delay(0.5)
    assert result == 0.5


def test_parse_delay_zero_is_valid():
    assert parse_delay(0) == 0.0


def test_parse_delay_negative_raises():
    with pytest.raises(DelayError, match=">= 0"):
        parse_delay(-1)


def test_parse_delay_string_raises():
    with pytest.raises(DelayError, match="number"):
        parse_delay("0.5")


def test_parse_delay_list_raises():
    with pytest.raises(DelayError, match="number"):
        parse_delay([0.5])


# --- apply_delay ---

def test_apply_delay_none_does_not_sleep():
    start = time.monotonic()
    apply_delay(None)
    elapsed = time.monotonic() - start
    assert elapsed < 0.05


def test_apply_delay_zero_does_not_sleep():
    start = time.monotonic()
    apply_delay(0.0)
    elapsed = time.monotonic() - start
    assert elapsed < 0.05


def test_apply_delay_sleeps_approximately():
    start = time.monotonic()
    apply_delay(0.1)
    elapsed = time.monotonic() - start
    assert elapsed >= 0.09


# --- get_response_delay ---

def test_get_response_delay_missing_key_returns_none():
    assert get_response_delay({"status": 200}) is None


def test_get_response_delay_valid_value():
    result = get_response_delay({"status": 200, "delay": 1})
    assert result == 1.0


def test_get_response_delay_invalid_value_raises():
    with pytest.raises(DelayError):
        get_response_delay({"status": 200, "delay": "slow"})


def test_get_response_delay_negative_raises():
    with pytest.raises(DelayError, match=">= 0"):
        get_response_delay({"status": 200, "delay": -0.5})
