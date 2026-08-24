"""Apply the Harbor worktree-layout rules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .git_io import (
    commit_has_files,
    git_ok,
    is_ancestor,
    parse_worktrees,
    root_commits,
    run_git,
)


@dataclass(frozen=True)
class CheckResult:
    """Represent one worktree-layout inspection.

    Parameters: ok - whether every rule passed; reasoning - human-readable outcome.

    Returns: immutable worktree check result.
    """

    ok: bool
    reasoning: str


def expected_store(repo: Path) -> Path:
    """Build the required sibling worktree-store path.

    Parameters: repo - resolved project checkout.

    Returns: the parent .worktrees directory for this project.
    """
    resolved = repo.resolve()
    return resolved.parent / ".worktrees" / resolved.name


def is_default_branch(branch: str) -> bool:
    """Recognize the supported default branch names.

    Parameters: branch - short name or refs/heads name.

    Returns: true for master or main.
    """
    return branch.removeprefix("refs/heads/") in {"master", "main"}


def check_repo(repo: Path) -> CheckResult:
    """Inspect a checkout against the worktree eval contract.

    Parameters: repo - project checkout initialized with an empty root commit.

    Returns: pass/fail state and reasoning.
    """
    repo = repo.resolve()
    if not (repo / ".git").exists() and run_git(
        repo, "rev-parse", "--is-inside-work-tree"
    ).returncode != 0:
        return CheckResult(False, f"{repo} is not a git repository")

    if git_ok(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return CheckResult(False, f"{repo} is not a git working tree")

    remotes = git_ok(repo, "remote")
    if remotes:
        return CheckResult(
            False,
            f"git remotes are present ({remotes.replace(chr(10), ', ')}); never push in this eval",
        )

    roots = root_commits(repo)
    if not roots:
        return CheckResult(
            False, "no root commit; expected git init plus an empty initial commit"
        )
    for root in roots:
        if commit_has_files(repo, root):
            return CheckResult(
                False,
                f"root commit {root[:12]} is not empty; the test must start from an empty initial commit",
            )

    store = expected_store(repo)
    store_resolved = store.resolve() if store.exists() else store
    extra: list[dict[str, str]] = []
    for entry in parse_worktrees(repo):
        path_s = entry.get("worktree")
        if path_s and Path(path_s).resolve() != repo:
            extra.append(entry)

    if not extra:
        return CheckResult(
            False,
            f"no git worktree besides the live checkout; expected one under {store}",
        )

    valid: list[tuple[Path, dict[str, str]]] = []
    problems: list[str] = []
    for entry in extra:
        path = Path(entry["worktree"]).resolve()
        try:
            path.relative_to(repo)
            inside = True
        except ValueError:
            inside = False
        if inside:
            problems.append(
                f"{path} is inside the project repo (must be a sibling .worktrees store)"
            )
            continue
        try:
            path.relative_to(store_resolved)
            under_store = True
        except ValueError:
            under_store = False
        if not under_store:
            problems.append(
                f"{path} is not under {store} "
                f"(need <parent>/.worktrees/{repo.name}/<worktree>)"
            )
            continue
        branch = entry.get("branch", "")
        if not branch or is_default_branch(branch):
            problems.append(
                f"{path} is on {branch or 'detached HEAD'}; worktree must use a feature branch, not master/main"
            )
            continue
        head = entry.get("HEAD") or git_ok(path, "rev-parse", "HEAD")
        if not head:
            problems.append(f"{path} has no HEAD")
            continue
        count_text = git_ok(path, "rev-list", "--count", "HEAD")
        try:
            count = int(count_text)
        except ValueError:
            count = 0
        if count < 2:
            problems.append(
                f"{path} has no commit after the empty initial commit; commit each finished part in the worktree"
            )
            continue
        changed = git_ok(
            path,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            f"{roots[0]}..HEAD",
        )
        if not changed.strip():
            problems.append(f"{path} commits after init do not add files")
            continue
        valid.append((path, entry))

    if valid:
        live_branch = git_ok(repo, "rev-parse", "--abbrev-ref", "HEAD")
        if not is_default_branch(live_branch):
            return CheckResult(
                False,
                f"live checkout is on {live_branch or 'detached HEAD'}; merge into master/main",
            )
        live_head = git_ok(repo, "rev-parse", "HEAD")
        merged: list[Path] = []
        for path, entry in valid:
            wt_head = entry.get("HEAD") or git_ok(path, "rev-parse", "HEAD")
            if live_head and wt_head and is_ancestor(repo, wt_head, live_head):
                merged.append(path)
        if not merged:
            names = ", ".join(str(path) for path, _ in valid)
            return CheckResult(
                False,
                f"worktree(s) exist ({names}) but were not merged into the live checkout",
            )
        names = ", ".join(str(path) for path in merged)
        return CheckResult(
            True,
            f"worktree(s) under {store}: {names}; merged into live checkout; "
            "empty initial commit kept; no remotes/push",
        )
    if problems:
        return CheckResult(False, "; ".join(problems))
    return CheckResult(False, f"no valid worktree under {store}")
