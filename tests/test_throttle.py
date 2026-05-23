"""Tests for patchwork.throttle."""

import pytest

from patchwork.throttle import (
    ThrottleError,
    check_throttle,
    parse_throttle,
    reset_throttle,
)


@pytest.fixture(autouse=True)
def clean_state():
    reset_throttle()
    yield
    reset_throttle()


# ---------------------------------------------------------------------------
# parse_throttle
# ---------------------------------------------------------------------------

def test_parse_throttle_none_when_absent():
    assert parse_throttle({}) is None


def test_parse_throttle_returns_config():
    cfg = parse_throttle({"throttle": {"rate": 10, "burst": 5}})
    assert cfg == {"rate": 10.0, "burst": 5}


def test_parse_throttle_default_burst_is_one():
    cfg = parse_throttle({"throttle": {"rate": 2}})
    assert cfg["burst"] == 1


def test_parse_throttle_not_a_mapping_raises():
    with pytest.raises(ThrottleError, match="mapping"):
        parse_throttle({"throttle": "fast"})


def test_parse_throttle_missing_rate_raises():
    with pytest.raises(ThrottleError, match="rate is required"):
        parse_throttle({"throttle": {}})


def test_parse_throttle_rate_not_a_number_raises():
    with pytest.raises(ThrottleError, match="must be a number"):
        parse_throttle({"throttle": {"rate": "fast"}})


def test_parse_throttle_rate_zero_raises():
    with pytest.raises(ThrottleError, match="greater than zero"):
        parse_throttle({"throttle": {"rate": 0}})


def test_parse_throttle_rate_negative_raises():
    with pytest.raises(ThrottleError, match="greater than zero"):
        parse_throttle({"throttle": {"rate": -1}})


def test_parse_throttle_burst_not_int_raises():
    with pytest.raises(ThrottleError, match="burst"):
        parse_throttle({"throttle": {"rate": 5, "burst": 1.5}})


def test_parse_throttle_burst_zero_raises():
    with pytest.raises(ThrottleError, match="burst"):
        parse_throttle({"throttle": {"rate": 5, "burst": 0}})


# ---------------------------------------------------------------------------
# check_throttle
# ---------------------------------------------------------------------------

def test_check_throttle_allows_first_request():
    cfg = {"rate": 10.0, "burst": 1}
    allowed, retry_after = check_throttle(cfg, "127.0.0.1", "GET:/hello")
    assert allowed is True
    assert retry_after == 0.0


def test_check_throttle_blocks_when_burst_exhausted():
    cfg = {"rate": 1.0, "burst": 1}
    check_throttle(cfg, "127.0.0.1", "GET:/hello")  # consume the single token
    allowed, retry_after = check_throttle(cfg, "127.0.0.1", "GET:/hello")
    assert allowed is False
    assert retry_after > 0.0


def test_check_throttle_tracks_clients_independently():
    cfg = {"rate": 1.0, "burst": 1}
    allowed_a, _ = check_throttle(cfg, "10.0.0.1", "GET:/hello")
    allowed_b, _ = check_throttle(cfg, "10.0.0.2", "GET:/hello")
    assert allowed_a is True
    assert allowed_b is True


def test_check_throttle_tracks_routes_independently():
    cfg = {"rate": 1.0, "burst": 1}
    allowed_r1, _ = check_throttle(cfg, "127.0.0.1", "GET:/foo")
    allowed_r2, _ = check_throttle(cfg, "127.0.0.1", "GET:/bar")
    assert allowed_r1 is True
    assert allowed_r2 is True


def test_reset_throttle_clears_state():
    cfg = {"rate": 1.0, "burst": 1}
    check_throttle(cfg, "127.0.0.1", "GET:/hello")
    reset_throttle()
    allowed, _ = check_throttle(cfg, "127.0.0.1", "GET:/hello")
    assert allowed is True
