"""Tests for the patchwork CLI entry point."""

import os
import pytest
from unittest.mock import patch, MagicMock

from patchwork.cli import build_parser, main
from patchwork.registry import RouteConflictError
from patchwork.loader import LoaderError
from patchwork.validator import ValidationError


def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["./definitions"])
    assert args.definitions_dir == "./definitions"
    assert args.host == "127.0.0.1"
    assert args.port == 8080
    assert args.quiet is False


def test_build_parser_custom_host_and_port():
    parser = build_parser()
    args = parser.parse_args(["./defs", "--host", "0.0.0.0", "--port", "9000"])
    assert args.host == "0.0.0.0"
    assert args.port == 9000


def test_build_parser_quiet_flag():
    parser = build_parser()
    args = parser.parse_args(["./defs", "--quiet"])
    assert args.quiet is True


def test_main_missing_directory_returns_2(tmp_path):
    non_existent = str(tmp_path / "no_such_dir")
    result = main([non_existent])
    assert result == 2


def test_main_loader_error_returns_1(tmp_path):
    with patch("patchwork.cli.Registry") as MockRegistry:
        instance = MockRegistry.return_value
        instance.load_definitions.side_effect = LoaderError("bad file")
        result = main([str(tmp_path)])
    assert result == 1


def test_main_validation_error_returns_1(tmp_path):
    with patch("patchwork.cli.Registry") as MockRegistry:
        instance = MockRegistry.return_value
        instance.load_definitions.side_effect = ValidationError("invalid field")
        result = main([str(tmp_path)])
    assert result == 1


def test_main_route_conflict_error_returns_1(tmp_path):
    with patch("patchwork.cli.Registry") as MockRegistry:
        instance = MockRegistry.return_value
        instance.load_definitions.side_effect = RouteConflictError("duplicate")
        result = main([str(tmp_path)])
    assert result == 1


def test_main_calls_run_server(tmp_path):
    with patch("patchwork.cli.Registry") as MockRegistry, \
         patch("patchwork.cli.run_server") as mock_run:
        instance = MockRegistry.return_value
        instance.load_definitions.return_value = None
        instance.routes = {}
        result = main([str(tmp_path), "--host", "127.0.0.1", "--port", "8080", "--quiet"])
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    assert call_kwargs.kwargs.get("host") == "127.0.0.1"
    assert call_kwargs.kwargs.get("port") == 8080
    assert result == 0
