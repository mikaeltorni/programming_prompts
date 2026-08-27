"""Command-line interface for the Harbor benchmark launcher."""

from __future__ import annotations

import argparse
import sys

from .display import Display, X11Display, launch_preset
from .menu import menu_loop, print_preset_list
from .presets import load_preset_file, resolve_preset, write_shipped_presets
from .self_test import _self_test

CLI_DESCRIPTION = """Interactive Harbor benchmark launcher with git-tracked presets.

Opens one graphical terminal per job on the **same monitor** as the window
that started this program (the menu / ``./launch_benchmarks.sh``). Windows are
normal-sized and cascaded (not maximised or monitor-tiled). Presets live as
JSON under ``evals/presets/`` and are safe to commit.

Usage (from ``evals/``)::

    ./launch_benchmarks.sh
    ./launch_benchmarks.sh --preset positive-all-harnesses-all-judges
    ./launch_benchmarks.sh --preset baseline-codex-cc
    ./launch_benchmarks.sh --list
    ./launch_benchmarks.sh --write-presets
    ./launch_benchmarks.sh --self-test

Stdout is the menu / machine-readable lists. Diagnostics go to stderr.
Tests must not spawn real terminals; ``--self-test`` uses a fake display.
"""


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark launcher command-line interface.

    Parameters: argv - optional arguments excluding the executable name.

    Returns: process exit status.
    """
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument(
        "--preset",
        help="Launch this preset (stem or path) without the menu",
    )
    parser.add_argument("--list", action="store_true", help="Print presets and exit")
    parser.add_argument(
        "--write-presets",
        action="store_true",
        help="Rewrite shipped positive/baseline matrix JSON under presets/",
    )
    parser.add_argument("--self-test", action="store_true", help="Fixture checks")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="With --preset: log monitor + cascade placements, do not spawn windows",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.write_presets:
        write_shipped_presets()
        return 0
    if args.list:
        print_preset_list()
        return 0

    display: Display = X11Display()
    if args.preset:
        path = resolve_preset(args.preset)
        preset = load_preset_file(path)
        launch_preset(preset, display, dry_run=args.dry_run)
        return 0

    if not sys.stdin.isatty():
        print(
            "No TTY. Use --preset NAME, --list, or --self-test.",
            file=sys.stderr,
        )
        return 2
    return menu_loop(display)
