"""Hot-reload coordinator: ties the Watcher to the Registry."""

import logging
from typing import Optional

from patchwork.registry import Registry
from patchwork.watcher import Watcher

logger = logging.getLogger(__name__)


class Reloader:
    """Listens for file-system changes and rebuilds the Registry in place."""

    def __init__(self, registry: Registry, interval: float = 1.0) -> None:
        self.registry = registry
        self.interval = interval
        self._watcher: Optional[Watcher] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Begin watching the registry's source directory."""
        directory = self.registry.directory
        if directory is None:
            raise ValueError("Registry has no directory set; cannot start reloader.")
        self._watcher = Watcher(directory, self._reload, interval=self.interval)
        self._watcher.start()
        logger.info("Hot-reload enabled for directory: %s", directory)

    def stop(self) -> None:
        """Stop watching for changes."""
        if self._watcher:
            self._watcher.stop()
            self._watcher = None
        logger.info("Hot-reload disabled.")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _reload(self) -> None:
        """Clear and repopulate the registry from disk."""
        logger.info("Reloading definitions from %s", self.registry.directory)
        self.registry.clear()
        self.registry.load_definitions(self.registry.directory)  # type: ignore[arg-type]
        logger.info(
            "Reload complete — %d route(s) registered.",
            len(self.registry.routes),
        )
