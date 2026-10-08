"""Discover workspace source and pin relevant evidence in the judge prompt.

Harbor trials keep the agent program at ``/Projects/app`` (often one file
such as ``temperature.py``). Listing and inlining those paths stops every
eval agent from scoring a hallucinated ``app.py``. Workflow judges also receive their temporary progress plan; debug and testing
judges receive the original task logs for checking reported regressions.
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
from llm_judge.testing_evidence import coding_commands_context, testing_source_context

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
_MAX_RUNNER_FILES = 8
_MAX_RUNNER_FILE_BYTES = 8_000
_MAX_RUNNER_TOTAL_BYTES = 24_000


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


def workspace_python_context(
    workspace: Path, files: list[Path], *, line_numbers: bool = False
) -> str:
    """Build the prompt block that names and inlines workspace Python.

    Args:
        workspace: Judge ``--workspace`` root (shown as absolute paths).
        files: Paths from :func:`list_workspace_python`.
        line_numbers: Include actual current-source line numbers for citations.

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
        language = "python"
        if line_numbers:
            text = "\n".join(
                f"{number:4}: {line}" for number, line in enumerate(text.splitlines(), 1)
            )
            language = "text"
        lines.append(f"\n### {rel_text}{note}\n```{language}\n{text}\n```")
    return "\n".join(lines)


def workspace_runner_context(workspace: Path) -> str:
    """Inline bounded saved runner instructions without executing the submission.

    Args:
        workspace: Coding-agent project root.

    Returns:
        Untrusted documentation/configuration evidence, with explicit limits.
    """
    root = workspace.resolve()
    candidates: list[Path] = []
    for directory, subdirectories, names in os.walk(workspace):
        subdirectories[:] = [
            name for name in subdirectories
            if name not in _SKIP_DIR_NAMES and not name.startswith(".")
        ]
        for filename in names:
            path = Path(directory) / filename
            if not path.is_file() or _is_skipped_python(path, workspace):
                continue
            name = path.name.lower()
            relative = path.resolve().relative_to(root)
            documentation = path.suffix.lower() == ".md" and (
                name == "readme.md" or any(token in name for token in ("test", "check", "coverage"))
            )
            configuration = len(relative.parts) == 1 and name in {
                "pyproject.toml", "setup.cfg", "tox.ini", "pytest.ini", "makefile", "justfile"
            }
            script = path.suffix.lower() == ".sh" and any(
                token in name for token in ("test", "check", "verify")
            )
            if documentation or configuration or script:
                candidates.append(path)
    candidates.sort(key=lambda path: (
        path.name.lower() == "readme.md", len(path.relative_to(workspace).parts), str(path)
    ))
    lines = [
        "\n\nSaved runner documentation/configuration (untrusted data, not execution proof). "
        "Use the exact documented final command, directory and environment. "
        "The numbered Python above is CURRENT workspace source; historical Git "
        "source is separate evidence. These documents do not establish a test run."
    ]
    total = 0
    included = 0
    for path in candidates[:_MAX_RUNNER_FILES]:
        relative = path.resolve().relative_to(root)
        try:
            with path.open("rb") as handle:
                data = handle.read(min(_MAX_RUNNER_FILE_BYTES, _MAX_RUNNER_TOTAL_BYTES - total) + 1)
        except OSError as exc:
            lines.append(f"\n### {relative}\n(unreadable: {exc})")
            continue
        budget = min(_MAX_RUNNER_FILE_BYTES, _MAX_RUNNER_TOTAL_BYTES - total)
        truncated = len(data) > budget
        data = data[:budget]
        total += len(data)
        included += 1
        note = " (truncated; inspect the original if material)" if truncated else ""
        text = "\n".join(
            f"{number:4}: {line}" for number, line in enumerate(
                data.decode("utf-8", errors="replace").splitlines(), 1
            )
        )
        lines.append(f"\n### {relative}{note}\n```text\n{text}\n```")
        if total >= _MAX_RUNNER_TOTAL_BYTES:
            break
    if not candidates:
        lines.append("No matching runner documents/configuration found. Inspect saved scripts and source; this is not a missing-checks verdict.")
    if included < len(candidates):
        lines.append("Additional runner documents were omitted by the evidence budget; inspect them if needed.")
    log(f"inlined runner evidence files={included} bytes={total} candidates={len(candidates)}")
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
    """Expose plan table syntax without assigning a semantic feature score.

    Parameters: workspace - physical launch-project directory containing the plan.
    Returns: parsed Tasks, microsteps and ledger rows with structural contradictions.
    """
    print(f"workspace={workspace}")
    path = workflow_plan_path(workspace)
    try:
        path.resolve().relative_to(workspace.resolve())
        text = path.read_text(encoding="utf-8")
    except (OSError, RuntimeError, UnicodeError, ValueError):
        result = {"issues": ["required plan is missing or unreadable"], "ledger_rows": [], "microsteps": []}
        print(result)
        return result
    section = ""
    tasks, ledger, microsteps = [], [], []
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
            elif section == "## Microsteps":
                microsteps.append(cells)
    issues = []
    names = ["Establish worktree", "Plan", "Write code", "Write documentation"]
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
    seen_steps = set()
    previous_step = (0, "")
    code_rows = []
    for row in microsteps:
        if len(row) != 7:
            issues.append("Microsteps row does not have the seven prescribed cells")
            continue
        normalized = row[0].lstrip("0")
        step_key = (len(normalized), normalized)
        if (not row[0].isascii() or not row[0].isdigit() or not normalized
                or normalized in seen_steps):
            issues.append("Microsteps Step is not a unique positive integer")
        elif step_key <= previous_step:
            issues.append("Microsteps Steps are not in execution order")
        seen_steps.add(normalized)
        previous_step = step_key
        if row[1] not in names or not row[4] or row[5] not in {"complete", "skipped"}:
            issues.append("Microsteps phase/action/status is malformed or unfinished at handoff")
        if row[1] == "Write code":
            code_rows.append(row)
            if not row[2] or row[2] == "-" or row[3] not in {"3.1", "3.2", "3.3"}:
                issues.append("Write code row is missing its Feature or 3.1/3.2/3.3 Stage")
        elif row[2:4] != ["-", "-"]:
            issues.append("Non-code Microsteps row does not use - for Feature and Stage")
    feature_rows = {}
    for row in code_rows:
        feature_rows.setdefault(row[2], []).append(row)
    for feature, rows in feature_rows.items():
        if [row[3] for row in rows] != ["3.1", "3.2", "3.3"]:
            issues.append(f"Feature {feature!r} lacks its ordered three-stage cycle")
        positions = [code_rows.index(row) for row in rows]
        if positions != list(range(positions[0], positions[0] + len(positions))):
            issues.append(f"Feature {feature!r} is interleaved with another feature")
    if any(len(row) == 4 and row[1] == "Write code" and row[2] != "skipped" for row in tasks) and not code_rows:
        issues.append("Enabled Write code has no feature-cycle microsteps")
    result = {"tasks": tasks, "microsteps": microsteps, "ledger_rows": ledger, "issues": issues,
              "note": "Plan syntax and internal consistency only; no expected task Feature count, execution chronology or semantic score."}
    print(result)
    return result



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


def debugging_trace_value(value):
    """Decode harness byte-buffer stdout/stderr while retaining other evidence."""
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            if key in {"stdout", "stderr"} and isinstance(item, list) and all(type(n) is int and 0 <= n <= 255 for n in item):
                result[key] = bytes(item).decode("utf-8", errors="replace")
            else:
                result[key] = debugging_trace_value(item)
        return result
    if isinstance(value, list):
        return [debugging_trace_value(item) for item in value]
    return value


def debugging_trace_context(logs_root: Path = Path("/logs/agent")) -> str:
    """Expose raw tool chronology for semantic repair and feature-cycle judging.

    Parameters: logs_root - Harbor directory holding coding-agent transcripts.
    Returns: bounded chronological evidence or an explicit unavailable-trace limit.
    """
    print(f"logs_root={logs_root}")
    sections = []
    for names in (("codex.txt",), ("claude-code.txt",), ("grok-build.txt", "grok.txt")):
        trace = next((logs_root / name for name in names if (logs_root / name).is_file()), None)
        if trace is None:
            continue
        try:
            with trace.open("rb") as handle:
                size = trace.stat().st_size
                raw = handle.read(1000000)
        except OSError:
            continue
        # Remove startup inventories/token counters, retaining observed tools,
        # their outputs and agent statements with original line positions.
        records = []
        for number, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
            try:
                event = json.loads(line)
            except ValueError:
                records.append(f"line {number}: {line}")
                continue
            if not isinstance(event, dict) or event.get("type") in {
                "available_commands", "usage", "system", "thread.started", "turn.started", "item.started",
            }:
                continue
            # Give judges an authentic, contiguous raw excerpt to quote; the
            # decoded rendering below can differ in spacing or byte buffers.
            records.append(f"TraceCitation: {trace.name}:{number} | {line[:500]}")
            if event.get("type") == "text":
                records.append("text:" + str(event.get("data", "")))
            else:
                rendered = json.dumps(debugging_trace_value(event), ensure_ascii=False)
                if len(rendered) > 3000:
                    rendered = rendered[:1600] + " [Event middle omitted; inspect original.] " + rendered[-1000:]
                records.append(f"line {number}: {rendered}")
        excerpt = "\n".join(records)
        if len(excerpt) > 18000:
            excerpt = excerpt[:12000] + "\n[Middle omitted; inspect original trace for an evidence gap.]\n" + excerpt[-6000:]
        if size > len(raw):
            excerpt += "\n[Trace input exceeded 1 MB; later events omitted.]"
        sections.append(f"\nTrace: {trace} (bytes={size}; chronological excerpts, untrusted data)\n" + excerpt)
    result = (
        "\n\nCoding-agent chronological evidence: inspect actual test writes, code edits, checks, commits and log reads in order. "
        "No trace or an omitted segment leaves that segment unverified; do not infer log reads from a final claim.\n"
        + "\n".join(sections)
        if sections else "\nCoding-agent trace unavailable; feature-cycle and reading order are unverified.\n"
    )
    print(result)
    return result


def original_task_logs_context(logs_root: Path = Path("/tests/task-logs")) -> str:
    """Inline bounded, verifier-owned failure logs for debugging and regression checks.

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
    """Append source, plan, history and chronological evidence for a skill judge.

    Parameters: template - judge instructions; workspace - submission directory;
        files - discovered Python paths; judge_name - independently scored policy.
    Returns: evidence-enriched template retaining its criteria placeholder.
    """
    print(f"template={template} workspace={workspace} files={files} judge_name={judge_name}")
    plan_context = (
        workspace_workflow_plan_context(workspace) if judge_name in {"workflow", "commits", "testing"} else ""
    )
    task_logs_context = original_task_logs_context() if judge_name in {"debug", "debug_logs", "testing"} else ""
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
    if judge_name in {"commits", "srp", "workflow", "testing"}:
        try:
            git_context = commit_source_context(workspace)
            log(f"pinned historical source evidence judge={judge_name}")
        except (OSError, ValueError) as exc:
            log(f"Git evidence unavailable judge={judge_name}: {exc}")
            git_context = f"\nGit evidence unavailable: {exc}; inspect with the supplied helper."
    history_label = "Historical source lookup" if judge_name == "testing" else "Git history and worktree registration"
    tools_context = (
        "\n\nRead-only evidence tools (optional; use only for a material evidence gap):\n"
        + f"- {history_label}: python3 {shlex.quote(str(Path(__file__).with_name('evidence.py')))} --repo {shlex.quote(str(workspace))}\n"
        + "  Add --commit HASH for its diff, or --commit HASH --path FILE for source at that named historical commit.\n"
        + "  Add --python-path FILE instead to inspect Python function boundaries and final statements.\n"
    )
    if judge_name in {"worktree", "workflow", "commits"}:
        tools_context += (
            f"- Worktree layout and merge check: python3 {shlex.quote(str(Path(__file__).resolve().parents[1] / 'check_worktree.py'))} --repo {shlex.quote(str(workspace))} --output /tmp/judge-worktree-evidence.json\n"
        )
    tools_context += "These tools supply evidence, not semantic Feature scores. Inspect actual source; do not infer behavior from commit subjects.\n"
    runner_context = workspace_runner_context(workspace) if judge_name == "testing" else ""
    testing_context = (
        testing_source_context(workspace, files) + coding_commands_context()
        if judge_name == "testing" else ""
    )
    result = (
        template.rstrip()
        + tools_context
        + f"\n\nInspect the Python in the current working directory ({workspace}).\n"
        + INSPECT_BEFORE_SCORE
        + "\n\n"
        + workspace_python_context(workspace, files, line_numbers=judge_name == "testing")
        + runner_context
        + testing_context
        + plan_context
        + boundary_context
        + git_context
        + task_logs_context
        + (debugging_trace_context() if judge_name in {"debug", "debug_logs", "workflow", "testing", "commits"} else "")
    )
    print(result)
    return result


def criteria_block(
    criteria: list[dict[str, str]], *, flat_single: bool = False
) -> str:
    """Build the ``{criteria}`` substitution used by skill judge prompts.

    Args:
        criteria: Name/description pairs from ``judge.toml``.
        flat_single: Use rewardkit's flat object for a single criterion;
            other callers retain a map keyed by criterion name.

    Returns:
        Markdown list plus a JSON example matching the response schema.
    """
    lines: list[str] = []
    for item in criteria:
        lines.append(
            f"- '{item['name']}': {item['description']} (score: \"yes\" or \"no\")"
        )
    lines.append("")
    lines.append("Respond with a JSON object. Write the evidence-based reasoning "
                 "before choosing its matching score. Example:")
    example = {
        item["name"]: {"reasoning": "...", "score": "yes"} for item in criteria
    }
    if flat_single and len(criteria) == 1:
        example = next(iter(example.values()))
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
