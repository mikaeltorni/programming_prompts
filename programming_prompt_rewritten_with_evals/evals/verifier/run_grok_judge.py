#!/usr/bin/env python3
"""Grok CLI agent-as-judge for Harbor LLM skills.

Rewardkit 0.1.7 only registers ``codex`` and ``claude-code`` as agent judges.
This helper shells out to the pinned ``grok`` CLI. Shared workspace listing,
reliability retry, and score parsing live in the ``llm_judge`` package so
Codex and Claude Code can use the same pin-and-retry path.

``--self-test`` covers prompt/schema/parse fixtures only — it never launches
Grok or a Harbor trial.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from llm_judge.log import log
from llm_judge.reliability import retry_prompt, run_until_reliable, unreliable_score_reason
from llm_judge.scores import parse_scores, response_schema, write_reward
from llm_judge.workspace import (
    DEFAULT_WORKSPACE,
    criteria_block,
    inspect_prompt,
    list_workspace_python,
    listed_python_keys,
    load_judge_dir,
    workspace_python_context,
)

DEFAULT_MAX_TURNS = 16


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
    log(
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
        log(f"grok judge failed rc={proc.returncode}: {err}")
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

    def attempt(reason: str | None, timeout_s: int) -> tuple[str, list[dict[str, Any]]]:
        text = prompt if reason is None else retry_prompt(prompt, reason)
        raw = runner(
            prompt=text,
            schema=schema,
            workspace=workspace,
            model=model,
            effort=effort,
            timeout=timeout_s,
            max_turns=max_turns,
        )
        return raw, parse_scores(raw, criteria)

    return run_until_reliable(
        listed_keys=listed_keys, timeout=timeout, attempt=attempt
    )


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
    write_reward(args.output, rows, raw, agent="grok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
