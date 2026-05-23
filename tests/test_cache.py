"""Tests for patchwork.cache."""

import time
import pytest

from patchwork.cache import (
    CacheError,
    parse_cache,
    make_key,
    get,
    put,
    invalidate,
    clear,
    size,
)


@pytest.fixture(autouse=True)
def reset_cache():
    clear()
    yield
    clear()


# --- parse_cache ---

def test_parse_cache_none_when_absent():
    assert parse_cache({}) is None


def test_parse_cache_int_returns_float():
    assert parse_cache({"cache": 5}) == 5.0


def test_parse_cache_float_returns_float():
    assert parse_cache({"cache": 2.5}) == 2.5


def test_parse_cache_zero_is_valid():
    assert parse_cache({"cache": 0}) == 0.0


def test_parse_cache_negative_raises():
    with pytest.raises(CacheError, match=">= 0"):
        parse_cache({"cache": -1})


def test_parse_cache_string_raises():
    with pytest.raises(CacheError, match="non-negative number"):
        parse_cache({"cache": "fast"})


def test_parse_cache_bool_raises():
    with pytest.raises(CacheError, match="non-negative number"):
        parse_cache({"cache": True})


# --- make_key ---

def test_make_key_uppercases_method():
    assert make_key("get", "/foo") == "GET:/foo:"


def test_make_key_includes_query():
    assert make_key("GET", "/search", "q=hello") == "GET:/search:q=hello"


# --- get / put ---

def test_get_returns_none_when_empty():
    assert get("GET:/missing:") is None


def test_put_and_get_returns_value():
    put("GET:/foo:", {"status": 200}, ttl=10.0)
    assert get("GET:/foo:") == {"status": 200}


def test_get_returns_none_after_expiry():
    put("GET:/bar:", "data", ttl=0.05)
    time.sleep(0.1)
    assert get("GET:/bar:") is None


def test_put_zero_ttl_does_not_store():
    put("GET:/baz:", "nope", ttl=0)
    assert get("GET:/baz:") is None


# --- invalidate ---

def test_invalidate_removes_entry():
    put("GET:/x:", "val", ttl=60)
    invalidate("GET:/x:")
    assert get("GET:/x:") is None


def test_invalidate_unknown_key_is_noop():
    invalidate("GET:/nonexistent:")  # should not raise


# --- clear / size ---

def test_clear_empties_store():
    put("GET:/a:", 1, ttl=60)
    put("GET:/b:", 2, ttl=60)
    clear()
    assert size() == 0


def test_size_reflects_entries():
    assert size() == 0
    put("GET:/p:", "v", ttl=60)
    assert size() == 1
