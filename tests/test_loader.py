"""Tests for patchwork.loader."""

import textwrap
from pathlib import Path

import pytest

from patchwork.loader import LoaderError, load_definitions_dir, load_yaml_file


# ---------------------------------------------------------------------------
# load_yaml_file
# ---------------------------------------------------------------------------


def test_load_yaml_file_returns_dict(tmp_path: Path) -> None:
    yaml_file = tmp_path / "route.yaml"
    yaml_file.write_text("method: GET\npath: /hello\n", encoding="utf-8")
    result = load_yaml_file(yaml_file)
    assert result == {"method": "GET", "path": "/hello"}


def test_load_yaml_file_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(LoaderError, match="not found"):
        load_yaml_file(tmp_path / "nonexistent.yaml")


def test_load_yaml_file_invalid_yaml_raises(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("key: [unclosed", encoding="utf-8")
    with pytest.raises(LoaderError, match="Failed to parse YAML"):
        load_yaml_file(bad_file)


def test_load_yaml_file_non_mapping_raises(tmp_path: Path) -> None:
    list_file = tmp_path / "list.yaml"
    list_file.write_text("- item1\n- item2\n", encoding="utf-8")
    with pytest.raises(LoaderError, match="Expected a YAML mapping"):
        load_yaml_file(list_file)


def test_load_yaml_file_path_is_directory_raises(tmp_path: Path) -> None:
    with pytest.raises(LoaderError, match="not a file"):
        load_yaml_file(tmp_path)


# ---------------------------------------------------------------------------
# load_definitions_dir
# ---------------------------------------------------------------------------


def test_load_definitions_dir_returns_all_yaml(tmp_path: Path) -> None:
    (tmp_path / "a.yaml").write_text("id: a\n", encoding="utf-8")
    (tmp_path / "b.yml").write_text("id: b\n", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("not yaml", encoding="utf-8")

    results = load_definitions_dir(tmp_path)
    ids = {r["id"] for r in results}
    assert ids == {"a", "b"}
    assert len(results) == 2


def test_load_definitions_dir_recurses_subdirs(tmp_path: Path) -> None:
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.yaml").write_text("id: root\n", encoding="utf-8")
    (sub / "child.yaml").write_text("id: child\n", encoding="utf-8")

    results = load_definitions_dir(tmp_path)
    ids = {r["id"] for r in results}
    assert ids == {"root", "child"}


def test_load_definitions_dir_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(LoaderError, match="not found"):
        load_definitions_dir(tmp_path / "no_such_dir")


def test_load_definitions_dir_empty_returns_empty_list(tmp_path: Path) -> None:
    assert load_definitions_dir(tmp_path) == []
