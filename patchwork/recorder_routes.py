"""Management routes for the request recorder (/_patchwork/recorder/*)."""

from __future__ import annotations

import json
from typing import Optional

from patchwork.recorder import Recorder

_PREFIX = "/_patchwork/recorder"


def _json_response(data: object) -> dict:
    return {
        "status": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(data),
    }


def _error(status: int, message: str) -> dict:
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": message}),
    }


def handle_recorder_request(
    method: str,
    path: str,
    query: str,
    recorder: Recorder,
) -> Optional[dict]:
    """Handle a recorder management request.

    Returns a response dict or None if the path is not a recorder route.
    """
    if not path.startswith(_PREFIX):
        return None

    sub = path[len(_PREFIX):].rstrip("/") or "/"

    # GET /_patchwork/recorder  — list all entries
    if sub == "/" and method == "GET":
        entries = [e.to_dict() for e in recorder.all()]
        return _json_response({"count": len(entries), "entries": entries})

    # DELETE /_patchwork/recorder  — clear all entries
    if sub == "/" and method == "DELETE":
        recorder.clear()
        return _json_response({"cleared": True})

    # GET /_patchwork/recorder/filter?method=GET&path=/foo
    if sub == "/filter" and method == "GET":
        params: dict = {}
        for part in query.split("&"):
            if "=" in part:
                k, v = part.split("=", 1)
                params[k] = v
        filter_method = params.get("method") or None
        filter_path = params.get("path") or None
        entries = [e.to_dict() for e in recorder.filter(method=filter_method, path=filter_path)]
        return _json_response({"count": len(entries), "entries": entries})

    return _error(404, f"unknown recorder route: {path}")
