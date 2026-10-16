"""Collect recorded Python artifacts without executing coding-agent commands."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex

from llm_judge.testing_evidence import MAX_TRACE_INPUT_BYTES
from llm_judge.workspace import (
    _is_skipped_python,
    list_workspace_python,
    source_listing_has_capacity,
)

_ABSOLUTE_PYTHON = re.compile(
    r'''"(?P<double>/[^"\n]+\.py)"|'(?P<single>/[^'\n]+\.py)'|(?P<bare>/[^\s;"'<>|()\\]+\.py)'''
)


def parse_recorded_python_paths(line: str) -> tuple[Path, ...]:
    """Extract literal Python paths from one completed Codex action.

    Parameters: line - original JSON transcript record, never shell input to execute.
    Returns: converted absolute Python paths from commands or file-change metadata.
    """
    print(f"line={line}")
    try:
        event = json.loads(line)
    except ValueError:
        print(())
        return ()
    if not isinstance(event, dict) or event.get("type") != "item.completed":
        print(())
        return ()
    item = event.get("item")
    if not isinstance(item, dict):
        print(())
        return ()
    paths = []
    if item.get("type") == "file_change":
        for change in item.get("changes", []):
            value = change.get("path") if isinstance(change, dict) else None
            if isinstance(value, str) and value.startswith("/") and value.endswith(".py"):
                paths.append(Path(value))
    elif item.get("type") == "command_execution":
        command = item.get("command", "")
        if isinstance(command, str):
            try:
                parts = shlex.split(command)
            except ValueError:
                parts = []
            if len(parts) == 3 and parts[1] in {"-c", "-lc"}:
                command = parts[-1]
            for match in _ABSOLUTE_PYTHON.finditer(command):
                paths.append(Path(next(value for value in match.groups() if value is not None)))
    result = tuple(dict.fromkeys(paths))
    print(result)
    return result


def require_trial_python_file(path: Path, workspace: Path, temporary_root: Path) -> Path:
    """Accept a current Python artifact in the submission or trial scratch space.

    Parameters: path - converted recorded path; workspace - submission root;
        temporary_root - trial temporary directory, excluding native Codex home.
    Returns: the accepted physical Python file path.
    """
    print(f"path={path} workspace={workspace} temporary_root={temporary_root}")
    resolved = path.resolve()
    if _is_skipped_python(resolved, workspace, temporary_root):
        raise ValueError("recorded source is missing or excluded")
    print(resolved)
    return resolved


def list_testing_python(
    workspace: Path,
    logs_root: Path = Path("/logs/agent"),
    temporary_root: Path | None = None,
) -> list[Path]:
    """Include existing recorded scratch checks in the testing source inventory.

    Parameters: workspace - submission root; logs_root - original Codex trace directory;
        temporary_root - explicit scratch root, or Harbor's /tmp namespace,
        independently of a verifier subprocess's TMPDIR setting.
    Returns: workspace and explicitly recorded trial Python files, with bounded discovery.
    """
    print(f"workspace={workspace} logs_root={logs_root} temporary_root={temporary_root}")
    files = list_workspace_python(workspace)
    scratch = temporary_root if temporary_root is not None else Path("/tmp")
    try:
        with (logs_root / "codex.txt").open("rb") as handle:
            data = handle.read(MAX_TRACE_INPUT_BYTES)
    except OSError:
        print(files)
        return files
    for line in data.decode("utf-8", errors="replace").splitlines():
        for path in parse_recorded_python_paths(line):
            try:
                accepted = require_trial_python_file(path, workspace, scratch)
            except (OSError, RuntimeError, ValueError):
                continue
            if accepted not in files and source_listing_has_capacity(files):
                files.append(accepted)
    print(files)
    return files
