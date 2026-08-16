#!/usr/bin/env python3
"""Grok CLI agent-as-judge for Harbor LLM skills.

Rewardkit 0.1.7 only registers ``codex`` and ``claude-code`` as agent judges.
This helper shells out to the pinned ``grok`` CLI with ``--json-schema`` so
``evalAgent=grok`` uses the same harness as the coding agent, then writes
rewardkit-shaped JSON next to ``--output``. ``--json-schema`` implies
``--output-format json``; scores live in ``structured_output``. The CLI is
given ``--max-turns`` so it can read workspace files before filling the
schema (a single-turn JSON dump was scoring no as "not yet inspected").
The prompt also lists and inlines the real ``*.py`` files under
``--workspace`` so the model cannot invent paths such as ``app.py``.
A failing score that admits non-inspection or cites a ``.py`` path
outside that listing is retried once.

``--self-test`` covers prompt/schema/parse fixtures only — it never launches
Grok or a Harbor trial.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path
from typing import Any


DEFAULT_WORKSPACE = Path("/Projects/app")
DEFAULT_MAX_TURNS = 16
_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)
_INSPECT_BEFORE_SCORE = (
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
MIN_RETRY_SECONDS = 40
_NOT_INSPECTED = re.compile(
    r"not inspected|withheld until|have not yet(?:\s+\w+){0,8}\s+inspect"
    r"|have not inspected|until the workspace python is inspected"
    r"|scoring is withheld|have not yet verified"
    r"|without (?:an? )?actual file",
    re.IGNORECASE,
)
_PY_MENTION = re.compile(
    r"(?:(?:\.{0,2}/)?[\w.-]+(?:/[\w.-]+)*)\.py",
    re.IGNORECASE,
)


def _log(message: str) -> None:
    """Write a verifier diagnostic to stderr (stdout stays JSON/CLI)."""
    print(f"run_grok_judge: {message}", file=sys.stderr, flush=True)


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

    Harbor trials keep the agent program at ``/Projects/app`` (often one
    file such as ``temperature.py``). Listing those paths in the prompt
    stops the judge from scoring a hallucinated ``app.py``.

    Args:
        workspace: Directory passed as ``--cwd`` to the Grok CLI.

    Returns:
        Sorted real files, capped at ``_MAX_LISTED_FILES``.
    """
    if not workspace.is_dir():
        _log(f"workspace is not a directory: {workspace}")
        return []
    found: list[Path] = []
    for path in sorted(workspace.rglob("*.py")):
        if not path.is_file():
            continue
        if _is_skipped_python(path, workspace):
            continue
        found.append(path.resolve())
        if len(found) >= _MAX_LISTED_FILES:
            _log(
                f"python listing capped at {_MAX_LISTED_FILES} files "
                f"under {workspace}"
            )
            break
    _log(
        f"listed {len(found)} python file(s) under {workspace}: "
        + ", ".join(p.name for p in found[:12])
        + ("…" if len(found) > 12 else "")
    )
    return found


def workspace_python_context(workspace: Path, files: list[Path]) -> str:
    """Build the prompt block that names and inlines workspace Python.

    Args:
        workspace: Judge ``--workspace`` root (shown as absolute paths).
        files: Paths from :func:`list_workspace_python`.

    Returns:
        Markdown listing every path and (budget permitting) file contents.
    """
    if not files:
        _log(f"no python files to inline under {workspace}")
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
            relative = path.name
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
            _log(f"unreadable python file {rel_text}: {exc}")
            lines.append(f"\n### {rel_text}\n(unreadable: {exc})")
            continue
        truncated = False
        if len(data) > _MAX_FILE_BYTES:
            data = data[:_MAX_FILE_BYTES]
            truncated = True
            _log(f"truncated {rel_text} to {_MAX_FILE_BYTES} bytes")
        if total + len(data) > _MAX_TOTAL_BYTES:
            _log(f"omitted {rel_text}: inline budget {_MAX_TOTAL_BYTES} bytes")
            lines.append(
                f"\n### {rel_text}\n(omitted: remaining inline budget exhausted)"
            )
            continue
        total += len(data)
        text = data.decode("utf-8", errors="replace")
        note = " (truncated)" if truncated else ""
        lines.append(f"\n### {rel_text}{note}\n```python\n{text}\n```")
    return "\n".join(lines)


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


def mentioned_python_paths(reasoning: str) -> list[str]:
    """Return ``.py`` paths cited in judge reasoning.

    Args:
        reasoning: Free-text ``reasoning`` field from Grok.

    Returns:
        Path-like strings in mention order (trailing punctuation stripped).
    """
    found: list[str] = []
    for match in _PY_MENTION.findall(reasoning):
        cleaned = match.rstrip(")'\".,;:")
        if cleaned:
            found.append(cleaned)
    return found


def _path_is_listed(mentioned: str, keys: set[str]) -> bool:
    """Return True when *mentioned* matches a listed workspace Python file."""
    text = mentioned.strip().lower()
    if text in keys:
        return True
    return Path(text).name.lower() in keys


def unreliable_score_reason(
    rows: list[dict[str, Any]], listed_keys: set[str]
) -> str | None:
    """Return why a failing score looks untrustworthy, or None.

    Triggers on skip-inspect wording or ``.py`` citations that are not in
    the workspace listing. Passing criteria are ignored.

    Args:
        rows: Parsed criterion scores from :func:`parse_scores`.
        listed_keys: Lowercased names from :func:`listed_python_keys`.

    Returns:
        ``not_inspected:<criterion>`` or ``wrong_path:<criterion>:<file>``.
    """
    for row in rows:
        if float(row["reward"]) >= 1.0:
            continue
        reasoning = str(row.get("reasoning") or "")
        name = str(row["name"])
        if _NOT_INSPECTED.search(reasoning):
            return f"not_inspected:{name}"
        mentioned = mentioned_python_paths(reasoning)
        if not mentioned:
            continue
        if any(_path_is_listed(item, listed_keys) for item in mentioned):
            continue
        return f"wrong_path:{name}:{Path(mentioned[0]).name}"
    return None


def retry_prompt(prompt: str, reason: str) -> str:
    """Append a one-shot correction after an unusable first score.

    Args:
        prompt: Original judge prompt (criteria and files already filled).
        reason: Short token from :func:`unreliable_score_reason` (no secrets).

    Returns:
        Prompt for the retry ``grok --single`` call.
    """
    return (
        prompt
        + "\n\nRETRY: the previous JSON score was unusable "
        + f"({reason}). Score ONLY the Python files listed above. "
        + "Do not invent app.py. Do not answer no because you have not "
        + "inspected — the source is in this prompt.\n"
    )


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
        raise FileNotFoundError(f"Grok judge needs prompt.md and judge.toml in {judge_dir}")
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


def _score_entry_schema() -> dict[str, Any]:
    """JSON Schema for one yes/no criterion object."""
    return {
        "type": "object",
        "properties": {
            "score": {"type": "string", "enum": ["yes", "no"]},
            "reasoning": {"type": "string"},
        },
        "required": ["score", "reasoning"],
        "additionalProperties": False,
    }


def response_schema(criteria: list[dict[str, str]]) -> dict[str, Any]:
    """Return the JSON Schema passed to ``grok --json-schema``.

    Always keyed by criterion name (including a single criterion). Grok's
    constrained decode drops unknown keys; a flat ``{score, reasoning}``
    schema therefore yielded ``structured_output: {}`` when the model used
    the criterion name, and ``parse_scores`` saw ``None``.

    Args:
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        An object schema whose properties are the criterion names.
    """
    props = {item["name"]: _score_entry_schema() for item in criteria}
    return {
        "type": "object",
        "properties": props,
        "required": list(props.keys()),
        "additionalProperties": False,
    }


def _as_object(value: Any) -> dict[str, Any] | None:
    """Return *value* as a dict, parsing a JSON object string when needed."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            fence = _JSON_FENCE.search(stripped)
            if not fence:
                return None
            try:
                parsed = json.loads(fence.group(1))
            except json.JSONDecodeError:
                return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _unwrap_grok_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Peel Grok ``--output-format json`` envelopes down to score JSON.

    ``--json-schema`` implies that format. The CLI writes
    ``{"type": "result", "structured_output": {...}, "result": "..."}``.
    """
    for key in ("structured_output", "structuredOutput"):
        inner = _as_object(payload.get(key))
        if inner:
            return inner
    inner = _as_object(payload.get("result"))
    if inner:
        return inner
    return payload


def _json_objects_from_text(text: str) -> list[dict[str, Any]]:
    """Collect JSON objects from a blob, JSONL stream, or fenced block."""
    stripped = text.strip()
    found: list[dict[str, Any]] = []
    fence = _JSON_FENCE.search(stripped)
    if fence:
        obj = _as_object(fence.group(1))
        if obj is not None:
            found.append(obj)
    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            found.append(payload)
        return found
    except json.JSONDecodeError:
        pass
    for line in stripped.splitlines():
        obj = _as_object(line.strip())
        if obj is not None:
            found.append(obj)
    if found:
        return found
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        obj = _as_object(match.group(0))
        if obj is not None:
            found.append(obj)
    return found


def _extract_json_object(text: str) -> dict[str, Any]:
    """Parse score JSON from Grok stdout (fence, JSONL, envelope, or raw)."""
    objects = _json_objects_from_text(text)
    if not objects:
        raise ValueError(f"Grok judge returned no JSON: {text.strip()[:200]}")
    chosen = objects[-1]
    for candidate in reversed(objects):
        if candidate.get("structured_output") or candidate.get("type") == "result":
            chosen = candidate
            break
    unwrapped = _unwrap_grok_payload(chosen)
    if unwrapped is chosen and chosen.get("type") == "result":
        _log(
            "grok envelope has no structured_output "
            f"subtype={chosen.get('subtype')!r} is_error={chosen.get('is_error')!r} "
            f"keys={sorted(chosen)}"
        )
    return unwrapped


def _criterion_entry(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Return the score object for *name*, including a flat yes/no payload."""
    entry = data.get(name)
    if isinstance(entry, dict) and "score" in entry:
        return entry
    if isinstance(entry, str):
        return {"score": entry, "reasoning": str(data.get("reasoning") or "")}
    if "score" in data and not isinstance(data.get("score"), dict):
        return {
            "score": data["score"],
            "reasoning": str(data.get("reasoning") or ""),
        }
    return None


def parse_scores(
    text: str, criteria: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Turn Grok JSON into per-criterion reward rows.

    Accepts the Grok CLI result envelope, a flat ``{score, reasoning}``
    object, or ``{<criterion>: {score, reasoning}}``.

    Args:
        text: Raw CLI stdout.
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        Dicts with ``name``, ``raw``, ``reward``, ``reasoning``.
    """
    data = _extract_json_object(text)
    if (
        len(criteria) == 1
        and "score" in data
        and not isinstance(data["score"], dict)
        and criteria[0]["name"] not in data
    ):
        data = {criteria[0]["name"]: data}
    rows: list[dict[str, Any]] = []
    for item in criteria:
        name = item["name"]
        entry = _criterion_entry(data, name)
        if entry is None:
            _log(
                f"parse failed for {name!r}; payload keys={sorted(data)} "
                f"stdout_prefix={text.strip()[:240]!r}"
            )
            raise ValueError(
                f"Grok criterion {name!r} missing score object; "
                f"got {data.get(name)!r} keys={sorted(data)}"
            )
        raw = entry["score"]
        raw_text = str(raw).strip().lower()
        reward = 1.0 if raw_text in {"yes", "true", "1"} else 0.0
        rows.append(
            {
                "name": name,
                "raw": raw,
                "reward": reward,
                "reasoning": str(entry.get("reasoning") or ""),
                "description": item["description"],
            }
        )
    return rows


def write_reward(
    output: Path, rows: list[dict[str, Any]], raw_output: str
) -> None:
    """Write ``reward-*.json`` plus sibling details JSON.

    Args:
        output: Path for the numeric reward file.
        rows: Per-criterion scores from :func:`parse_scores`.
        raw_output: Unparsed Grok stdout kept for audits.
    """
    overall = 1.0 if rows and all(float(row["reward"]) >= 1.0 for row in rows) else 0.0
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps({"reward": overall}, indent=2) + "\n", encoding="utf-8"
    )
    details = {
        "reward": {
            "score": overall,
            "aggregation": "all_pass",
            "kind": "agent",
            "agent": "grok",
            "criteria": [
                {
                    "name": row["name"],
                    "value": row["reward"],
                    "raw": row["raw"],
                    "weight": 1.0,
                    "description": row["description"],
                    "reasoning": row["reasoning"],
                }
                for row in rows
            ],
            "judge_output": raw_output[:8000],
        }
    }
    details_path = output.parent / "reward-details.json"
    name = output.name
    if name.startswith("reward-") and name.endswith(".json") and name != "reward.json":
        inner = name[len("reward-") : -len(".json")]
        if inner:
            details_path = output.parent / f"reward-{inner}-details.json"
    payload = json.dumps(details, indent=2) + "\n"
    details_path.write_text(payload, encoding="utf-8")
    sibling = output.parent / "reward-details.json"
    if sibling != details_path:
        sibling.write_text(payload, encoding="utf-8")
    _log(f"wrote reward={overall} to {output}")


def build_grok_command(
    *,
    prompt: str,
    schema: dict[str, Any],
    workspace: Path,
    model: str,
    effort: str,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> list[str]:
    """Return the Grok CLI argv for a headless judge call.

    ``--single`` is one user prompt, not one model turn. ``--max-turns``
    lets the agent read workspace files before emitting ``structured_output``.

    Args:
        prompt: Full judge prompt (criteria already substituted).
        schema: JSON Schema for ``--json-schema``.
        workspace: Working directory the CLI may inspect.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        max_turns: Agent tool/model rounds before the CLI must stop.

    Returns:
        Argument list for ``subprocess.run`` (first item is ``grok``).
    """
    return [
        "grok",
        "--single",
        prompt,
        "--json-schema",
        json.dumps(schema),
        "--model",
        model,
        "--reasoning-effort",
        effort,
        "--cwd",
        str(workspace),
        "--max-turns",
        str(max_turns),
        "--always-approve",
        "--permission-mode",
        "bypassPermissions",
        "--disable-web-search",
    ]


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
        The full prompt passed to ``grok --single``.
    """
    files = (
        python_files if python_files is not None else list_workspace_python(workspace)
    )
    return (
        template.replace("{criteria}", criteria_block(criteria))
        + f"\n\nInspect the Python in the current working directory ({workspace}).\n"
        + _INSPECT_BEFORE_SCORE
        + "\n\n"
        + workspace_python_context(workspace, files)
    )


def run_grok(
    *,
    prompt: str,
    schema: dict[str, Any],
    workspace: Path,
    model: str,
    effort: str,
    timeout: int,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> str:
    """Invoke the Grok CLI as a headless structured-output judge.

    Args:
        prompt: Full judge prompt (criteria already substituted).
        schema: JSON Schema for ``--json-schema``.
        workspace: Working directory the CLI may inspect.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Subprocess timeout in seconds.
        max_turns: Agent rounds; see :func:`build_grok_command`.

    Returns:
        Decoded stdout.

    Raises:
        FileNotFoundError: When ``grok`` is not on PATH.
        subprocess.CalledProcessError: When the CLI exits non-zero.
        subprocess.TimeoutExpired: When the CLI exceeds *timeout*.
    """
    cmd = build_grok_command(
        prompt=prompt,
        schema=schema,
        workspace=workspace,
        model=model,
        effort=effort,
        max_turns=max_turns,
    )
    _log(
        f"starting grok judge model={model} effort={effort} "
        f"max_turns={max_turns} workspace={workspace} timeout={timeout}s"
    )
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[:500]
        _log(f"grok judge failed rc={proc.returncode}: {err}")
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )
    return proc.stdout or ""


def run_grok_until_reliable(
    *,
    prompt: str,
    schema: dict[str, Any],
    workspace: Path,
    model: str,
    effort: str,
    timeout: int,
    max_turns: int,
    criteria: list[dict[str, str]],
    listed_keys: set[str],
    invoke: Any | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Run the Grok judge, retrying once on skip-inspect or invented paths.

    Args:
        prompt: Full judge prompt (criteria and files already filled).
        schema: JSON Schema for ``--json-schema``.
        workspace: Working directory the CLI may inspect.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Wall budget in seconds for both attempts combined.
        max_turns: Agent rounds per attempt.
        criteria: Name/description pairs from ``judge.toml``.
        listed_keys: Allowed ``.py`` citations from :func:`listed_python_keys`.
        invoke: Optional runner (``--self-test`` injects a fake; default
            :func:`run_grok`). Must accept the same keyword args as
            :func:`run_grok` and return stdout text.

    Returns:
        Raw stdout and parsed rows from the last attempt used.
    """
    runner = invoke or run_grok
    started = time.monotonic()
    raw = runner(
        prompt=prompt,
        schema=schema,
        workspace=workspace,
        model=model,
        effort=effort,
        timeout=timeout,
        max_turns=max_turns,
    )
    rows = parse_scores(raw, criteria)
    reason = unreliable_score_reason(rows, listed_keys)
    if reason is None:
        return raw, rows
    remaining = timeout - (time.monotonic() - started) - 5
    if remaining < MIN_RETRY_SECONDS:
        _log(
            f"skip retry reason={reason} remaining_s={remaining:.0f} "
            f"min_s={MIN_RETRY_SECONDS}"
        )
        return raw, rows
    _log(f"retrying grok judge once reason={reason} remaining_s={remaining:.0f}")
    raw_retry = runner(
        prompt=retry_prompt(prompt, reason),
        schema=schema,
        workspace=workspace,
        model=model,
        effort=effort,
        timeout=int(remaining),
        max_turns=max_turns,
    )
    rows_retry = parse_scores(raw_retry, criteria)
    second = unreliable_score_reason(rows_retry, listed_keys)
    if second:
        _log(f"retry still unreliable reason={second}")
    else:
        _log("retry produced a usable score")
    return raw_retry, rows_retry


def _self_test() -> int:
    """Parse/schema fixtures only — does not launch Grok."""
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)

    criteria = [{"name": "single_responsibility", "description": "SRP helpers"}]
    schema = response_schema(criteria)
    check(
        "single_schema",
        schema.get("required") == ["single_responsibility"],
        "named yes/no schema even for one criterion",
    )
    block = criteria_block(criteria)
    check("criteria_token", '"yes" or "no"' in block, "prompt lists yes/no scores")
    rows = parse_scores(
        '{"score": "yes", "reasoning": "parse helper plus core"}',
        criteria,
    )
    check(
        "parse_yes",
        rows[0]["reward"] == 1.0 and rows[0]["raw"] == "yes",
        "flat yes maps to reward 1.0",
    )
    rows_no = parse_scores(
        "```json\n{\"score\": \"no\", \"reasoning\": \"monolith\"}\n```",
        criteria,
    )
    check("parse_fence_no", rows_no[0]["reward"] == 0.0, "fenced no maps to 0.0")
    envelope = {
        "type": "result",
        "subtype": "success",
        "is_error": False,
        "result": "Here's a summary...",
        "structured_output": {
            "function_commenting": {
                "score": "yes",
                "reasoning": "Parameters and Returns present",
            }
        },
    }
    commenting = [{"name": "function_commenting", "description": "docs"}]
    env_rows = parse_scores(json.dumps(envelope), commenting)
    check(
        "parse_grok_envelope",
        env_rows[0]["reward"] == 1.0,
        "unwrap structured_output from --output-format json",
    )
    named = parse_scores(
        '{"function_commenting": {"score": "no", "reasoning": "Args:"}}',
        commenting,
    )
    check("parse_named_key", named[0]["reward"] == 0.0, "criterion-name key")
    multi = [
        {"name": "srp", "description": "SRP"},
        {"name": "commenting", "description": "docs"},
    ]
    multi_schema = response_schema(multi)
    check(
        "multi_schema",
        "srp" in multi_schema.get("properties", {}),
        "named properties for two criteria",
    )
    cmd = build_grok_command(
        prompt="score this",
        schema=schema,
        workspace=Path("/Projects/app"),
        model="grok-4.6",
        effort="low",
    )
    check(
        "cmd_max_turns",
        "--max-turns" in cmd and str(DEFAULT_MAX_TURNS) in cmd,
        "judge CLI allows tool rounds before JSON",
    )
    check(
        "cmd_bypass_permissions",
        cmd[cmd.index("--permission-mode") + 1] == "bypassPermissions",
        "judge does not stop to ask before reading files",
    )
    filled = inspect_prompt(
        "Score it.\n{criteria}\n",
        criteria,
        Path("/Projects/app"),
        python_files=[],
    )
    check(
        "inspect_before_score",
        "Read every `*.py` file" in filled and "inspect first" in filled,
        "prompt forbids no-as-not-inspected",
    )
    with tempfile.TemporaryDirectory(prefix="grok-judge-") as raw:
        root = Path(raw)
        (root / "temperature.py").write_text(
            "def convert():\n    return 0\n", encoding="utf-8"
        )
        cache = root / "__pycache__"
        cache.mkdir()
        (cache / "ignored.py").write_text("# junk\n", encoding="utf-8")
        venv_pkg = root / ".venv" / "lib"
        venv_pkg.mkdir(parents=True)
        (venv_pkg / "site.py").write_text("# venv\n", encoding="utf-8")
        listed = list_workspace_python(root)
        check(
            "list_skips_junk",
            [p.name for p in listed] == ["temperature.py"],
            "listing keeps solution py and drops pycache/venv",
        )
        context = workspace_python_context(root, listed)
        check(
            "context_inlines_source",
            "def convert():" in context and "Score ONLY these Python files" in context,
            "prompt names and inlines the real file",
        )
        check(
            "context_forbids_app_py",
            "Do not invent other paths" in context and "ignored.py" not in context,
            "prompt forbids invented paths and omits junk files",
        )
        pinned = inspect_prompt("Score it.\n{criteria}\n", criteria, root)
        check(
            "inspect_lists_temperature",
            "temperature.py" in pinned and "def convert():" in pinned,
            "full prompt includes the workspace path and source",
        )
        listed_keys = listed_python_keys(listed, root)
        withheld = [
            {
                "name": "single_responsibility",
                "reward": 0.0,
                "reasoning": (
                    "Scoring is withheld until the workspace Python is inspected."
                ),
            }
        ]
        check(
            "retry_not_inspected",
            unreliable_score_reason(withheld, listed_keys)
            == "not_inspected:single_responsibility",
            "skip-inspect no is flagged for retry",
        )
        invented = [
            {
                "name": "function_commenting",
                "reward": 0.0,
                "reasoning": (
                    "Checked /Projects/app/app.py; Parameters: and Returns: missing."
                ),
            }
        ]
        invented_reason = unreliable_score_reason(invented, listed_keys)
        check(
            "retry_wrong_path",
            invented_reason == "wrong_path:function_commenting:app.py",
            "hallucinated app.py is flagged for retry",
        )
        legitimate = [
            {
                "name": "function_commenting",
                "reward": 0.0,
                "reasoning": "temperature.py uses Args: instead of Parameters:",
            }
        ]
        check(
            "retry_skips_real_file_no",
            unreliable_score_reason(legitimate, listed_keys) is None,
            "a no that cites the real file is not retried",
        )
        passing = [
            {
                "name": "single_responsibility",
                "reward": 1.0,
                "reasoning": "Scoring is withheld until inspected",
            }
        ]
        check(
            "retry_ignores_passing",
            unreliable_score_reason(passing, listed_keys) is None,
            "yes scores are not retried even with skip-inspect wording",
        )
        calls: list[str] = []

        def fake_retry(**kwargs: Any) -> str:
            calls.append(str(kwargs["prompt"]))
            if len(calls) == 1:
                return json.dumps(
                    {
                        "single_responsibility": {
                            "score": "no",
                            "reasoning": (
                                "Scoring is withheld until the workspace "
                                "Python is inspected."
                            ),
                        }
                    }
                )
            return json.dumps(
                {
                    "single_responsibility": {
                        "score": "yes",
                        "reasoning": "temperature.py splits parse and core",
                    }
                }
            )

        retried_raw, retried_rows = run_grok_until_reliable(
            prompt="score it",
            schema=schema,
            workspace=root,
            model="grok-4.6",
            effort="low",
            timeout=180,
            max_turns=16,
            criteria=criteria,
            listed_keys=listed_keys,
            invoke=fake_retry,
        )
        check(
            "retry_loop_second_call",
            len(calls) == 2
            and "RETRY" in calls[1]
            and retried_rows[0]["reward"] == 1.0
            and "yes" in retried_raw,
            "one retry replaces skip-inspect no with a usable yes",
        )
        skip_calls: list[str] = []

        def fake_too_slow(**kwargs: Any) -> str:
            skip_calls.append("called")
            time.sleep(0.05)
            return json.dumps(
                {
                    "single_responsibility": {
                        "score": "no",
                        "reasoning": (
                            "Scoring is withheld until the workspace "
                            "Python is inspected."
                        ),
                    }
                }
            )

        skipped_raw, skipped_rows = run_grok_until_reliable(
            prompt="score it",
            schema=schema,
            workspace=root,
            model="grok-4.6",
            effort="low",
            timeout=1,
            max_turns=16,
            criteria=criteria,
            listed_keys=listed_keys,
            invoke=fake_too_slow,
        )
        check(
            "retry_skipped_when_budget_low",
            len(skip_calls) == 1
            and skipped_rows[0]["reward"] == 0.0
            and "withheld" in skipped_raw,
            "no second grok call when remaining timeout is under the floor",
        )
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} grok-judge self-test(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} grok-judge self-tests passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--self-test`` or run Grok against a judge directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--judge-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--model", default="grok-4.6")
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--timeout", type=int, default=0)
    parser.add_argument(
        "--max-turns",
        type=int,
        default=DEFAULT_MAX_TURNS,
        help="Grok agent rounds for reading files before structured output",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.judge_dir is None or args.output is None:
        parser.error("--judge-dir and --output are required unless --self-test")
    template, criteria, toml_timeout = load_judge_dir(args.judge_dir)
    timeout = args.timeout or toml_timeout
    files = list_workspace_python(args.workspace)
    prompt = inspect_prompt(
        template, criteria, args.workspace, python_files=files
    )
    schema = response_schema(criteria)
    raw, rows = run_grok_until_reliable(
        prompt=prompt,
        schema=schema,
        workspace=args.workspace,
        model=args.model,
        effort=args.reasoning_effort,
        timeout=timeout,
        max_turns=args.max_turns,
        criteria=criteria,
        listed_keys=listed_python_keys(files, args.workspace),
    )
    write_reward(args.output, rows, raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
