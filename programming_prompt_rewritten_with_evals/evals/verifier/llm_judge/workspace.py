"""Discover workspace Python and pin it in the judge prompt.

Harbor trials keep the agent program at ``/Projects/app`` (often one file
such as ``temperature.py``). Listing and inlining those paths stops every
eval agent from scoring a hallucinated ``app.py``.
"""

from __future__ import annotations

import json
import tomllib
from pathlib import Path

from llm_judge.log import log

DEFAULT_WORKSPACE = Path("/Projects/app")
INSPECT_BEFORE_SCORE = (
    "Read every `*.py` file in the working directory before you score. "
    "Use tools to open the files. Do not answer no because you have not "
    "inspected the source yet — inspect first. 'If unsure, answer no' "
    "applies only after you have read the Python."
)
_SKIP_DIR_NAMES = frozenset(
    {
        "__pycache__",
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "site-packages",
        ".worktrees",
        "node_modules",
        ".tox",
        ".mypy_cache",
        ".pytest_cache",
    }
)
_MAX_LISTED_FILES = 40
_MAX_FILE_BYTES = 80_000
_MAX_TOTAL_BYTES = 200_000


def _is_skipped_python(path: Path, workspace: Path) -> bool:
    """Return True when *path* lives under junk/hidden dirs, not solution code.

    Args:
        path: Candidate ``*.py`` file.
        workspace: Judge ``--workspace`` root.

    Returns:
        True to omit the file from the prompt listing.
    """
    try:
        relative = path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return True
    for part in relative.parts:
        if part in _SKIP_DIR_NAMES:
            return True
        if part.startswith(".") and part not in {".", ".."}:
            return True
    return False


def list_workspace_python(workspace: Path) -> list[Path]:
    """Return solution ``*.py`` files under *workspace*, junk dirs omitted.

    Args:
        workspace: Directory the coding agent wrote into.

    Returns:
        Sorted real files, capped at ``_MAX_LISTED_FILES``.
    """
    if not workspace.is_dir():
        log(f"workspace is not a directory: {workspace}")
        return []
    found: list[Path] = []
    for path in sorted(workspace.rglob("*.py")):
        if not path.is_file():
            continue
        if _is_skipped_python(path, workspace):
            continue
        found.append(path.resolve())
        if len(found) >= _MAX_LISTED_FILES:
            log(
                f"python listing capped at {_MAX_LISTED_FILES} files "
                f"under {workspace}"
            )
            break
    log(
        f"listed {len(found)} python file(s) under {workspace}: "
        + ", ".join(p.name for p in found[:12])
        + ("…" if len(found) > 12 else "")
    )
    return found


def listed_python_keys(files: list[Path], workspace: Path) -> set[str]:
    """Lowercased names and paths the judge is allowed to cite.

    Args:
        files: Paths from :func:`list_workspace_python`.
        workspace: Judge ``--workspace`` root.

    Returns:
        Absolute paths, relative paths, and basenames.
    """
    keys: set[str] = set()
    root = workspace.resolve()
    for path in files:
        resolved = path.resolve()
        keys.add(resolved.name.lower())
        keys.add(str(resolved).lower())
        keys.add(resolved.as_posix().lower())
        keys.add(str(workspace / resolved.name).lower())
        keys.add(f"{workspace.as_posix()}/{resolved.name}".lower())
        try:
            relative = resolved.relative_to(root)
            keys.add(relative.as_posix().lower())
            keys.add(str(relative).lower())
        except ValueError:
            pass
    return keys


def workspace_python_context(workspace: Path, files: list[Path]) -> str:
    """Build the prompt block that names and inlines workspace Python.

    Args:
        workspace: Judge ``--workspace`` root (shown as absolute paths).
        files: Paths from :func:`list_workspace_python`.

    Returns:
        Markdown listing every path and (budget permitting) file contents.
    """
    if not files:
        log(f"no python files to inline under {workspace}")
        return (
            f"No `*.py` files were found under {workspace}. "
            "Do not invent paths such as app.py. Score only files that exist."
        )
    lines: list[str] = [
        "Score ONLY these Python files. Do not invent other paths "
        f"(for example {workspace / 'app.py'} is not a file unless listed):",
    ]
    root = workspace.resolve()
    for path in files:
        try:
            relative = path.resolve().relative_to(root)
        except ValueError:
            relative = Path(path.name)
        lines.append(f"- {path.resolve()}  (relative: {relative.as_posix()})")
    lines.append("")
    lines.append(
        "File contents below are the workspace source. Score this text. "
        "Do not substitute a different filename."
    )
    total = 0
    for path in files:
        try:
            relative = path.resolve().relative_to(root)
        except ValueError:
            relative = Path(path.name)
        rel_text = relative.as_posix()
        try:
            data = path.read_bytes()
        except OSError as exc:
            log(f"unreadable python file {rel_text}: {exc}")
            lines.append(f"\n### {rel_text}\n(unreadable: {exc})")
            continue
        truncated = False
        if len(data) > _MAX_FILE_BYTES:
            data = data[:_MAX_FILE_BYTES]
            truncated = True
            log(f"truncated {rel_text} to {_MAX_FILE_BYTES} bytes")
        if total + len(data) > _MAX_TOTAL_BYTES:
            log(f"omitted {rel_text}: inline budget {_MAX_TOTAL_BYTES} bytes")
            lines.append(
                f"\n### {rel_text}\n(omitted: remaining inline budget exhausted)"
            )
            continue
        total += len(data)
        text = data.decode("utf-8", errors="replace")
        note = " (truncated)" if truncated else ""
        lines.append(f"\n### {rel_text}{note}\n```python\n{text}\n```")
    return "\n".join(lines)


def pin_workspace_python(
    template: str, workspace: Path, files: list[Path]
) -> str:
    """Append inspect instructions and inlined sources.

    Leaves a ``{criteria}`` placeholder intact so rewardkit can still
    substitute it. Grok fills criteria first, then calls this.

    Args:
        template: Judge prompt text (may still contain ``{criteria}``).
        workspace: Path shown in the inspect instruction.
        files: Paths from :func:`list_workspace_python`.

    Returns:
        Prompt text with the workspace listing appended.
    """
    return (
        template.rstrip()
        + f"\n\nInspect the Python in the current working directory ({workspace}).\n"
        + INSPECT_BEFORE_SCORE
        + "\n\n"
        + workspace_python_context(workspace, files)
    )


def criteria_block(criteria: list[dict[str, str]]) -> str:
    """Build the ``{criteria}`` substitution used by skill judge prompts.

    Args:
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        Markdown list plus a JSON example matching the response schema.
    """
    lines: list[str] = []
    for item in criteria:
        lines.append(
            f"- '{item['name']}': {item['description']} (score: \"yes\" or \"no\")"
        )
    lines.append("")
    lines.append("Respond with a JSON object. Example:")
    example = {
        item["name"]: {"score": "yes", "reasoning": "..."} for item in criteria
    }
    lines.append(json.dumps(example, indent=2))
    return "\n".join(lines)


def inspect_prompt(
    template: str,
    criteria: list[dict[str, str]],
    workspace: Path,
    python_files: list[Path] | None = None,
) -> str:
    """Fill ``{criteria}`` and pin scoring to real workspace Python files.

    Args:
        template: Judge prompt with a ``{criteria}`` placeholder.
        criteria: Name/description pairs from ``judge.toml``.
        workspace: Path shown in the inspect instruction.
        python_files: Optional precomputed listing; ``None`` walks *workspace*.

    Returns:
        The full prompt passed to a headless agent CLI.
    """
    files = (
        python_files if python_files is not None else list_workspace_python(workspace)
    )
    filled = template.replace("{criteria}", criteria_block(criteria))
    return pin_workspace_python(filled, workspace, files)


def load_judge_dir(judge_dir: Path) -> tuple[str, list[dict[str, str]], int]:
    """Read ``prompt.md`` plus binary criteria from ``judge.toml``.

    Args:
        judge_dir: Directory with ``prompt.md`` (or ``judge-prompt.md``) and
            ``judge.toml``.

    Returns:
        Prompt template, criterion dicts (``name`` / ``description``), timeout.

    Raises:
        FileNotFoundError: When the prompt or toml is missing.
        ValueError: When the template has no ``{criteria}`` placeholder.
    """
    prompt_path = judge_dir / "prompt.md"
    if not prompt_path.is_file():
        prompt_path = judge_dir / "judge-prompt.md"
    toml_path = judge_dir / "judge.toml"
    if not prompt_path.is_file() or not toml_path.is_file():
        raise FileNotFoundError(
            f"LLM judge needs prompt.md and judge.toml in {judge_dir}"
        )
    template = prompt_path.read_text(encoding="utf-8")
    if "{criteria}" not in template:
        raise ValueError(f"{prompt_path} must contain a {{criteria}} placeholder")
    payload = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    timeout = int((payload.get("judge") or {}).get("timeout") or 180)
    criteria: list[dict[str, str]] = []
    for item in payload.get("criterion") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "criterion")
        description = str(item.get("description") or name)
        criteria.append({"name": name, "description": description})
    if not criteria:
        raise ValueError(f"{toml_path} has no [[criterion]] entries")
    return template, criteria, timeout
