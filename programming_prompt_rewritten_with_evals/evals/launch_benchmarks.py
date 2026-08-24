#!/usr/bin/env python3
"""Interactive Harbor benchmark launcher with git-tracked presets.

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

from launcher.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
