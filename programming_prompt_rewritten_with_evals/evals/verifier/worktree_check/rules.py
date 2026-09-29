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
from .naming import check_names


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


def store_entry_problems(store: Path, registered: set[Path]) -> list[str]:
    """Report store contents that are not a registered worktree directory.

    Every direct child of the project store must be one registered worktree.
    Leftover copies, scratch directories, and stray files mean the task did not
    work in the isolated worktree, and a worktree found deeper than one level
    means the layout skipped the required ``<project>_<type>-<feature>`` leaf.

    Parameters: store - project worktree store; registered - resolved paths of
    every worktree git knows about.

    Returns: one message per unexpected store entry.
    """
    if not store.is_dir():
        return []
    problems: list[str] = []
    for child in sorted(store.iterdir()):
        resolved = child.resolve()
        if resolved in registered:
            continue
        nested = sorted(
            path for path in registered if path != resolved and _is_under(path, resolved)
        )
        if nested:
            problems.append(
                f"{nested[0]} is nested below {resolved}; the worktree must sit "
                f"directly in {store} as <project>_<type>-<feature>"
            )
            continue
        kind = "directory" if child.is_dir() else "file"
        problems.append(
            f"{resolved} is an unregistered {kind} in the worktree store; "
            "the store holds registered worktrees only"
        )
    return problems


def _is_under(path: Path, parent: Path) -> bool:
    """Check whether one path lies inside another.

    Parameters: path - candidate descendant; parent - candidate ancestor.

    Returns: true when path is contained in parent.
    """
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def delivery_problems(repo: Path, merged: list[Path]) -> list[str]:
    """Check Python and README delivery in the live and merged checkouts.

    Args:
        repo: Physical live checkout.
        merged: Valid worktrees whose HEAD is reachable from the live HEAD.

    Returns:
        Evidence of uncommitted deliverables or README commits authored outside
        the task worktrees. Temporary plans, caches and ignored logs are not
        deliverables. No task-specific names or Feature counts are used.
    """
    problems = []
    for checkout in [repo, *merged]:
        status = run_git(checkout, "status", "--porcelain=v1", "-z",
                         "--untracked-files=all")
        if status.returncode:
            problems.append(f"cannot inspect delivery status in {checkout}")
            continue
        entries = iter(status.stdout.split("\0"))
        for entry in entries:
            if not entry:
                continue
            code, name = entry[:2], entry[3:]
            if "R" in code or "C" in code:
                next(entries, None)
            path = Path(name)
            if any(part in {"tmp", ".log", "__pycache__", ".venv", "venv"}
                   for part in path.parts):
                continue
            if path.suffix == ".py" or path.name.lower() == "readme.md":
                problems.append(f"uncommitted deliverable in {checkout}: {name}")
    readme = repo / "README.md"
    if readme.is_file():
        commit = git_ok(repo, "log", "--no-merges", "-1", "--format=%H",
                        "HEAD", "--", "README.md")
        authors = set()
        for checkout in merged:
            for event in git_ok(checkout, "reflog", "show", "--format=%H%x09%gs", "HEAD").splitlines():
                sha, separator, action = event.partition("\t")
                if separator and action.startswith("commit"):
                    authors.add(sha)
        if not commit or commit not in authors:
            problems.append("README.md has no introducing/update commit authored in a merged task worktree")
    return problems


def check_repo(repo: Path, env: dict[str, str] | None = None) -> CheckResult:
    """Inspect a checkout against the worktree eval contract.

    Parameters: repo - project checkout initialized with an empty root commit;
    env - deprecated compatibility parameter; project naming is derived from
    the physical checkout basename.

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
    registered: set[Path] = set()
    for entry in parse_worktrees(repo):
        path_s = entry.get("worktree")
        if not path_s:
            continue
        resolved_entry = Path(path_s).resolve()
        registered.add(resolved_entry)
        if resolved_entry != repo:
            extra.append(entry)

    strays = store_entry_problems(store_resolved, registered)

    if not extra:
        return CheckResult(
            False,
            f"no git worktree besides the live checkout; expected one under {store}",
        )

    valid: list[tuple[Path, dict[str, str]]] = []
    problems: list[str] = list(strays)
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
        naming = check_names(path.name, branch, repo.name)
        if naming:
            problems.append(f"{path}: {'; '.join(naming)}")
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
                f"{path} has no commit after the empty initial commit; commit your work in the worktree"
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
        # Registration and ancestry alone also pass an unused worktree created
        # after coding in the live checkout. HEAD reflogs are worktree-local.
        events = git_ok(path, "reflog", "show", "--format=%H%x09%gs", "HEAD")
        authored_here = []
        for event in events.splitlines():
            commit, separator, action = event.partition("\t")
            if separator and action.startswith("commit") and is_ancestor(repo, commit, head):
                authored_here.append(commit)
        if not authored_here:
            problems.append(
                f"{path} has no reachable commit recorded in its own HEAD reflog; "
                "creating an unused worktree after coding is not isolation"
            )
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
        if strays:
            return CheckResult(False, "; ".join(strays))
        delivery = delivery_problems(repo, merged)
        if delivery:
            return CheckResult(False, "; ".join(delivery))
        names = ", ".join(str(path) for path in merged)
        return CheckResult(
            True,
            f"worktree(s) under {store}: {names}; merged into live checkout; "
            "empty initial commit kept; no remotes/push",
        )
    if problems:
        return CheckResult(False, "; ".join(problems))
    return CheckResult(False, f"no valid worktree under {store}")
