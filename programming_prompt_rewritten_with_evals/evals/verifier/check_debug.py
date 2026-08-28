#!/usr/bin/env python3
"""Run the programmatic Harbor read-logs-first checker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from debug_check import check_repo, run_self_test
from worktree_check import write_reward

DEFAULT_REPO = Path("/Projects/app")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI options and run the requested debug check.

    Parameters: argv - optional argument override.

    Returns: process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        type=Path,
        default=DEFAULT_REPO,
        help="project checkout (default /Projects/app)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/logs/verifier/reward-debug.json"),
        help="reward JSON path",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run built-in pass/fail fixtures and exit",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    result = check_repo(args.repo)
    write_reward(
        result,
        args.output,
        criterion="read_logs_first",
        description="when .log/ exists, workspace Python matches the log diagnosis",
    )
    print(
        f"debug check: {'yes' if result.ok else 'no'} — {result.reasoning}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
