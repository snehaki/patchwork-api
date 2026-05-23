"""Tests for patchwork.cors."""

import pytest

from patchwork.cors import (
    CORSError,
    build_cors_headers,
    parse_cors,
)


# ---------------------------------------------------------------------------
# parse_cors
# ---------------------------------------------------------------------------

def test_parse_cors_none_when_absent():
    assert parse_cors(None) is None


def test_parse_cors_not_a_mapping_raises():
    with pytest.raises(CORSError, match="mapping"):
        parse_cors("*")


def test_parse_cors_defaults():
    cfg = parse_cors({})
    assert cfg["origins"] == ["*"]
    assert "GET" in cfg["methods"]
    assert cfg["allow_credentials"] is False
    assert cfg["max_age"] is None


def test_parse_cors_custom_origins():
    cfg = parse_cors({"origins": ["https://example.com"]})
    assert cfg["origins"] == ["https://example.com"]


def test_parse_cors_empty_origins_raises():
    with pytest.raises(CORSError, match="not be empty"):
        parse_cors({"origins": []})


def test_parse_cors_origins_not_list_raises():
    with pytest.raises(CORSError, match="list of strings"):
        parse_cors({"origins": "*"})


def test_parse_cors_methods_uppercased():
    cfg = parse_cors({"methods": ["get", "post"]})
    assert cfg["methods"] == ["GET", "POST"]


def test_parse_cors_invalid_methods_raises():
    with pytest.raises(CORSError, match="list of strings"):
        parse_cors({"methods": "GET"})


def test_parse_cors_max_age_converted_to_float():
    cfg = parse_cors({"max_age": 600})
    assert cfg["max_age"] == 600.0


def test_parse_cors_negative_max_age_raises():
    with pytest.raises(CORSError, match="non-negative"):
        parse_cors({"max_age": -1})


def test_parse_cors_allow_credentials_true():
    cfg = parse_cors({"allow_credentials": True})
    assert cfg["allow_credentials"] is True


def test_parse_cors_allow_credentials_non_bool_raises():
    with pytest.raises(CORSError, match="boolean"):
        parse_cors({"allow_credentials": "yes"})


# ---------------------------------------------------------------------------
# build_cors_headers
# ---------------------------------------------------------------------------

def test_build_cors_headers_wildcard_origin():
    cfg = parse_cors({})
    headers = build_cors_headers(cfg)
    assert headers["Access-Control-Allow-Origin"] == "*"


def test_build_cors_headers_reflects_matching_origin():
    cfg = parse_cors({"origins": ["https://a.com", "https://b.com"]})
    headers = build_cors_headers(cfg, request_origin="https://b.com")
    assert headers["Access-Control-Allow-Origin"] == "https://b.com"


def test_build_cors_headers_unmatched_origin_uses_first():
    cfg = parse_cors({"origins": ["https://a.com"]})
    headers = build_cors_headers(cfg, request_origin="https://evil.com")
    assert headers["Access-Control-Allow-Origin"] == "https://a.com"


def test_build_cors_headers_includes_methods_and_headers():
    cfg = parse_cors({"methods": ["GET"], "headers": ["X-Custom"]})
    headers = build_cors_headers(cfg)
    assert headers["Access-Control-Allow-Methods"] == "GET"
    assert headers["Access-Control-Allow-Headers"] == "X-Custom"


def test_build_cors_headers_credentials_present_when_true():
    cfg = parse_cors({"allow_credentials": True})
    headers = build_cors_headers(cfg)
    assert headers["Access-Control-Allow-Credentials"] == "true"


def test_build_cors_headers_credentials_absent_when_false():
    cfg = parse_cors({})
    headers = build_cors_headers(cfg)
    assert "Access-Control-Allow-Credentials" not in headers


def test_build_cors_headers_max_age_present():
    cfg = parse_cors({"max_age": 3600})
    headers = build_cors_headers(cfg)
    assert headers["Access-Control-Max-Age"] == "3600"


def test_build_cors_headers_max_age_absent_when_none():
    cfg = parse_cors({})
    headers = build_cors_headers(cfg)
    assert "Access-Control-Max-Age" not in headers
