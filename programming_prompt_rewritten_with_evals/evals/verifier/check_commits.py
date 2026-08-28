#!/usr/bin/env python3
"""Run the programmatic Harbor feature-commits checker."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from commits_check import check_repo, parse_feature_spec, run_self_test
from worktree_check import write_reward

DEFAULT_REPO = Path("/Projects/app")


def main(argv: list[str] | None = None) -> int:
    """Parse CLI options and run the requested commits check.

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
        default=Path("/logs/verifier/reward-commits.json"),
        help="reward JSON path",
    )
    parser.add_argument(
        "--feature-count-file",
        type=Path,
        default=Path("/tests/feature_count.txt"),
        help="file with Feature count (first line) and optional per-commit markers",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run built-in pass/fail fixtures and exit",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    required, markers = parse_feature_spec(args.feature_count_file)
    result = check_repo(args.repo, required=required, markers=markers)
    write_reward(
        result,
        args.output,
        criterion="feature_commits",
        description="one Python commit per Feature; later Features must not already be in earlier commits",
    )
    print(
        f"commits check: {'yes' if result.ok else 'no'} — {result.reasoning}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
