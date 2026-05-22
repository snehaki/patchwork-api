"""Tests for patchwork.recorder and patchwork.recorder_routes."""

import pytest

from patchwork.recorder import Recorder, RecorderError, RecordedEntry
from patchwork.recorder_routes import handle_recorder_request


def _entry(method="GET", path="/foo", status=200, query=""):
    return RecordedEntry(
        method=method,
        path=path,
        query=query,
        request_headers={},
        status=status,
        response_headers={"Content-Type": "application/json"},
        body={"ok": True},
    )


# ---------------------------------------------------------------------------
# Recorder unit tests
# ---------------------------------------------------------------------------

def test_recorder_starts_empty():
    r = Recorder()
    assert len(r) == 0


def test_recorder_records_entry():
    r = Recorder()
    r.record(_entry())
    assert len(r) == 1


def test_recorder_all_returns_snapshot():
    r = Recorder()
    r.record(_entry(path="/a"))
    r.record(_entry(path="/b"))
    entries = r.all()
    assert [e.path for e in entries] == ["/a", "/b"]


def test_recorder_evicts_oldest_when_full():
    r = Recorder(max_entries=2)
    r.record(_entry(path="/a"))
    r.record(_entry(path="/b"))
    r.record(_entry(path="/c"))
    paths = [e.path for e in r.all()]
    assert paths == ["/b", "/c"]


def test_recorder_clear_removes_all():
    r = Recorder()
    r.record(_entry())
    r.clear()
    assert len(r) == 0


def test_recorder_filter_by_method():
    r = Recorder()
    r.record(_entry(method="GET"))
    r.record(_entry(method="POST"))
    results = r.filter(method="GET")
    assert all(e.method == "GET" for e in results)
    assert len(results) == 1


def test_recorder_filter_by_path():
    r = Recorder()
    r.record(_entry(path="/foo"))
    r.record(_entry(path="/bar"))
    results = r.filter(path="/foo")
    assert len(results) == 1 and results[0].path == "/foo"


def test_recorder_max_entries_must_be_positive():
    with pytest.raises(RecorderError):
        Recorder(max_entries=0)


def test_recorded_entry_to_dict_has_expected_keys():
    e = _entry()
    d = e.to_dict()
    for key in ("method", "path", "query", "request_headers", "status", "response_headers", "body"):
        assert key in d


# ---------------------------------------------------------------------------
# recorder_routes tests
# ---------------------------------------------------------------------------

def _call(method, path, query="", recorder=None):
    if recorder is None:
        recorder = Recorder()
    return handle_recorder_request(method, path, query, recorder)


def test_non_recorder_path_returns_none():
    assert _call("GET", "/api/data") is None


def test_list_entries_empty():
    resp = _call("GET", "/_patchwork/recorder")
    import json
    body = json.loads(resp["body"])
    assert body["count"] == 0 and body["entries"] == []


def test_list_entries_returns_recorded():
    import json
    r = Recorder()
    r.record(_entry(path="/hello"))
    resp = handle_recorder_request("GET", "/_patchwork/recorder", "", r)
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["entries"][0]["path"] == "/hello"


def test_delete_clears_recorder():
    import json
    r = Recorder()
    r.record(_entry())
    resp = handle_recorder_request("DELETE", "/_patchwork/recorder", "", r)
    body = json.loads(resp["body"])
    assert body["cleared"] is True
    assert len(r) == 0


def test_filter_route_by_method():
    import json
    r = Recorder()
    r.record(_entry(method="GET"))
    r.record(_entry(method="POST"))
    resp = handle_recorder_request("GET", "/_patchwork/recorder/filter", "method=POST", r)
    body = json.loads(resp["body"])
    assert body["count"] == 1
    assert body["entries"][0]["method"] == "POST"


def test_unknown_sub_route_returns_404():
    resp = _call("GET", "/_patchwork/recorder/unknown")
    assert resp["status"] == 404
