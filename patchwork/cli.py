"""Command-line interface for the Patchwork mock API server."""

import argparse
import sys
import os

from patchwork.registry import Registry, RouteConflictError
from patchwork.loader import LoaderError
from patchwork.validator import ValidationError
from patchwork.server import run_server


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patchwork",
        description="Lightweight mock API server powered by YAML definitions.",
    )
    parser.add_argument(
        "definitions_dir",
        metavar="DIR",
        help="Path to directory containing YAML route definition files.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind the server to (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port number to listen on (default: 8080).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress startup and request log output.",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    definitions_dir = os.path.abspath(args.definitions_dir)

    if not os.path.isdir(definitions_dir):
        print(f"error: '{definitions_dir}' is not a directory.", file=sys.stderr)
        return 2

    registry = Registry()
    try:
        registry.load_definitions(definitions_dir)
    except (LoaderError, ValidationError, RouteConflictError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        route_count = len(registry.routes)
        print(
            f"Loaded {route_count} route(s) from '{definitions_dir}'.\n"
            f"Starting Patchwork server on http://{args.host}:{args.port} ..."
        )

    run_server(registry, host=args.host, port=args.port, quiet=args.quiet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
