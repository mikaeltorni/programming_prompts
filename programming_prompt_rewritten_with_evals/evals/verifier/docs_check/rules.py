"""Apply the Harbor docs-after-code rules."""

from __future__ import annotations

import re
from pathlib import Path

from worktree_check.rules import CheckResult

README_NAME = "README.md"
ORIGINAL_TASK = Path("/tests/task.md")
ENTRYPOINT_RE = re.compile(r"^def (run_[A-Za-z0-9_]+)\s*\(", re.MULTILINE)


def _workspace_python_files(repo: Path) -> list[Path]:
    """List application Python files, excluding tests and internal stores.

    Parameters: repo - project checkout.

    Returns: sorted Python paths.
    """
    files: list[Path] = []
    for path in sorted(repo.rglob("*.py")):
        relative = path.relative_to(repo)
        if any(part in {".git", "__pycache__", ".worktrees", "tests", "test"} for part in relative.parts):
            continue
        if path.name == "conftest.py" or path.name.startswith("test_") or path.name.endswith("_test.py"):
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


def _required_commands(task_text: str) -> list[str]:
    """Extract named command forms from the original task's inline grammar.

    Parameters: task_text - verifier-owned original request text.
    Returns: sorted unique command names explicitly documented by the task.
    """
    print(f"task_text={task_text}")
    pattern = r"`([a-z][a-z0-9_-]*)(?:\s+<[^`<>]+>)+`|`([a-z][a-z0-9_-]*)`\s*(?:returns\b|→)"
    result = sorted({match.group(1) or match.group(2) for match in re.finditer(pattern, task_text)})
    print(result)
    return result


def check_repo(repo: Path) -> CheckResult:
    """Inspect whether README.md documents the workspace program.

    Parameters: repo - project checkout after merge.

    Returns: pass/fail state and reasoning.
    """
    print(f"repo={repo}")
    repo = repo.resolve()
    readme = repo / README_NAME
    if not readme.is_file():
        result = CheckResult(False, f"missing {readme}; write docs after the code")
        print(result)
        return result
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as exc:
        result = CheckResult(False, f"could not read {readme}: {exc}")
        print(result)
        return result
    if not text.strip():
        result = CheckResult(False, f"{readme} is empty")
        print(result)
        return result
    try:
        task_text = ORIGINAL_TASK.read_text(encoding="utf-8")
    except OSError:
        command_note = "; command coverage unverified: original task unavailable"
    else:
        commands = _required_commands(task_text)
        missing_commands = [name for name in commands if not re.search(r"\b" + re.escape(name) + r"\b", text)]
        if missing_commands:
            result = CheckResult(False, f"{README_NAME} does not document command(s) {missing_commands!r}")
            print(result)
            return result
        command_note = f"; names requested commands {commands!r}"
    entrypoints = public_entrypoints(repo)
    if entrypoints:
        missing = [name for name in entrypoints if name not in text]
        if missing:
            result = CheckResult(
                False,
                f"{README_NAME} does not name the public entrypoint(s) {missing!r}",
            )
            print(result)
            return result
        result = CheckResult(
            True,
            f"{README_NAME} documents entrypoint(s) {entrypoints!r}{command_note}",
        )
        print(result)
        return result
    py_names = [path.name for path in _workspace_python_files(repo)]
    if not py_names:
        result = CheckResult(False, f"{README_NAME} exists but there is no workspace Python to document")
        print(result)
        return result
    missing_files = [name for name in py_names if name not in text]
    if missing_files:
        result = CheckResult(
            False,
            f"{README_NAME} does not name the program file(s) {missing_files!r}",
        )
        print(result)
        return result
    result = CheckResult(True, f"{README_NAME} documents {py_names!r}{command_note}")
    print(result)
    return result
