"""YAML response definition loader for patchwork-api."""

import os
from pathlib import Path
from typing import Any

import yaml


class LoaderError(Exception):
    """Raised when a YAML definition file cannot be loaded or parsed."""


def load_yaml_file(path: str | Path) -> dict[str, Any]:
    """Load and parse a single YAML file.

    Args:
        path: Filesystem path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        LoaderError: If the file is missing, unreadable, or contains invalid YAML.
    """
    path = Path(path)
    if not path.exists():
        raise LoaderError(f"Definition file not found: {path}")
    if not path.is_file():
        raise LoaderError(f"Path is not a file: {path}")

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        raise LoaderError(f"Failed to parse YAML in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise LoaderError(
            f"Expected a YAML mapping at the top level in {path}, got {type(data).__name__}"
        )

    return data


def load_definitions_dir(directory: str | Path) -> list[dict[str, Any]]:
    """Recursively load all YAML definition files from a directory.

    Args:
        directory: Root directory to scan for ``*.yaml`` / ``*.yml`` files.

    Returns:
        List of parsed definition dictionaries, one per file.

    Raises:
        LoaderError: If the directory does not exist.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise LoaderError(f"Definitions directory not found: {directory}")

    definitions: list[dict[str, Any]] = []
    for root, _dirs, files in os.walk(directory):
        for filename in sorted(files):
            if filename.endswith((".yaml", ".yml")):
                file_path = Path(root) / filename
                definitions.append(load_yaml_file(file_path))

    return definitions
