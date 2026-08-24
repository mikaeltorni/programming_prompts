"""Exercise LLM judge parsing, pinning, and retry behavior."""

from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .grok import DEFAULT_MAX_TURNS, build_grok_command, score_with_grok
from .homes import claude_wrapper_script
from .reliability import unreliable_score_reason
from .rewardkit import rewardkit_backend, score_with_rewardkit, write_pinned_judge_dir
from .scores import (
    parse_scores,
    response_schema,
    rows_from_rewardkit_details,
)
from .workspace import (
    criteria_block,
    inspect_prompt,
    list_workspace_python,
    listed_python_keys,
    pin_workspace_python,
    workspace_python_context,
)


def run_self_test() -> int:
    """Run fixture-only LLM judge checks without launching agents.

    Parameters: None.

    Returns: zero when every check passes, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        """Record and print one self-test result.

        Parameters: name - check name; ok - whether it passed; detail - expected behavior.

        Returns: None.
        """
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

    source = Path(__file__).resolve()
    judge_candidates = [
        source.parents[1] / "judges",
        source.parents[2] / "judges",
    ]
    judges = next(
        (candidate for candidate in judge_candidates if candidate.is_dir()),
        judge_candidates[-1],
    )
    srp_prompt = judges / "srp" / "prompt.md"
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
        srp_checks = [
            (
                "srp_yes_allows_dispatch",
                "dispatch" in yes_block.lower() and "if/elif" in yes_block.lower(),
                "yes-path allows a thin if/elif entrypoint",
            ),
            (
                "srp_no_does_not_punish_dispatch",
                "dispatch" not in no_block.lower(),
                "no-path does not treat dispatch as an SRP failure",
            ),
            (
                "srp_helpers_may_format",
                "formatted" in lower,
                "helpers may return a formatted result string",
            ),
            (
                "srp_logging_not_srp_fail",
                "logging" in lower and "not an srp failure" in lower,
                "logging prints are scored separately",
            ),
            (
                "srp_no_rejects_fat_entrypoint",
                "entrypoint" in no_block.lower()
                and (
                    "arithmetic" in no_block.lower()
                    or "state" in no_block.lower()
                ),
                "no-path fails when the entrypoint still does core work",
            ),
            (
                "srp_no_not_only_if",
                "only if" not in no_block.lower(),
                "no-path is not limited to one exception (false-positive hole)",
            ),
            (
                "srp_yes_allows_get_format",
                "already-computed" in yes_block.lower()
                or "get" in yes_block.lower(),
                "thin entrypoint may format existing state in one line",
            ),
            (
                "srp_yes_allows_int_in_helper",
                "int()" in yes_block or "already-split" in yes_block.lower(),
                "int() of a split token in a state helper is core logic",
            ),
        ]
        for item in srp_checks:
            check(*item)
    else:
        check("srp_prompt_present", False, f"missing {srp_prompt}")

    commenting_prompt = judges / "commenting" / "prompt.md"
    if commenting_prompt.is_file():
        text = commenting_prompt.read_text(encoding="utf-8").lower()
        for item in [
            (
                "commenting_every_function",
                "every function" in text,
                "commenting scores every function, not some",
            ),
            (
                "commenting_same_line_labels",
                "same line" in text,
                "Parameters:/Returns: content stays on the label line",
            ),
            (
                "commenting_rejects_wrapped",
                "wrapped" not in text and "google" in text,
                "Google-style wrapped Parameters: is a no, not a yes",
            ),
            ("commenting_rejects_args", "args:" in text, "Args: remains a commenting failure"),
            (
                "commenting_accepts_none_case",
                "capitalization" in text or "does not matter" in text,
                "Parameters: none and Parameters: None both pass",
            ),
            (
                "commenting_blank_line_ok",
                "blank line" in text,
                "blank line before Parameters: is a yes",
            ),
        ]:
            check(*item)
    else:
        check("commenting_prompt_present", False, f"missing {commenting_prompt}")

    logging_prompt = judges / "logging" / "prompt.md"
    if logging_prompt.is_file():
        text = logging_prompt.read_text(encoding="utf-8").lower()
        for item in [
            (
                "logging_every_function",
                "every function" in text,
                "logging scores every function, not some",
            ),
            (
                "logging_builtin_print_only",
                "print(" in text and "equivalent" not in text,
                "only builtin print(), not an equivalent",
            ),
            (
                "logging_names_and_values",
                "names and values" in text,
                "entry prints must show parameter names and values",
            ),
        ]:
            check(*item)
    else:
        check("logging_prompt_present", False, f"missing {logging_prompt}")

    rows = parse_scores(
        '{"score": "yes", "reasoning": "parse helper plus core"}', criteria
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
    commenting = [{"name": "function_commenting", "description": "docs"}]
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
    env_rows = parse_scores(json.dumps(envelope), commenting)
    check(
        "parse_grok_envelope",
        env_rows[0]["reward"] == 1.0,
        "unwrap structured_output from --output-format json",
    )
    text_envelope = {
        "structuredOutput": {},
        "structuredOutputError": "schema mismatch",
        "text": json.dumps(
            {
                "function_commenting": {
                    "score": "yes",
                    "reasoning": "All seven functions in counter.py have Parameters:",
                }
            }
        ),
    }
    text_rows = parse_scores(json.dumps(text_envelope), commenting)
    check(
        "parse_grok_text_when_structured_output_fails",
        text_rows[0]["reward"] == 1.0
        and "counter.py" in text_rows[0]["reasoning"],
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
    command = build_grok_command(
        prompt="score this",
        schema=schema,
        workspace=Path("/Projects/app"),
        model="grok-4.6",
        effort="low",
    )
    check(
        "cmd_max_turns",
        "--max-turns" in command and str(DEFAULT_MAX_TURNS) in command,
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
        "Score it.\n{criteria}\n", criteria, Path("/Projects/app"), python_files=[]
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
            [path.name for path in listed] == ["temperature.py"],
            "listing keeps solution py and drops pycache/venv",
        )
        context = workspace_python_context(root, listed)
        check(
            "context_inlines_source",
            "def convert():" in context
            and "Score ONLY these Python files" in context,
            "prompt names and inlines the real file",
        )
        pinned = pin_workspace_python("Score it.\n{criteria}\n", root, listed)
        check(
            "pin_keeps_criteria_token",
            "{criteria}" in pinned and "temperature.py" in pinned,
            "rewardkit prompt still has {criteria} after pinning files",
        )
        listed_keys = listed_python_keys(listed, root)
        withheld = [
            {
                "name": "single_responsibility",
                "reward": 0.0,
                "reasoning": "Scoring is withheld until the workspace Python is inspected.",
            }
        ]
        check(
            "retry_not_inspected",
            unreliable_score_reason(withheld, listed_keys)
            == "not_inspected:single_responsibility",
            "skip-inspect no is flagged for retry",
        )
        check(
            "retry_wrong_path",
            unreliable_score_reason(rk_rows, listed_keys)
            == "wrong_path:function_commenting:app.py",
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
            """Write an invented-path result followed by a valid result.

            Parameters: kwargs - rewardkit invocation arguments.

            Returns: None.
            """
            calls.append(str(kwargs["work"]))
            work_dir = Path(kwargs["output"]).parent
            score = 1.0 if len(calls) > 1 else 0.0
            details = {
                "commenting": {
                    "score": score,
                    "criteria": [
                        {
                            "name": "function_commenting",
                            "value": score,
                            "raw": "yes" if score else "no",
                            "reasoning": (
                                "temperature.py has Parameters:"
                                if score
                                else "Checked /Projects/app/app.py"
                            ),
                        }
                    ],
                }
            }
            Path(kwargs["output"]).write_text(
                json.dumps({"reward": score}) + "\n", encoding="utf-8"
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
            """Return one unreliable Grok score and then a usable score.

            Parameters: kwargs - Grok invocation arguments.

            Returns: serialized criterion score.
            """
            grok_calls.append(str(kwargs["prompt"]))
            score = "no" if len(grok_calls) == 1 else "yes"
            reasoning = (
                "Scoring is withheld until the workspace Python is inspected."
                if len(grok_calls) == 1
                else "temperature.py splits parse and core"
            )
            return json.dumps(
                {
                    "single_responsibility": {
                        "score": score,
                        "reasoning": reasoning,
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
