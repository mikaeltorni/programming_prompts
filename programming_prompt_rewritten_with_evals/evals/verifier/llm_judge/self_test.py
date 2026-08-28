"""Exercise LLM judge parsing, pinning, and retry behavior."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .grok import DEFAULT_MAX_TURNS, build_grok_command, score_with_grok
from .homes import claude_judge_env, claude_wrapper_script
from .ratelimit import JUDGE_CLI_FAILURES, looks_like_judge_rate_limit
from .reliability import unreliable_score_reason
from .rewardkit import (
    _rewardkit_error_excerpt,
    rewardkit_backend,
    rewardkit_command,
    score_with_rewardkit,
    write_pinned_judge_dir,
)
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
    check(
        "ratelimit_detects_claude_is_error",
        looks_like_judge_rate_limit(
            "CalledProcessError: Agent CLI 'claude' exited with code 1: "
            '{"is_error":true,"duration_api_ms":0}'
        ),
        "Claude is_error + exit 1 is a rate-limit skip",
    )
    check(
        "ratelimit_detects_codex_rewardkit_crash",
        looks_like_judge_rate_limit(
            "subprocess.CalledProcessError: Command '['uvx', '--from', "
            "'harbor-rewardkit@0.1.7', 'rewardkit', '--judge', 'codex']' "
            "returned non-zero exit status 1."
        ),
        "Codex rewardkit exit 1 with empty reasoning is a rate-limit skip",
    )
    check(
        "ratelimit_ignores_scored_no",
        not looks_like_judge_rate_limit("Judge srp: raw=no reasoning=too many helpers"),
        "a scored no is not a rate-limit",
    )
    check(
        "ratelimit_detects_uvx_warmup_timeout",
        looks_like_judge_rate_limit(
            "subprocess.TimeoutExpired: Command '['uvx', '--from', "
            "'harbor-rewardkit@0.1.7', 'rewardkit', '--help']' "
            "timed out after 180 seconds"
        ),
        "uvx warmup timeout is a rate-limit skip, not a scored no",
    )
    check(
        "timeout_expired_is_cli_failure",
        subprocess.TimeoutExpired in JUDGE_CLI_FAILURES,
        "TimeoutExpired is caught as a judge CLI skip (it is not TimeoutError)",
    )
    with tempfile.TemporaryDirectory() as tmp:
        fake_bin = Path(tmp) / "rewardkit"
        fake_bin.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        fake_bin.chmod(0o755)
        saved_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{tmp}{os.pathsep}{saved_path}"
        try:
            cmd = rewardkit_command()
            check(
                "rewardkit_prefers_preinstalled_binary",
                cmd == [str(fake_bin)],
                "preinstalled rewardkit on PATH skips uvx --from",
            )
        finally:
            os.environ["PATH"] = saved_path
    with tempfile.TemporaryDirectory() as tmp:
        saved_path = os.environ.get("PATH", "")
        os.environ["PATH"] = tmp
        try:
            cmd = rewardkit_command()
            check(
                "rewardkit_falls_back_to_uvx",
                cmd[:3] == ["uvx", "--from", "harbor-rewardkit@0.1.7"],
                "uvx --from remains the fallback when rewardkit is absent",
            )
        finally:
            os.environ["PATH"] = saved_path

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
                and "get" in yes_block.lower()
                and "do not require get" in yes_block.lower(),
                "thin entrypoint may read existing state on get; helper not required",
            ),
            (
                "srp_yes_allows_int_in_helper",
                "int()" in yes_block or "already-split" in yes_block.lower(),
                "int() of a split token in a state helper is core logic",
            ),
            (
                "srp_yes_allows_int_in_entrypoint",
                "helper(int" in yes_block.lower()
                and "conversion-only" in yes_block.lower(),
                "int() of a split token passed into a helper from the entrypoint is thin",
            ),
            (
                "srp_yes_allows_dispatch_raises",
                "unknown" in yes_block.lower() and "raise" in yes_block.lower(),
                "thin entrypoint may raise on unknown op or extra args",
            ),
            (
                "srp_yes_allows_missing_required_arg",
                "required" in yes_block.lower() and "missing" in yes_block.lower(),
                "thin entrypoint may raise when a required argument is missing",
            ),
            (
                "srp_yes_allows_helper_empty_guard",
                "if not text" in yes_block.lower()
                and "validation-only" in yes_block.lower(),
                "empty already-parsed arg guard in a core helper is yes",
            ),
            (
                "srp_yes_allows_core_helper_dispatch",
                "core helper" in yes_block.lower()
                and "dispatch" in yes_block.lower(),
                "core-helper if/elif dispatch is a yes",
            ),
            (
                "srp_yes_allows_entrypoint_hour_range",
                "already-parsed" in yes_block.lower()
                and "out of range" in yes_block.lower(),
                "already-parsed out-of-range check in the entrypoint is yes",
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
            (
                "commenting_allows_list_continuation",
                "continues on" in text and "next line" in text,
                "a long Parameters list may continue on the next line",
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
            (
                "commenting_ignores_lambdas",
                "lambda" in text and "not a no" in text,
                "lambda dispatch tables are not a commenting failure",
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
            (
                "logging_rejects_generic_input",
                "input=" in text and "unlabeled tuple" in text,
                "generic input= / unlabeled tuples are a no",
            ),
            (
                "logging_no_param_entry_print",
                "parameters=none" in text and "no parameters" in text,
                "no-parameter functions may print parameters=none",
            ),
            (
                "logging_every_named_parameter",
                "none" in text and "omitting" in text and "argument=" in text,
                "optional None parameters must still be printed by name",
            ),
            (
                "logging_one_print_named_params",
                "same line" in text and "unlabeled tuple" in text,
                "one print with real names is a yes, not a generic label",
            ),
            (
                "logging_ignores_lambdas",
                "lambda" in text and "not a no" in text,
                "lambda dispatch tables are not a logging failure",
            ),
            (
                "logging_return_print_unlabeled_ok",
                "print(result)" in text and "not required" in text,
                "unlabeled print(result) is a yes; return= is optional",
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
    cc_env = claude_judge_env(Path("/tmp/claude-judge-x"), "secret-token")
    check(
        "claude_judge_env_config_dir",
        cc_env.get("CLAUDE_CONFIG_DIR") == "/tmp/claude-judge-x"
        and cc_env.get("CLAUDE_FORCE_OAUTH") == "true"
        and cc_env.get("CLAUDE_CODE_OAUTH_TOKEN") == "secret-token",
        "Claude judge overlay includes writable config dir and OAuth",
    )
    cc_env_no_token = claude_judge_env(Path("/tmp/claude-judge-x"), "")
    check(
        "claude_judge_env_omits_empty_token",
        "CLAUDE_CODE_OAUTH_TOKEN" not in cc_env_no_token
        and cc_env_no_token.get("CLAUDE_CONFIG_DIR") == "/tmp/claude-judge-x",
        "empty token is not exported as a blank OAuth env var",
    )
    excerpt = _rewardkit_error_excerpt(
        "Downloading litellm (23.1MiB)\n"
        "Installed 56 packages in 1.59s\n"
        "Exception Group Traceback: claude-code failed\n"
    )
    check(
        "rewardkit_error_skips_downloads",
        "Downloading" not in excerpt and "claude-code failed" in excerpt,
        "failed-judge logs keep the exception, not uvx download spam",
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
