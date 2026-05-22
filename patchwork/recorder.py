"""Request/response recorder for patchwork-api.

Records incoming requests and their matched responses so they can be
inspected or replayed later.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class RecorderError(Exception):
    """Raised when the recorder is used incorrectly."""


@dataclass
class RecordedEntry:
    method: str
    path: str
    query: str
    request_headers: Dict[str, str]
    status: int
    response_headers: Dict[str, str]
    body: Any
    params: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "path": self.path,
            "query": self.query,
            "request_headers": self.request_headers,
            "status": self.status,
            "response_headers": self.response_headers,
            "body": self.body,
            "params": self.params,
        }


class Recorder:
    """Thread-safe in-memory recorder."""

    def __init__(self, max_entries: int = 200) -> None:
        if max_entries < 1:
            raise RecorderError("max_entries must be at least 1")
        self._max = max_entries
        self._entries: List[RecordedEntry] = []
        self._lock = threading.Lock()

    def record(self, entry: RecordedEntry) -> None:
        """Append an entry, evicting the oldest if the buffer is full."""
        with self._lock:
            if len(self._entries) >= self._max:
                self._entries.pop(0)
            self._entries.append(entry)

    def all(self) -> List[RecordedEntry]:
        """Return a snapshot of all recorded entries."""
        with self._lock:
            return list(self._entries)

    def filter(self, *, method: Optional[str] = None, path: Optional[str] = None) -> List[RecordedEntry]:
        """Return entries matching optional method and/or path filters."""
        results = self.all()
        if method is not None:
            results = [e for e in results if e.method == method.upper()]
        if path is not None:
            results = [e for e in results if e.path == path]
        return results

    def clear(self) -> None:
        """Remove all recorded entries."""
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)
