"""Archive Harbor Projects layouts and reset copied clones."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .fsutil import copy_tree


def _projects_source(artifacts: Path) -> Path | None:
    """Locate the directory containing app or worktree artifacts.

    Parameters: artifacts - Harbor trial artifacts directory.

    Returns: projects source directory, or ``None`` when absent.
    """
    if not artifacts.is_dir():
        return None
    nested = artifacts / "Projects"
    if nested.is_dir() and ((nested / "app").exists() or (nested / ".worktrees").exists()):
        return nested
    if (artifacts / "app").exists() or (artifacts / ".worktrees").exists():
        return artifacts
    return None


def _git_output(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a captured git command without raising.

    Parameters: repo - copied repository; args - git arguments.

    Returns: completed git process.
    """
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def reset_clone_to_initial(repo: Path) -> None:
    """Reset a copied checkout to its empty initial commit.

    Parameters: repo - copied git checkout.

    Returns: nothing.
    """
    if not (repo / ".git").exists():
        return
    proc = _git_output(repo, "rev-list", "--max-parents=0", "HEAD")
    roots = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    if proc.returncode != 0 or not roots:
        return
    _git_output(repo, "reset", "--hard", roots[0])
    _git_output(repo, "clean", "-fd")
    _git_output(repo, "worktree", "prune")
    extra = repo / ".git" / "worktrees"
    if extra.is_dir():
        shutil.rmtree(extra, ignore_errors=True)


def archive_projects_layout(trial_dir: Path, dest_projects: Path) -> bool:
    """Copy one trial's simulated Projects tree.

    Parameters: trial_dir - Harbor trial directory; dest_projects - destination trial Projects directory.

    Returns: whether an app clone or worktree tree was written.
    """
    source = _projects_source(trial_dir / "artifacts")
    if source is None:
        return False
    dest_projects.mkdir(parents=True, exist_ok=True)
    src_app = source / "app"
    src_worktrees = source / ".worktrees"
    if src_app.exists():
        copy_tree(src_app, dest_projects / "app")
        reset_clone_to_initial(dest_projects / "app")
    if src_worktrees.exists():
        copy_tree(src_worktrees, dest_projects / ".worktrees")
    return (dest_projects / "app").exists() or (dest_projects / ".worktrees").exists()
