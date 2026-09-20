from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from gdguard import __version__
from gdguard.errors import GDGuardError
from gdguard.reporter import render_json, render_text
from gdguard.scanner import scan_project

EXIT_OK = 0
EXIT_CHECK_FAILED = 1
EXIT_USAGE = 2


def main(argv: Sequence[str] | None = None) -> int:
    _configure_stdio()
    parser = _build_parser()
    args: argparse.Namespace | None = None
    try:
        args = parser.parse_args(list(argv) if argv is not None else None)
        return _dispatch(args)
    except GDGuardError as exc:
        print(exc.message, file=sys.stderr)
        return exc.exit_code
    except SystemExit as exc:
        code = exc.code
        if code is None:
            return EXIT_OK
        if isinstance(code, int):
            return code
        print(str(code), file=sys.stderr)
        return EXIT_USAGE
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        if args is not None and args.verbose:
            traceback.print_exc()
        else:
            print(f"GDGuard failed: {exc}", file=sys.stderr)
            print("Re-run with --verbose for a full traceback.", file=sys.stderr)
        return EXIT_USAGE


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "check":
        return _run_check(args)
    parser = _build_parser()
    parser.print_help()
    return EXIT_USAGE


def _run_check(args: argparse.Namespace) -> int:
    target = Path(args.path)
    report = scan_project(
        target,
        godot_path=args.godot,
        import_project=args.import_project,
        headless=args.headless,
        dotnet_build=args.dotnet_build,
    )
    if args.format == "json":
        sys.stdout.write(render_json(report))
    else:
        sys.stdout.write(render_text(report))
    return EXIT_CHECK_FAILED if report.error_count else EXIT_OK


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gdguard",
        description="Godot-native project validation and CI checks.",
    )
    parser.add_argument("--version", action="version", version=f"gdguard {__version__}")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show Python traceback on unexpected failures.",
    )
    subparsers = parser.add_subparsers(dest="command")
    check = subparsers.add_parser("check", help="Validate a Godot project.")
    check.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Path to a Godot project directory (default: current directory).",
    )
    check.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format. JSON is machine-readable and contains no extra text.",
    )
    check.add_argument(
        "--godot",
        default=None,
        help="Optional path or executable name for the Godot binary.",
    )
    check.add_argument(
        "--import",
        dest="import_project",
        action="store_true",
        help="Run Godot editor import (may execute code and write caches).",
    )
    check.add_argument(
        "--headless",
        action="store_true",
        help="Run main-scene smoke test for one iteration; not a sandbox.",
    )
    check.add_argument(
        "--dotnet-build",
        action="store_true",
        help="Run dotnet build (may execute tasks and restore over network).",
    )
    check.add_argument(
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Show Python traceback on unexpected failures.",
    )
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
