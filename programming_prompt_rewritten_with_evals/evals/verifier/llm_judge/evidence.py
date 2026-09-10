"""Read-only Git evidence for semantic judges; no task-specific scoring.

Run this file with --repo PATH and optionally --commit REV [--path FILE].
The default JSON report lists history, parents, changed paths and worktrees.
Commit mode returns the actual diff or a source blob, without checking out refs.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_judge.log import log


def git(repo: Path, *args: str) -> str:
    """Run a bounded Git read and expose failures instead of empty evidence."""
    proc = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if proc.returncode:
        raise ValueError(proc.stderr.strip() or "Git evidence command failed")
    return proc.stdout


def history(repo: Path) -> dict:
    """Collect reachable commits in parent order, including merge topology."""
    commits = []
    for line in git(repo, "rev-list", "--reverse", "--topo-order", "--parents", "HEAD").splitlines():
        commit, *parents = line.split()
        commits.append({
            "commit": commit, "parents": parents,
            "subject": git(repo, "show", "-s", "--format=%s", commit).strip(),
            "changed_paths": git(repo, "diff-tree", "--root", "--no-commit-id",
                                 "--name-status", "-r", commit).splitlines(),
        })
    log(f"collected Git evidence commits={len(commits)}")
    return {
        "repository": str(repo.resolve()), "commits": commits,
        "worktrees": git(repo, "worktree", "list", "--porcelain"),
        "note": "Subjects and counts are not proof; inspect diffs and source at each feature boundary.",
    }


def main() -> int:
    """Print evidence to stdout; errors are explicit and never a failing score."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit")
    parser.add_argument("--path", help="source path at --commit; omit for its diff")
    args = parser.parse_args()
    if args.path and not args.commit:
        parser.error("--path requires --commit")
    try:
        if args.commit:
            commit = git(args.repo, "rev-parse", "--verify", "--end-of-options",
                         args.commit + "^{commit}").strip()
            log(f"reading commit evidence commit={commit}")
            if args.path:
                print(git(args.repo, "show", f"{commit}:{args.path}"), end="")
            else:
                print(git(args.repo, "show", "--format=fuller", "--no-ext-diff",
                          "--no-textconv", commit, "--"), end="")
        else:
            print(json.dumps(history(args.repo), indent=2))
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        log(f"evidence unavailable: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
