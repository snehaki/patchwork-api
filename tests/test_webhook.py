"""Tests for patchwork.webhook."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch

import pytest

from patchwork.webhook import (
    WebhookError,
    fire_webhook,
    parse_webhook,
)


# ---------------------------------------------------------------------------
# parse_webhook
# ---------------------------------------------------------------------------

def test_parse_webhook_none_when_absent():
    assert parse_webhook({}) is None


def test_parse_webhook_returns_config():
    cfg = parse_webhook({"webhook": {"url": "http://example.com/hook"}})
    assert cfg["url"] == "http://example.com/hook"
    assert cfg["method"] == "POST"
    assert cfg["async"] is True


def test_parse_webhook_custom_method():
    cfg = parse_webhook({"webhook": {"url": "http://x.test/", "method": "put"}})
    assert cfg["method"] == "PUT"


def test_parse_webhook_not_a_mapping_raises():
    with pytest.raises(WebhookError, match="mapping"):
        parse_webhook({"webhook": "http://bad"})


def test_parse_webhook_missing_url_raises():
    with pytest.raises(WebhookError, match="url.*required"):
        parse_webhook({"webhook": {}})


def test_parse_webhook_url_not_string_raises():
    with pytest.raises(WebhookError, match="string"):
        parse_webhook({"webhook": {"url": 123}})


def test_parse_webhook_bad_scheme_raises():
    with pytest.raises(WebhookError, match="http"):
        parse_webhook({"webhook": {"url": "ftp://example.com"}})


def test_parse_webhook_unsupported_method_raises():
    with pytest.raises(WebhookError, match="unsupported"):
        parse_webhook({"webhook": {"url": "http://x.test/", "method": "HEAD"}})


def test_parse_webhook_async_false():
    cfg = parse_webhook({"webhook": {"url": "http://x.test/", "async": False}})
    assert cfg["async"] is False


# ---------------------------------------------------------------------------
# fire_webhook (synchronous path, using a tiny local HTTP server)
# ---------------------------------------------------------------------------

class _Collector(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        _Collector.received.append({"method": "POST", "body": body})
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args):
        pass


def test_fire_webhook_sends_post(tmp_path):
    _Collector.received.clear()
    srv = HTTPServer(("127.0.0.1", 0), _Collector)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.handle_request)
    t.start()

    config = {
        "url": f"http://127.0.0.1:{port}/hook",
        "method": "POST",
        "headers": {},
        "body": {"event": "hit"},
        "async": False,
    }
    fire_webhook(config, {})
    t.join(timeout=3)
    srv.server_close()

    assert len(_Collector.received) == 1
    payload = json.loads(_Collector.received[0]["body"])
    assert payload["event"] == "hit"


def test_fire_webhook_async_does_not_block():
    """Async fire should return immediately even if the target is unreachable."""
    config = {
        "url": "http://127.0.0.1:1/unreachable",
        "method": "POST",
        "headers": {},
        "body": None,
        "async": True,
    }
    # Should not raise and should return quickly
    fire_webhook(config, {})
