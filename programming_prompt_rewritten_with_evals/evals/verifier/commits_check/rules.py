"""Apply the Harbor feature-commit count rules."""

from __future__ import annotations

from pathlib import Path

from worktree_check.git_io import git_ok, root_commits
from worktree_check.rules import CheckResult

SEED_SUBJECT = "Seed task files"
DEFAULT_FEATURE_COUNT_FILE = Path("/tests/feature_count.txt")


def read_required_features(path: Path | None = None) -> int:
    """Read how many Features the coding prompt declared.

    Parameters: path - file with one integer; defaults to /tests/feature_count.txt.

    Returns: required Feature count, at least 1. Missing or unreadable files yield 1.
    """
    target = path if path is not None else DEFAULT_FEATURE_COUNT_FILE
    try:
        text = target.read_text(encoding="utf-8").strip()
    except OSError:
        return 1
    try:
        value = int(text)
    except ValueError:
        return 1
    return value if value >= 1 else 1


def _py_commit_count(repo: Path) -> tuple[int, str]:
    """Count non-merge Python-changing commits after the empty root.

    Parameters: repo - project checkout.

    Returns: count and a short subject list for reasoning. Seed commits are skipped.
    """
    roots = root_commits(repo)
    if not roots:
        return 0, "no root commit"
    log_text = git_ok(
        repo,
        "log",
        "--reverse",
        "--no-merges",
        "--format=%H%x09%s",
        f"{roots[0]}..HEAD",
    )
    counted: list[str] = []
    for line in log_text.splitlines():
        if not line.strip():
            continue
        commit, _, subject = line.partition("\t")
        if subject.strip() == SEED_SUBJECT:
            continue
        names = git_ok(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        )
        if any(name.endswith(".py") for name in names.splitlines() if name.strip()):
            counted.append(subject.strip() or commit[:12])
    return len(counted), ", ".join(counted) if counted else "none"


def check_repo(repo: Path, required: int | None = None) -> CheckResult:
    """Inspect git history for one Python commit per declared Feature.

    Parameters: repo - project checkout; required - Feature count override.

    Returns: pass/fail state and reasoning.
    """
    repo = repo.resolve()
    if git_ok(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return CheckResult(False, f"{repo} is not a git working tree")
    need = required if required is not None else read_required_features()
    count, subjects = _py_commit_count(repo)
    if count < need:
        return CheckResult(
            False,
            f"need at least {need} Python Feature commit(s) after init "
            f"(excluding seed); found {count} ({subjects})",
        )
    return CheckResult(
        True,
        f"{count} Python Feature commit(s) after init (required {need}): {subjects}",
    )
