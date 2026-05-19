"""Tests for patchwork.reloader."""

import time
import threading
import pytest

from unittest.mock import MagicMock, patch, call

from patchwork.registry import Registry
from patchwork.reloader import Reloader


@pytest.fixture()
def registry_with_dir(tmp_path):
    (tmp_path / "ping.yaml").write_text(
        "method: GET\npath: /ping\nstatus: 200\nbody: ok\n"
    )
    reg = Registry()
    reg.load_definitions(str(tmp_path))
    return reg, tmp_path


def test_reloader_start_requires_directory():
    reg = Registry()
    reloader = Reloader(reg)
    with pytest.raises(ValueError, match="no directory"):
        reloader.start()


def test_reloader_start_and_stop(registry_with_dir):
    reg, _ = registry_with_dir
    reloader = Reloader(reg, interval=0.1)
    reloader.start()
    reloader.stop()
    assert reloader._watcher is None


def test_reloader_triggers_reload_on_change(registry_with_dir):
    reg, tmp_path = registry_with_dir
    reload_count = [0]

    original_reload = Reloader._reload

    def counting_reload(self):
        reload_count[0] += 1
        original_reload(self)

    with patch.object(Reloader, "_reload", counting_reload):
        reloader = Reloader(reg, interval=0.1)
        reloader.start()
        time.sleep(0.15)
        (tmp_path / "new.yaml").write_text(
            "method: POST\npath: /new\nstatus: 201\nbody: created\n"
        )
        time.sleep(0.4)
        reloader.stop()

    assert reload_count[0] >= 1


def test_reloader_reload_repopulates_registry(registry_with_dir):
    reg, tmp_path = registry_with_dir
    assert len(reg.routes) == 1

    (tmp_path / "extra.yaml").write_text(
        "method: DELETE\npath: /item\nstatus: 204\nbody: ''\n"
    )
    reloader = Reloader(reg, interval=0.1)
    reloader._reload()

    assert len(reg.routes) == 2


def test_reloader_stop_is_safe_when_not_started(registry_with_dir):
    reg, _ = registry_with_dir
    reloader = Reloader(reg, interval=0.1)
    reloader.stop()  # should not raise
