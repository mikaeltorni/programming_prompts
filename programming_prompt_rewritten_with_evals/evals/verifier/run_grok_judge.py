#!/usr/bin/env python3
"""Grok CLI agent-as-judge for Harbor LLM skills.

Rewardkit 0.1.7 only registers ``codex`` and ``claude-code`` as agent judges.
This helper shells out to the pinned ``grok`` CLI with ``--json-schema`` so
``evalAgent=grok`` uses the same harness as the coding agent, then writes
rewardkit-shaped JSON next to ``--output``. ``--json-schema`` implies
``--output-format json``; scores live in ``structured_output``. The CLI is
given ``--max-turns`` so it can read workspace files before filling the
schema (a single-turn JSON dump was scoring no as "not yet inspected").

``--self-test`` covers prompt/schema/parse fixtures only — it never launches
Grok or a Harbor trial.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
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


def _log(message: str) -> None:
    """Write a verifier diagnostic to stderr (stdout stays JSON/CLI)."""
    print(f"run_grok_judge: {message}", file=sys.stderr, flush=True)


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


def inspect_prompt(template: str, criteria: list[dict[str, str]], workspace: Path) -> str:
    """Fill ``{criteria}`` and require a file-read before scoring.

    Args:
        template: Judge prompt with a ``{criteria}`` placeholder.
        criteria: Name/description pairs from ``judge.toml``.
        workspace: Path shown in the inspect instruction.

    Returns:
        The full prompt passed to ``grok --single``.
    """
    return (
        template.replace("{criteria}", criteria_block(criteria))
        + f"\n\nInspect the Python in the current working directory ({workspace}).\n"
        + _INSPECT_BEFORE_SCORE
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
    )
    check(
        "inspect_before_score",
        "Read every `*.py` file" in filled and "inspect first" in filled,
        "prompt forbids no-as-not-inspected",
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
    prompt = inspect_prompt(template, criteria, args.workspace)
    schema = response_schema(criteria)
    raw = run_grok(
        prompt=prompt,
        schema=schema,
        workspace=args.workspace,
        model=args.model,
        effort=args.reasoning_effort,
        timeout=timeout,
        max_turns=args.max_turns,
    )
    rows = parse_scores(raw, criteria)
    write_reward(args.output, rows, raw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
