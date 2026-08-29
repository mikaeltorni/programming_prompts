"""Apply the Harbor docs-after-code rules."""

from __future__ import annotations

import re
from pathlib import Path

from worktree_check.rules import CheckResult

README_NAME = "README.md"
ENTRYPOINT_RE = re.compile(r"^def (run_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)


def _workspace_python_files(repo: Path) -> list[Path]:
    """List workspace Python files, skipping git and worktree stores.

    Parameters: repo - project checkout.

    Returns: sorted Python paths.
    """
    files: list[Path] = []
    for path in sorted(repo.rglob("*.py")):
        if any(part in {".git", "__pycache__", ".worktrees"} for part in path.parts):
            continue
        files.append(path)
    return files


def public_entrypoints(repo: Path) -> list[str]:
    """Collect public ``run_*`` function names from workspace Python.

    Parameters: repo - project checkout.

    Returns: unique entrypoint names in first-seen order.
    """
    names: list[str] = []
    seen: set[str] = set()
    for path in _workspace_python_files(repo):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for match in ENTRYPOINT_RE.finditer(text):
            name = match.group(1)
            if name not in seen:
                seen.add(name)
                names.append(name)
    return names


def check_repo(repo: Path) -> CheckResult:
    """Inspect whether README.md documents the workspace program.

    Parameters: repo - project checkout after merge.

    Returns: pass/fail state and reasoning.
    """
    repo = repo.resolve()
    readme = repo / README_NAME
    if not readme.is_file():
        return CheckResult(False, f"missing {readme}; write docs after the code")
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        return CheckResult(False, f"could not read {readme}: {exc}")
    if not text.strip():
        return CheckResult(False, f"{readme} is empty")
    entrypoints = public_entrypoints(repo)
    if entrypoints:
        missing = [name for name in entrypoints if name not in text]
        if missing:
            return CheckResult(
                False,
                f"{README_NAME} does not name the public entrypoint(s) {missing!r}",
            )
        return CheckResult(
            True,
            f"{README_NAME} documents entrypoint(s) {entrypoints!r}",
        )
    py_names = [path.name for path in _workspace_python_files(repo)]
    if not py_names:
        return CheckResult(False, f"{README_NAME} exists but there is no workspace Python to document")
    missing_files = [name for name in py_names if name not in text]
    if missing_files:
        return CheckResult(
            False,
            f"{README_NAME} does not name the program file(s) {missing_files!r}",
        )
    return CheckResult(True, f"{README_NAME} documents {py_names!r}")
