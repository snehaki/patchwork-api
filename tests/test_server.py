import json
import threading
import urllib.request
import urllib.error
import pytest

from patchwork.registry import Registry
from patchwork.server import create_server


DEF_GET_HELLO = {
    "method": "GET",
    "path": "/hello",
    "status": 200,
    "body": {"message": "hello world"},
}

DEF_POST_ECHO = {
    "method": "POST",
    "path": "/echo",
    "status": 201,
    "body": "created",
    "headers": {"X-Custom": "yes"},
}


@pytest.fixture(scope="module")
def live_server():
    registry = Registry()
    registry.register(DEF_GET_HELLO)
    registry.register(DEF_POST_ECHO)

    server = create_server(registry, host="127.0.0.1", port=19876)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield "http://127.0.0.1:19876"
    server.shutdown()


def test_get_known_route_returns_200(live_server):
    with urllib.request.urlopen(f"{live_server}/hello") as resp:
        assert resp.status == 200
        data = json.loads(resp.read())
        assert data == {"message": "hello world"}


def test_get_known_route_content_type_json(live_server):
    with urllib.request.urlopen(f"{live_server}/hello") as resp:
        assert "application/json" in resp.headers.get("Content-Type", "")


def test_post_known_route_returns_201(live_server):
    req = urllib.request.Request(f"{live_server}/echo", method="POST", data=b"")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 201
        assert resp.read().decode() == "created"


def test_post_known_route_custom_header(live_server):
    req = urllib.request.Request(f"{live_server}/echo", method="POST", data=b"")
    with urllib.request.urlopen(req) as resp:
        assert resp.headers.get("X-Custom") == "yes"


def test_unknown_route_returns_404(live_server):
    req = urllib.request.Request(f"{live_server}/not-found")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    assert exc_info.value.code == 404


def test_unknown_route_returns_json_error(live_server):
    req = urllib.request.Request(f"{live_server}/not-found")
    with pytest.raises(urllib.error.HTTPError) as exc_info:
        urllib.request.urlopen(req)
    body = json.loads(exc_info.value.read())
    assert "error" in body
    assert body["path"] == "/not-found"
