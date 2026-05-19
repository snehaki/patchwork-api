"""File system watcher that reloads route definitions when YAML files change."""

import os
import time
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)


class Watcher:
    """Monitors a directory for YAML file changes and triggers a reload callback."""

    def __init__(
        self,
        directory: str,
        callback: Callable[[], None],
        interval: float = 1.0,
    ) -> None:
        self.directory = directory
        self.callback = callback
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._snapshots: dict[str, float] = {}

    def _take_snapshot(self) -> dict[str, float]:
        """Return a mapping of YAML file paths to their last-modified timestamps."""
        snapshot: dict[str, float] = {}
        try:
            for entry in os.scandir(self.directory):
                if entry.is_file() and entry.name.endswith((".yaml", ".yml")):
                    snapshot[entry.path] = entry.stat().st_mtime
        except OSError as exc:
            logger.warning("Watcher could not scan directory: %s", exc)
        return snapshot

    def _has_changed(self, current: dict[str, float]) -> bool:
        return current != self._snapshots

    def _run(self) -> None:
        self._snapshots = self._take_snapshot()
        while not self._stop_event.wait(self.interval):
            current = self._take_snapshot()
            if self._has_changed(current):
                logger.info("Change detected in %s — reloading definitions.", self.directory)
                self._snapshots = current
                try:
                    self.callback()
                except Exception as exc:  # noqa: BLE001
                    logger.error("Reload callback raised an error: %s", exc)

    def start(self) -> None:
        """Start the background watcher thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="patchwork-watcher")
        self._thread.start()
        logger.debug("Watcher started for directory: %s", self.directory)

    def stop(self) -> None:
        """Stop the background watcher thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)
        logger.debug("Watcher stopped.")
