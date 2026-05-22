"""Tests for patchwork.proxy."""

from __future__ import annotations

import http.client
from unittest.mock import MagicMock, patch

import pytest

from patchwork.proxy import ProxyError, _parse_upstream, forward_request


# ---------------------------------------------------------------------------
# _parse_upstream
# ---------------------------------------------------------------------------

def test_parse_upstream_http():
    host, base, ssl = _parse_upstream("http://localhost:8080")
    assert host == "localhost:8080"
    assert base == ""
    assert ssl is False


def test_parse_upstream_https():
    host, base, ssl = _parse_upstream("https://api.example.com")
    assert host == "api.example.com"
    assert ssl is True


def test_parse_upstream_with_base_path():
    host, base, ssl = _parse_upstream("http://example.com/v1/")
    assert base == "/v1"


def test_parse_upstream_unsupported_scheme_raises():
    with pytest.raises(ProxyError, match="Unsupported scheme"):
        _parse_upstream("ftp://example.com")


def test_parse_upstream_missing_host_raises():
    with pytest.raises(ProxyError, match="Missing host"):
        _parse_upstream("http://")


# ---------------------------------------------------------------------------
# forward_request — happy path (mocked connection)
# ---------------------------------------------------------------------------

def _make_mock_response(status: int, headers: list, body: bytes):
    mock_resp = MagicMock()
    mock_resp.status = status
    mock_resp.read.return_value = body
    mock_resp.getheaders.return_value = headers
    return mock_resp


def _patch_conn(mock_resp):
    mock_conn = MagicMock()
    mock_conn.getresponse.return_value = mock_resp
    return mock_conn


def test_forward_request_returns_status_headers_body():
    mock_resp = _make_mock_response(200, [("content-type", "application/json")], b'{"ok": true}')
    mock_conn = _patch_conn(mock_resp)

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        status, headers, body = forward_request(
            "http://example.com", "GET", "/ping", {}
        )

    assert status == 200
    assert headers["content-type"] == "application/json"
    assert body == b'{"ok": true}'
    mock_conn.request.assert_called_once_with("GET", "/ping", body=None, headers={})


def test_forward_request_strips_hop_by_hop_headers():
    mock_resp = _make_mock_response(204, [], b"")
    mock_conn = _patch_conn(mock_resp)

    dirty_headers = {"Connection": "keep-alive", "X-Custom": "yes", "Transfer-Encoding": "chunked"}

    with patch("http.client.HTTPConnection", return_value=mock_conn):
        forward_request("http://example.com", "POST", "/data", dirty_headers, body=b"{}")

    _, _, kwargs = mock_conn.request.mock_calls[0]
    forwarded = mock_conn.request.call_args[1]["headers"]
    assert "X-Custom" in forwarded
    assert "Connection" not in forwarded
    assert "Transfer-Encoding" not in forwarded


def test_forward_request_os_error_raises_proxy_error():
    with patch("http.client.HTTPConnection") as mock_cls:
        mock_cls.return_value.request.side_effect = OSError("refused")
        with pytest.raises(ProxyError, match="Connection to upstream"):
            forward_request("http://example.com", "GET", "/", {})


def test_forward_request_uses_https_connection():
    mock_resp = _make_mock_response(200, [], b"")
    mock_conn = _patch_conn(mock_resp)

    with patch("http.client.HTTPSConnection", return_value=mock_conn) as mock_cls:
        forward_request("https://secure.example.com", "GET", "/", {})
        mock_cls.assert_called_once_with("secure.example.com", timeout=10.0)
