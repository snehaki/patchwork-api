"""Tests for patchwork.limiter — RateLimiter and make_rate_limit_middleware."""

import pytest
from unittest.mock import MagicMock
from patchwork.limiter import RateLimiter, RateLimitExceeded, make_rate_limit_middleware
from patchwork.middleware import RequestContext, ResponseContext


# ---------------------------------------------------------------------------
# RateLimiter unit tests
# ---------------------------------------------------------------------------

def test_rate_limiter_allows_requests_within_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True


def test_rate_limiter_blocks_request_over_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    limiter.is_allowed("x")
    limiter.is_allowed("x")
    assert limiter.is_allowed("x") is False


def test_rate_limiter_tracks_clients_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.is_allowed("alice") is True
    assert limiter.is_allowed("bob") is True
    assert limiter.is_allowed("alice") is False


def test_rate_limiter_reset_clears_client_state():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    limiter.is_allowed("c")
    assert limiter.is_allowed("c") is False
    limiter.reset("c")
    assert limiter.is_allowed("c") is True


def test_rate_limiter_reset_unknown_key_is_noop():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    limiter.reset("nonexistent")  # should not raise


def test_rate_limiter_invalid_max_requests_raises():
    with pytest.raises(ValueError, match="max_requests"):
        RateLimiter(max_requests=0)


def test_rate_limiter_invalid_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        RateLimiter(max_requests=10, window_seconds=0)


def test_rate_limiter_expired_timestamps_are_evicted():
    """Requests older than the window should not count against the limit."""
    import time
    limiter = RateLimiter(max_requests=1, window_seconds=0.05)
    assert limiter.is_allowed("d") is True
    assert limiter.is_allowed("d") is False
    time.sleep(0.1)
    # Old timestamp evicted; request should be allowed again
    assert limiter.is_allowed("d") is True


# ---------------------------------------------------------------------------
# make_rate_limit_middleware tests
# ---------------------------------------------------------------------------

def _make_contexts(client="127.0.0.1"):
    req = RequestContext(method="GET", path="/test", headers={}, body=None, client_address=client)
    resp = ResponseContext(status=200, headers={}, body=None)
    return req, resp


def test_middleware_passes_through_when_allowed():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    mw = make_rate_limit_middleware(limiter)
    req, resp = _make_contexts()
    next_handler = MagicMock(return_value=resp)
    result = mw(req, resp, next_handler)
    next_handler.assert_called_once_with(req, resp)
    assert result is resp


def test_middleware_returns_429_when_limit_exceeded():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    mw = make_rate_limit_middleware(limiter)
    req, resp = _make_contexts()
    next_handler = MagicMock(return_value=resp)
    mw(req, resp, next_handler)  # first request — allowed
    req2, resp2 = _make_contexts()
    result = mw(req2, resp2, next_handler)  # second — blocked
    assert result.status == 429
    assert "error" in result.body
    assert "Retry-After" in result.headers


def test_middleware_retry_after_header_matches_window():
    limiter = RateLimiter(max_requests=1, window_seconds=30)
    mw = make_rate_limit_middleware(limiter)
    req, resp = _make_contexts("1.2.3.4")
    mw(req, resp, MagicMock(return_value=resp))
    req2, resp2 = _make_contexts("1.2.3.4")
    mw(req2, resp2, MagicMock(return_value=resp2))
    assert resp2.headers.get("Retry-After") == "30"


def test_middleware_uses_unknown_key_for_missing_client():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    mw = make_rate_limit_middleware(limiter)
    req = RequestContext(method="GET", path="/", headers={}, body=None, client_address=None)
    resp = ResponseContext(status=200, headers={}, body=None)
    result = mw(req, resp, MagicMock(return_value=resp))
    # Should not raise; client key falls back to "unknown"
    assert result is not None
