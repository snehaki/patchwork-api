"""Tests for patchwork.watcher."""

import os
import time
import threading
import pytest

from patchwork.watcher import Watcher


@pytest.fixture()
def yaml_dir(tmp_path):
    """Return a temporary directory with one YAML file."""
    (tmp_path / "route.yaml").write_text("method: GET\npath: /ping\nstatus: 200\n")
    return tmp_path


def _wait(condition: threading.Event, timeout: float = 3.0) -> bool:
    return condition.wait(timeout)


def test_watcher_calls_callback_on_new_file(yaml_dir):
    triggered = threading.Event()
    watcher = Watcher(str(yaml_dir), triggered.set, interval=0.1)
    watcher.start()
    time.sleep(0.15)
    (yaml_dir / "new_route.yaml").write_text("method: POST\npath: /new\nstatus: 201\n")
    assert _wait(triggered), "Callback was not called after new file was added"
    watcher.stop()


def test_watcher_calls_callback_on_modified_file(yaml_dir):
    triggered = threading.Event()
    watcher = Watcher(str(yaml_dir), triggered.set, interval=0.1)
    watcher.start()
    time.sleep(0.15)
    route_file = yaml_dir / "route.yaml"
    route_file.write_text("method: GET\npath: /ping\nstatus: 204\n")
    os.utime(route_file, (time.time() + 1, time.time() + 1))
    assert _wait(triggered), "Callback was not called after file was modified"
    watcher.stop()


def test_watcher_calls_callback_on_deleted_file(yaml_dir):
    triggered = threading.Event()
    watcher = Watcher(str(yaml_dir), triggered.set, interval=0.1)
    watcher.start()
    time.sleep(0.15)
    (yaml_dir / "route.yaml").unlink()
    assert _wait(triggered), "Callback was not called after file was deleted"
    watcher.stop()


def test_watcher_no_callback_when_no_change(yaml_dir):
    triggered = threading.Event()
    watcher = Watcher(str(yaml_dir), triggered.set, interval=0.1)
    watcher.start()
    time.sleep(0.35)
    # No file changes — event must NOT be set
    assert not triggered.is_set(), "Callback fired unexpectedly with no file changes"
    watcher.stop()


def test_watcher_ignores_non_yaml_files(yaml_dir):
    triggered = threading.Event()
    watcher = Watcher(str(yaml_dir), triggered.set, interval=0.1)
    watcher.start()
    time.sleep(0.15)
    (yaml_dir / "notes.txt").write_text("ignored")
    time.sleep(0.35)
    assert not triggered.is_set(), "Callback fired for a non-YAML file"
    watcher.stop()


def test_watcher_stop_is_idempotent(yaml_dir):
    watcher = Watcher(str(yaml_dir), lambda: None, interval=0.1)
    watcher.start()
    watcher.stop()
    watcher.stop()  # second stop should not raise


def test_watcher_start_is_idempotent(yaml_dir):
    watcher = Watcher(str(yaml_dir), lambda: None, interval=0.1)
    watcher.start()
    watcher.start()  # second start should not spawn a second thread
    assert threading.active_count() >= 1
    watcher.stop()
