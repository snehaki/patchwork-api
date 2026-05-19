"""Tests for patchwork.middleware and patchwork.builtin_middleware."""

import pytest

from patchwork.middleware import (
    MiddlewareChain,
    MiddlewareError,
    RequestContext,
    ResponseContext,
)
from patchwork.builtin_middleware import (
    cors_middleware,
    logging_middleware,
    make_api_key_middleware,
)


# ---------------------------------------------------------------------------
# RequestContext / ResponseContext
# ---------------------------------------------------------------------------

def make_ctx(method="GET", path="/test", headers=None, body=b""):
    return RequestContext(method, path, headers or {}, body)


def test_request_context_normalises_method():
    ctx = make_ctx(method="get")
    assert ctx.method == "GET"


def test_request_context_stores_fields():
    ctx = make_ctx(path="/hello", headers={"Content-Type": "application/json"}, body=b"{}")
    assert ctx.path == "/hello"
    assert ctx.headers["Content-Type"] == "application/json"
    assert ctx.body == b"{}"


def test_response_context_stores_fields():
    resp = ResponseContext(200, {"X-Foo": "bar"}, "ok")
    assert resp.status == 200
    assert resp.headers["X-Foo"] == "bar"
    assert resp.body == "ok"


# ---------------------------------------------------------------------------
# MiddlewareChain
# ---------------------------------------------------------------------------

def test_chain_starts_empty():
    chain = MiddlewareChain()
    assert len(chain) == 0


def test_chain_add_non_callable_raises():
    chain = MiddlewareChain()
    with pytest.raises(MiddlewareError):
        chain.add("not_a_function")  # type: ignore


def test_chain_process_request_all_pass_returns_none():
    chain = MiddlewareChain()
    chain.add(lambda ctx: None)
    chain.add(lambda ctx: None)
    assert chain.process_request(make_ctx()) is None


def test_chain_short_circuits_on_response():
    called = []

    def blocker(ctx):
        return ResponseContext(403, {}, "Forbidden")

    def should_not_run(ctx):
        called.append(True)

    chain = MiddlewareChain()
    chain.add(blocker)
    chain.add(should_not_run)
    resp = chain.process_request(make_ctx())
    assert resp is not None
    assert resp.status == 403
    assert called == []


def test_chain_wraps_middleware_exception():
    def bad(ctx):
        raise ValueError("boom")

    chain = MiddlewareChain()
    chain.add(bad)
    with pytest.raises(MiddlewareError, match="boom"):
        chain.process_request(make_ctx())


# ---------------------------------------------------------------------------
# Built-in middleware
# ---------------------------------------------------------------------------

def test_logging_middleware_sets_meta_and_returns_none():
    ctx = make_ctx()
    result = logging_middleware(ctx)
    assert result is None
    assert "request_start" in ctx.meta


def test_cors_middleware_options_returns_204():
    ctx = make_ctx(method="OPTIONS")
    resp = cors_middleware(ctx)
    assert resp is not None
    assert resp.status == 204


def test_cors_middleware_get_returns_none():
    assert cors_middleware(make_ctx(method="GET")) is None


def test_api_key_middleware_valid_key_passes():
    mw = make_api_key_middleware({"secret"})
    ctx = make_ctx(headers={"X-Api-Key": "secret"})
    assert mw(ctx) is None


def test_api_key_middleware_missing_key_returns_401():
    mw = make_api_key_middleware({"secret"})
    resp = mw(make_ctx())
    assert resp is not None
    assert resp.status == 401


def test_api_key_middleware_custom_header():
    mw = make_api_key_middleware({"tok"}, header="Authorization")
    ctx = make_ctx(headers={"Authorization": "tok"})
    assert mw(ctx) is None
