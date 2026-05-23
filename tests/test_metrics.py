"""Tests for patchwork.metrics."""

import pytest
from patchwork.metrics import record, snapshot, reset, Timer, MetricsError


@pytest.fixture(autouse=True)
def clean_state():
    reset()
    yield
    reset()


def test_record_increments_count():
    record("GET", "/users", 200, 0.01)
    data = snapshot()
    assert data["GET /users"]["count"] == 1


def test_record_accumulates_multiple_calls():
    record("GET", "/users", 200, 0.01)
    record("GET", "/users", 200, 0.03)
    data = snapshot()
    assert data["GET /users"]["count"] == 2


def test_record_tracks_status_codes():
    record("POST", "/items", 201, 0.05)
    record("POST", "/items", 400, 0.02)
    data = snapshot()
    statuses = data["POST /items"]["statuses"]
    assert statuses["201"] == 1
    assert statuses["400"] == 1


def test_record_computes_avg_ms():
    record("GET", "/ping", 200, 0.1)   # 100 ms
    record("GET", "/ping", 200, 0.3)   # 300 ms
    data = snapshot()
    assert data["GET /ping"]["avg_ms"] == pytest.approx(200.0, rel=1e-3)


def test_record_negative_elapsed_raises():
    with pytest.raises(MetricsError):
        record("GET", "/x", 200, -0.1)


def test_snapshot_returns_copy():
    record("GET", "/a", 200, 0.01)
    s1 = snapshot()
    record("GET", "/a", 200, 0.01)
    s2 = snapshot()
    assert s1["GET /a"]["count"] == 1
    assert s2["GET /a"]["count"] == 2


def test_reset_clears_all():
    record("GET", "/z", 200, 0.01)
    reset()
    assert snapshot() == {}


def test_method_is_uppercased():
    record("get", "/lower", 200, 0.0)
    data = snapshot()
    assert "GET /lower" in data


def test_timer_records_on_exit():
    with Timer("GET", "/timed") as t:
        t.status = 204
    data = snapshot()
    assert "GET /timed" in data
    assert data["GET /timed"]["statuses"]["204"] == 1


def test_timer_default_status_is_200():
    with Timer("DELETE", "/res"):
        pass
    data = snapshot()
    assert data["DELETE /res"]["statuses"]["200"] == 1
