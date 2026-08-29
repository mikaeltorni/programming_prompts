"""Run and interpret git commands for worktree checks."""

from __future__ import annotations

import subprocess
from pathlib import Path


def run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git without raising on a non-zero exit.

    Parameters: repo - git working tree; args - git subcommand and flags.

    Returns: completed process with captured text output.
    """
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def git_ok(repo: Path, *args: str) -> str:
    """Return git stdout when the command succeeds.

    Parameters: repo - git working tree; args - git subcommand and flags.

    Returns: stripped stdout, or an empty string on failure.
    """
    proc = run_git(repo, *args)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def parse_worktrees(repo: Path) -> list[dict[str, str]]:
    """Parse git's porcelain worktree listing.

    Parameters: repo - git working tree.

    Returns: one field mapping per registered worktree.
    """
    proc = run_git(repo, "worktree", "list", "--porcelain")
    if proc.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def is_ancestor(repo: Path, ancestor: str, descendant: str) -> bool:
    """Check whether one commit belongs to another commit's history.

    Parameters: repo - git working tree; ancestor - expected ancestor hash; descendant - expected descendant hash.

    Returns: true when git confirms the ancestry relation.
    """
    return run_git(
        repo, "merge-base", "--is-ancestor", ancestor, descendant
    ).returncode == 0


def root_commits(repo: Path) -> list[str]:
    """List root commits reachable from HEAD.

    Parameters: repo - git working tree.

    Returns: root commit hashes.
    """
    return [
        line
        for line in git_ok(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()
        if line
    ]


def commit_has_files(repo: Path, commit: str) -> bool:
    """Check whether a commit contains file paths.

    Parameters: repo - git working tree; commit - commit hash to inspect.

    Returns: true when the commit tree contains at least one path.
    """
    text = git_ok(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--root",
        "-r",
        commit,
    )
    return bool(text.strip())
