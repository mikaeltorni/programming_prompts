#!/usr/bin/env python3
"""Run the programmatic Harbor worktree-layout checker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from worktree_check import check_repo, run_self_test, write_reward

DEFAULT_REPO = Path("/Projects/app")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI options and run the requested worktree check.

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
        default=Path("/logs/verifier/reward-worktree.json"),
        help="reward JSON path",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run built-in pass/fail layout fixtures and exit",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    result = check_repo(args.repo)
    write_reward(result, args.output)
    print(
        f"worktree check: {'yes' if result.ok else 'no'} — {result.reasoning}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
