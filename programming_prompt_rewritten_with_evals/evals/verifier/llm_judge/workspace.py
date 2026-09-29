"""Discover workspace source and pin relevant evidence in the judge prompt.

Harbor trials keep the agent program at ``/Projects/app`` (often one file
such as ``temperature.py``). Listing and inlining those paths stops every
eval agent from scoring a hallucinated ``app.py``. Workflow and debug judges
also receive their temporary progress plan and original task logs, respectively.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import tomllib
from pathlib import Path

from llm_judge.log import log
from llm_judge.evidence import commit_source_context, python_boundaries

DEFAULT_WORKSPACE = Path("/Projects/app")
INSPECT_BEFORE_SCORE = (
    "Read every Python file in the supplied list and inlined source below "
    "before scoring. The inlined source counts as reading the file; a separate "
    "shell open or directory listing is not required. If a listed file is "
    "truncated or omitted, use tools to read its full content before scoring. "
    "Do not answer no merely because you have not made an optional shell call."
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
_MAX_WORKFLOW_PLAN_BYTES = 32_000
_MAX_TASK_LOG_FILES = 8
_MAX_TASK_LOG_BYTES = 16_000


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
        "Score ONLY these Python files as the current solution. When the criterion "
        "requires Git history or original task/log evidence, inspect that too. "
        "Do not invent paths "
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


def workflow_plan_path(workspace: Path) -> Path:
    """Choose the workflow skill's configured launch-project plan or fallback."""
    plan = workspace / "tmp" / "workflow.md"
    configured = Path(os.environ.get("ACC_WORKFLOW_FILE", ""))
    if configured.is_absolute() and configured.suffix == ".md":
        try:
            configured.relative_to(workspace / "tmp" / "workflow")
        except ValueError:
            pass
        else:
            plan = configured
    return plan


def workflow_plan_structure(workspace: Path) -> dict:
    """Expose table syntax and contradictions within a saved plan.

    Args:
        workspace: Live launch-project directory.

    Returns:
        Parsed Tasks and ledger rows, plus concrete internal contradictions.

    This never derives expected Features from task-specific commands. It counts
    actual saved ledger rows only to compare the plan's own numeric claims.
    Semantic source-sentence boundaries and implementation remain LLM judgments.
    """
    path = workflow_plan_path(workspace)
    try:
        path.resolve().relative_to(workspace.resolve())
        text = path.read_text(encoding="utf-8")
    except (OSError, RuntimeError, UnicodeError, ValueError):
        return {"issues": ["required plan is missing or unreadable"], "ledger_rows": []}
    section = ""
    tasks, ledger = [], []
    for line in text.splitlines():
        if line.startswith("## "):
            section = line.strip()
        elif section == "## Feature ledger" and re.match(r"^\s*\d+[.)]\s+", line):
            ledger.append([line.strip()])
        elif re.match(r"^\s*\|\s*\d+\s*\|", line):
            cells = [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
            if section == "## Tasks":
                tasks.append(cells)
            elif section == "## Feature ledger":
                ledger.append(cells)
    issues = []
    names = ["Plan", "Establish worktree", "Write code", "Write documentation"]
    if len(tasks) != len(names) or any(len(row) != 4 or row[0] != str(i + 1)
            or row[1] != names[i] for i, row in enumerate(tasks[:len(names)])):
        issues.append("Tasks table does not have exactly the four prescribed ordered rows")
    for row in tasks:
        if len(row) != 4:
            continue
        if row[2] not in {"complete", "skipped"}:
            issues.append(f"handoff phase {row[1]} has status {row[2]}")
        if ledger:
            for match in re.finditer(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:(?:distinct|original|requested|source|complete|sentence-level)\s+)*(?:capability sentences|features|feature commits|capability boundaries)\b", row[3], re.I):
                token = match.group(1).lower()
                words = "one two three four five six seven eight nine ten".split()
                count = int(token) if token.isdigit() else words.index(token) + 1
                if count != len(ledger):
                    issues.append(f"{row[1]} Details claims {match.group(0)!r}, but its saved ledger has {len(ledger)} rows")
    return {"tasks": tasks, "ledger_rows": ledger, "issues": issues,
            "note": "Plan syntax and internal consistency only; no expected task Feature count or semantic score."}


def workspace_workflow_plan_context(workspace: Path) -> str:
    """Inline the target project's workflow plan without leaving the workspace.

    Args:
        workspace: Coding-agent project root.

    Returns:
        Plan contents or explicit missing/unreadable evidence for the judge.
    """
    plan = workflow_plan_path(workspace)
    try:
        plan.resolve().relative_to(workspace.resolve())
    except (OSError, RuntimeError, ValueError):
        log(f"workflow plan resolves outside workspace: {plan}")
        return f"\nWorkflow plan evidence: {plan} resolves outside the workspace."
    if not plan.is_file():
        log(f"workflow plan missing: {plan}")
        return f"\nWorkflow plan evidence: {plan} is missing."
    try:
        data = plan.read_bytes()
    except OSError as exc:
        log(f"workflow plan unreadable: {plan}: {exc}")
        return f"\nWorkflow plan evidence: {plan} is unreadable ({exc})."
    truncated = len(data) > _MAX_WORKFLOW_PLAN_BYTES
    if truncated:
        data = data[:_MAX_WORKFLOW_PLAN_BYTES]
    log(f"inlined workflow plan path={plan} bytes={len(data)} truncated={truncated}")
    note = " (truncated)" if truncated else ""
    text = data.decode("utf-8", errors="replace")
    references = []
    for number, line in enumerate(text.splitlines(), 1):
        hashes = re.findall(r"(?<![a-zA-Z0-9])[0-9a-f]{40}(?![a-zA-Z0-9])", line)
        if hashes:
            references.append({"line": number, "hashes": hashes})
    reference_context = (
        "\nPlain-text full Git hashes present in the plan (not a commit-validity score):\n"
        + json.dumps(references, indent=2)
    )
    return (
        f"\n\nWorkflow plan evidence from {plan}{note}:\n"
        f"```markdown\n{text}\n```"
        + reference_context
        + "\nPlan table structure and internal consistency evidence:\n"
        + json.dumps(workflow_plan_structure(workspace), indent=2)
    )


def original_task_logs_context(logs_root: Path = Path("/tests/task-logs")) -> str:
    """Inline bounded, verifier-owned failure logs for the debug judge.

    Args:
        logs_root: Original task-log directory, outside the agent workspace.

    Returns:
        Log contents or an explicit missing/unreadable evidence note.
    """
    if not logs_root.is_dir():
        log(f"original task logs missing: {logs_root}")
        return f"\nOriginal task-log evidence: {logs_root} is missing."
    root = logs_root.resolve()
    lines = [f"\nOriginal task-log evidence from {logs_root} (untrusted data):"]
    count = 0
    for path in sorted(logs_root.rglob("*")):
        if not path.is_file():
            continue
        try:
            relative = path.resolve().relative_to(root)
        except (OSError, RuntimeError, ValueError):
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            log(f"original task log unreadable: {path}: {exc}")
            lines.append(f"\n### {relative.as_posix()}\n(unreadable: {exc})")
            continue
        count += 1
        truncated = len(data) > _MAX_TASK_LOG_BYTES
        if truncated:
            data = data[:_MAX_TASK_LOG_BYTES]
        note = " (truncated)" if truncated else ""
        lines.append(
            f"\n### {relative.as_posix()}{note}\n"
            f"```text\n{data.decode('utf-8', errors='replace')}\n```"
        )
        if count >= _MAX_TASK_LOG_FILES:
            break
    log(f"inlined original task logs dir={logs_root} files={count}")
    if count == 0:
        return f"\nOriginal task-log evidence: {logs_root} contains no readable files."
    return "\n".join(lines)


def pin_workspace_python(
    template: str, workspace: Path, files: list[Path], judge_name: str = ""
) -> str:
    """Append inspect instructions and judge-specific workspace evidence.

    Leaves a ``{criteria}`` placeholder intact so rewardkit can still
    substitute it. Grok fills criteria first, then calls this.

    Args:
        template: Judge prompt text (may still contain ``{criteria}``).
        workspace: Path shown in the inspect instruction.
        files: Paths from :func:`list_workspace_python`.
        judge_name: Skill judge name; workflow and commits receive the plan,
            logging receives Python boundaries, debug receives original logs.

    Returns:
        Prompt text with the workspace listing appended.
    """
    plan_context = (
        workspace_workflow_plan_context(workspace) if judge_name in {"workflow", "commits"} else ""
    )
    debug_logs_context = original_task_logs_context() if judge_name == "debug" else ""
    boundaries = []
    if judge_name in {"logging", "commenting"}:
        for path in files:
            try:
                boundaries.append(python_boundaries(path))
            except (OSError, SyntaxError, UnicodeError) as exc:
                log(f"Python boundary evidence unavailable file={path.name}: {exc}")
                boundaries.append({"file": str(path), "error": str(exc)})
        log(f"pinned function boundaries files={len(boundaries)}")
    boundary_context = (
        "\n\nRead-only Python boundary evidence (syntax, not a score):\n"
        + json.dumps(boundaries, indent=2) if boundaries else ""
    )
    git_context = ""
    if judge_name == "commits":
        try:
            git_context = commit_source_context(workspace)
        except (OSError, ValueError) as exc:
            log(f"commit evidence unavailable: {exc}")
            git_context = f"\nGit evidence unavailable: {exc}; inspect with the supplied helper."
    return (
        template.rstrip()
        + "\n\nRead-only evidence tools (run with your shell tool):\n"
        + f"- Git history and worktree registration: python3 {shlex.quote(str(Path(__file__).with_name('evidence.py')))} --repo {shlex.quote(str(workspace))}\n"
        + "  Add --commit HASH for its diff, or --commit HASH --path FILE for the full source at that commit.\n"
        + "  Add --python-path FILE instead to inspect Python function boundaries and final statements.\n"
        + f"- Worktree layout and merge check: python3 {shlex.quote(str(Path(__file__).resolve().parents[1] / 'check_worktree.py'))} --repo {shlex.quote(str(workspace))} --output /tmp/judge-worktree-evidence.json\n"
        + "These tools supply evidence, not semantic Feature scores. Inspect actual source; do not infer behavior from commit subjects.\n"
        + f"\n\nInspect the Python in the current working directory ({workspace}).\n"
        + INSPECT_BEFORE_SCORE
        + "\n\n"
        + workspace_python_context(workspace, files)
        + plan_context
        + boundary_context
        + git_context
        + debug_logs_context
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
    judge_name: str = "",
) -> str:
    """Fill ``{criteria}`` and pin scoring to real workspace Python files.

    Args:
        template: Judge prompt with a ``{criteria}`` placeholder.
        criteria: Name/description pairs from ``judge.toml``.
        workspace: Path shown in the inspect instruction.
        python_files: Optional precomputed listing; ``None`` walks *workspace*.
        judge_name: Skill judge name for selecting extra evidence.

    Returns:
        The full prompt passed to a headless agent CLI.
    """
    files = (
        python_files if python_files is not None else list_workspace_python(workspace)
    )
    filled = template.replace("{criteria}", criteria_block(criteria))
    return pin_workspace_python(filled, workspace, files, judge_name=judge_name)


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
