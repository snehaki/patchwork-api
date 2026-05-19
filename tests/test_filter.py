"""Tests for patchwork.filter."""

import pytest

from patchwork.filter import (
    FilterError,
    _parse_query_string,
    _match_query_filters,
    filter_candidates,
)


# ---------------------------------------------------------------------------
# _parse_query_string
# ---------------------------------------------------------------------------

def test_parse_empty_string_returns_empty_dict():
    assert _parse_query_string("") == {}


def test_parse_single_pair():
    assert _parse_query_string("foo=bar") == {"foo": "bar"}


def test_parse_multiple_pairs():
    result = _parse_query_string("a=1&b=2&c=3")
    assert result == {"a": "1", "b": "2", "c": "3"}


def test_parse_key_without_value():
    assert _parse_query_string("flag") == {"flag": ""}


# ---------------------------------------------------------------------------
# _match_query_filters
# ---------------------------------------------------------------------------

def test_match_exact_value():
    assert _match_query_filters({"env": "prod"}, {"env": "prod"})


def test_match_exact_value_mismatch():
    assert not _match_query_filters({"env": "prod"}, {"env": "dev"})


def test_match_none_value_requires_key_present():
    assert _match_query_filters({"debug": None}, {"debug": ""})


def test_match_none_value_key_missing():
    assert not _match_query_filters({"debug": None}, {})


def test_match_wildcard_any_non_empty_value():
    assert _match_query_filters({"token": "*"}, {"token": "abc"})


def test_match_wildcard_empty_value_fails():
    assert not _match_query_filters({"token": "*"}, {"token": ""})


# ---------------------------------------------------------------------------
# filter_candidates
# ---------------------------------------------------------------------------

def _make(status: int, query=None) -> dict:
    d = {"status": status, "body": {}}
    if query is not None:
        d["query"] = query
    return d


def test_filter_candidates_empty_list_returns_none():
    assert filter_candidates([], "foo=bar") is None


def test_filter_candidates_no_query_key_is_catch_all():
    candidate = _make(200)
    assert filter_candidates([candidate], "") is candidate


def test_filter_candidates_exact_match_wins_over_catch_all():
    catch_all = _make(200)
    specific = _make(201, query={"env": "prod"})
    result = filter_candidates([catch_all, specific], "env=prod")
    assert result is specific


def test_filter_candidates_more_specific_wins():
    less = _make(200, query={"a": "1"})
    more = _make(201, query={"a": "1", "b": "2"})
    result = filter_candidates([less, more], "a=1&b=2")
    assert result is more


def test_filter_candidates_unmatched_specific_falls_back_to_catch_all():
    catch_all = _make(200)
    specific = _make(201, query={"env": "prod"})
    result = filter_candidates([catch_all, specific], "env=dev")
    assert result is catch_all


def test_filter_candidates_no_match_returns_none():
    specific = _make(201, query={"env": "prod"})
    assert filter_candidates([specific], "env=dev") is None


def test_filter_candidates_invalid_query_type_raises():
    bad = _make(200, query="not-a-dict")
    with pytest.raises(FilterError, match="mapping"):
        filter_candidates([bad], "foo=bar")
