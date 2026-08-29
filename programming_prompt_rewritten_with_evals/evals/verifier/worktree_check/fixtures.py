"""Build temporary git fixtures for worktree self-tests."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

INITIAL_SUBJECT = "Initial empty commit"


def git_env() -> dict[str, str]:
    """Provide a local identity for fixture commits.

    Parameters: None.

    Returns: environment variables containing fallback git identity values.
    """
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Eval")
    env.setdefault("GIT_AUTHOR_EMAIL", "eval@local")
    env.setdefault("GIT_COMMITTER_NAME", "Eval")
    env.setdefault("GIT_COMMITTER_EMAIL", "eval@local")
    return env


def run_command(cwd: Path, *args: str) -> None:
    """Run one fixture command and require success.

    Parameters: cwd - working directory; args - command argv.

    Returns: None.
    """
    subprocess.run(
        list(args),
        cwd=str(cwd),
        check=True,
        env=git_env(),
        capture_output=True,
        text=True,
    )


def init_empty_repo(repo: Path) -> None:
    """Create a repository with one empty root commit.

    Parameters: repo - directory to initialize.

    Returns: None.
    """
    repo.mkdir(parents=True, exist_ok=True)
    run_command(repo, "git", "init", "-b", "master")
    run_command(repo, "git", "commit", "--allow-empty", "-m", INITIAL_SUBJECT)


def add_worktree(repo: Path, path: Path, *git_args: str) -> None:
    """Create a fixture worktree.

    Parameters: repo - main checkout; path - destination; git_args - arguments before the destination.

    Returns: None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    run_command(repo, "git", "worktree", "add", *git_args, str(path))


def merge_branch(repo: Path, branch: str) -> None:
    """Merge a fixture branch into master.

    Parameters: repo - live checkout; branch - feature branch.

    Returns: None.
    """
    run_command(repo, "git", "checkout", "master")
    run_command(repo, "git", "merge", "--no-ff", branch, "-m", f"Merge {branch}")


def write_python(path: Path, body: str = "def run():\n    return 1\n") -> None:
    """Write a small Python fixture.

    Parameters: path - destination file; body - file contents.

    Returns: None.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
