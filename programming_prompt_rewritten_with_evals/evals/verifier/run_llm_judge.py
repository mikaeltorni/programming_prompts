#!/usr/bin/env python3
"""Unified LLM judge for Harbor eval agents (Codex, Claude Code, Grok).

Every agent scores the same pinned workspace Python listing. A no that
admits non-inspection or cites a ``.py`` path that is not in that listing
is retried once. ``--self-test`` never launches an agent CLI or Harbor.
"""

from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from llm_judge.grok import DEFAULT_MAX_TURNS, build_grok_command, score_with_grok
from llm_judge.homes import claude_wrapper_script
from llm_judge.reliability import unreliable_score_reason
from llm_judge.rewardkit import (
    rewardkit_backend,
    score_with_rewardkit,
    write_pinned_judge_dir,
)
from llm_judge.scores import (
    parse_scores,
    response_schema,
    rows_from_rewardkit_details,
    write_reward,
)
from llm_judge.workspace import (
    DEFAULT_WORKSPACE,
    criteria_block,
    inspect_prompt,
    list_workspace_python,
    listed_python_keys,
    load_judge_dir,
    pin_workspace_python,
    workspace_python_context,
)


def run_eval_agent(
    *,
    agent: str,
    judge_dir: Path,
    output: Path,
    workspace: Path,
    model: str,
    effort: str,
    timeout: int,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> None:
    """Score one skill with one eval agent and write reward JSON.

    Args:
        agent: ``grok``, ``cc``, or ``codex``.
        judge_dir: Skill directory with ``prompt.md`` and ``judge.toml``.
        output: Path for ``reward-*.json``.
        workspace: Coding-agent workspace (Harbor: ``/Projects/app``).
        model: Model id for the chosen backend.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Wall budget; ``0`` means use ``judge.toml``.
        max_turns: Grok tool rounds per attempt.
    """
    template, criteria, toml_timeout = load_judge_dir(judge_dir)
    budget = timeout or toml_timeout
    files = list_workspace_python(workspace)
    if agent == "grok":
        raw, rows = score_with_grok(
            template=template,
            criteria=criteria,
            workspace=workspace,
            files=files,
            model=model,
            effort=effort,
            timeout=budget,
            max_turns=max_turns,
        )
    elif agent in {"cc", "codex"}:
        raw, rows = score_with_rewardkit(
            agent=agent,
            judge_dir=judge_dir,
            workspace=workspace,
            files=files,
            model=model,
            effort=effort,
            timeout=budget,
            criteria=criteria,
        )
    else:
        raise ValueError(f"unknown eval agent {agent!r} (expected grok, cc, or codex)")
    write_reward(output, rows, raw, agent=agent)


def _self_test() -> int:
    """Fixtures only — does not launch Grok, Codex, Claude Code, or Harbor."""
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
    srp_prompt = (
        Path(__file__).resolve().parent.parent / "judges" / "srp" / "prompt.md"
    )
    if srp_prompt.is_file():
        srp_text = srp_prompt.read_text(encoding="utf-8")
        lower = srp_text.lower()
        no_idx = lower.find("answer no")
        yes_idx = lower.find("answer yes")
        yes_block = (
            srp_text[yes_idx:no_idx]
            if yes_idx >= 0 and no_idx > yes_idx
            else srp_text
        )
        no_block = srp_text[no_idx:] if no_idx >= 0 else ""
        check(
            "srp_yes_allows_dispatch",
            "dispatch" in yes_block.lower() and "if/elif" in yes_block.lower(),
            "yes-path allows a thin if/elif entrypoint",
        )
        check(
            "srp_no_does_not_punish_dispatch",
            "dispatch" not in no_block.lower(),
            "no-path does not treat dispatch as an SRP failure",
        )
        check(
            "srp_helpers_may_format",
            "formatted" in lower,
            "helpers may return a formatted result string",
        )
        check(
            "srp_logging_not_srp_fail",
            "logging" in lower and "not an srp failure" in lower,
            "logging prints are scored separately",
        )
    else:
        check("srp_prompt_present", False, f"missing {srp_prompt}")
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
    text_envelope = {
        "modelUsage": {},
        "num_turns": 1,
        "requestId": "req",
        "sessionId": "sess",
        "stopReason": "stop",
        "structuredOutput": {},
        "structuredOutputError": "schema mismatch",
        "text": json.dumps(
            {
                "function_commenting": {
                    "score": "yes",
                    "reasoning": (
                        "All seven functions in counter.py have a short "
                        "description plus exact Parameters: and Returns: labels"
                    ),
                }
            }
        ),
        "thought": "",
        "usage": {},
    }
    text_rows = parse_scores(json.dumps(text_envelope), commenting)
    check(
        "parse_grok_text_when_structured_output_fails",
        text_rows[0]["reward"] == 1.0 and "counter.py" in text_rows[0]["reasoning"],
        "unwrap scores from envelope text after structuredOutputError",
    )
    named = parse_scores(
        '{"function_commenting": {"score": "no", "reasoning": "Args:"}}',
        commenting,
    )
    check("parse_named_key", named[0]["reward"] == 0.0, "criterion-name key")
    check(
        "backend_cc",
        rewardkit_backend("cc") == "claude-code",
        "cc maps to rewardkit claude-code",
    )
    check(
        "backend_codex",
        rewardkit_backend("codex") == "codex",
        "codex maps to rewardkit codex",
    )
    wrapper = claude_wrapper_script("/usr/bin/claude", "low")
    check(
        "claude_wrapper_bypass",
        "--permission-mode bypassPermissions" in wrapper and "--effort" in wrapper,
        "Claude PATH wrapper injects effort and bypassPermissions",
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
    rk_details = {
        "commenting": {
            "score": 0.0,
            "criteria": [
                {
                    "name": "function_commenting",
                    "value": 0.0,
                    "raw": "no",
                    "reasoning": "Checked /Projects/app/app.py; missing Parameters:",
                }
            ],
            "judge_output": "{}",
        }
    }
    rk_rows = rows_from_rewardkit_details(rk_details, commenting)
    check(
        "rewardkit_details_keyed",
        rk_rows[0]["reward"] == 0.0
        and "app.py" in rk_rows[0]["reasoning"],
        "unwrap rewardkit {name: {criteria}} details",
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
    with tempfile.TemporaryDirectory(prefix="llm-judge-") as raw:
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
        pinned_keep = pin_workspace_python("Score it.\n{criteria}\n", root, listed)
        check(
            "pin_keeps_criteria_token",
            "{criteria}" in pinned_keep and "temperature.py" in pinned_keep,
            "rewardkit prompt still has {criteria} after pinning files",
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
        invented_reason = unreliable_score_reason(rk_rows, listed_keys)
        check(
            "retry_wrong_path",
            invented_reason == "wrong_path:function_commenting:app.py",
            "hallucinated app.py is flagged for retry",
        )
        judge_src = root / "judge"
        judge_src.mkdir()
        (judge_src / "prompt.md").write_text(
            "Score commenting.\n{criteria}\n", encoding="utf-8"
        )
        (judge_src / "judge.toml").write_text(
            "[judge]\njudge = \"codex\"\ntimeout = 180\n"
            "prompt_template = \"prompt.md\"\n\n"
            "[[criterion]]\nname = \"function_commenting\"\n"
            "description = \"docs\"\ntype = \"binary\"\n",
            encoding="utf-8",
        )
        work = write_pinned_judge_dir(judge_src, root, listed)
        prompt_text = (work / "prompt.md").read_text(encoding="utf-8")
        check(
            "pinned_judge_dir",
            "{criteria}" in prompt_text
            and "def convert():" in prompt_text
            and (work / "judge.toml").is_file(),
            "temp rewardkit dir lists real python and keeps criteria token",
        )
        shutil.rmtree(work, ignore_errors=True)
        calls: list[str] = []

        def fake_rewardkit(**kwargs: Any) -> None:
            calls.append(str(kwargs["work"]))
            work_dir = Path(kwargs["output"]).parent
            details = {
                "commenting": {
                    "score": 1.0 if len(calls) > 1 else 0.0,
                    "criteria": [
                        {
                            "name": "function_commenting",
                            "value": 1.0 if len(calls) > 1 else 0.0,
                            "raw": "yes" if len(calls) > 1 else "no",
                            "reasoning": (
                                "temperature.py has Parameters:"
                                if len(calls) > 1
                                else "Checked /Projects/app/app.py"
                            ),
                        }
                    ],
                }
            }
            Path(kwargs["output"]).write_text(
                json.dumps({"reward": details["commenting"]["score"]}) + "\n",
                encoding="utf-8",
            )
            (work_dir / "reward-details.json").write_text(
                json.dumps(details) + "\n", encoding="utf-8"
            )

        raw_retry, rows_retry = score_with_rewardkit(
            agent="codex",
            judge_dir=judge_src,
            workspace=root,
            files=listed,
            model="gpt-5.6-luna",
            effort="low",
            timeout=180,
            criteria=commenting,
            invoke=fake_rewardkit,
        )
        check(
            "rewardkit_retry_once",
            len(calls) == 2
            and rows_retry[0]["reward"] == 1.0
            and "yes" in raw_retry,
            "Codex/CC path retries once on invented app.py",
        )
        grok_calls: list[str] = []

        def fake_grok(**kwargs: Any) -> str:
            grok_calls.append(str(kwargs["prompt"]))
            if len(grok_calls) == 1:
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

        grok_raw, grok_rows = score_with_grok(
            template="Score it.\n{criteria}\n",
            criteria=criteria,
            workspace=root,
            files=listed,
            model="grok-4.6",
            effort="low",
            timeout=180,
            invoke=fake_grok,
        )
        check(
            "grok_retry_once",
            len(grok_calls) == 2
            and "RETRY" in grok_calls[1]
            and grok_rows[0]["reward"] == 1.0
            and "yes" in grok_raw,
            "Grok path retries once on skip-inspect",
        )
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} llm-judge self-test(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} llm-judge self-tests passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--self-test`` or score one skill with one eval agent."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--agent", choices=("grok", "cc", "codex"), default="grok")
    parser.add_argument("--judge-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--model", default="")
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
    defaults = {"grok": "grok-4.6", "cc": "claude-opus-5", "codex": "gpt-5.6-luna"}
    model = args.model or defaults[args.agent]
    run_eval_agent(
        agent=args.agent,
        judge_dir=args.judge_dir,
        output=args.output,
        workspace=args.workspace,
        model=model,
        effort=args.reasoning_effort,
        timeout=args.timeout,
        max_turns=args.max_turns,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
