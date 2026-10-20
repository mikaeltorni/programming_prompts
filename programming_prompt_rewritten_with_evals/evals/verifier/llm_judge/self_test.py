"""Exercise LLM judge parsing, pinning, and retry behavior."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

from .native_trace import format_native_tool_records, parse_native_tool_records
from .grok import DEFAULT_MAX_TURNS, build_grok_command, score_with_grok
from .homes import claude_judge_env, claude_wrapper_script, codex_reasoning_on_path
from .ratelimit import JUDGE_CLI_FAILURES, looks_like_judge_rate_limit
from .reliability import unreliable_score_reason
from .rewardkit import (
    _rewardkit_error_excerpt,
    rewardkit_backend,
    rewardkit_command,
    run_rewardkit,
    score_with_rewardkit,
    write_pinned_judge_dir,
)
from .scores import (
    parse_scores,
    response_schema,
    reasoning_first_schema,
    rows_from_rewardkit_details,
)
from .workspace import (
    criteria_block,
    inspect_prompt,
    list_workspace_python,
    listed_python_keys,
    pin_workspace_python,
    workspace_python_context,
    workspace_prompt_context,
)


def run_self_test() -> int:
    """Run fixture-only LLM judge checks without launching agents.

    Parameters: none.

    Returns: zero when every check passes, otherwise one.
    """
    print("parameters=none")
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
    check(
        "reasoning_precedes_score",
        list(schema["properties"]["single_responsibility"]["properties"])
        == ["reasoning", "score"],
        "constrained output presents the explanation before the verdict",
    )
    block = criteria_block(criteria)
    check(
        "reasoning_first_example",
        block.index('"reasoning"') < block.index('"score"'),
        "the prompt example matches explanation-first schema order",
    )
    check(
        "rewardkit_flat_example",
        '"single_responsibility": {' not in criteria_block(criteria, flat_single=True),
        "a single rewardkit criterion uses its existing flat response shape",
    )
    check("criteria_token", '"yes" or "no"' in block, "prompt lists yes/no scores")
    check(
        "ratelimit_ignores_generic_cli_error",
        not looks_like_judge_rate_limit(
            "CalledProcessError: Agent CLI 'claude' exited with code 1: "
            '{"is_error":true,"duration_api_ms":0}'
        ),
        "generic is_error plus exit 1 does not establish provider quota",
    )
    check(
        "ratelimit_ignores_rewardkit_crash",
        not looks_like_judge_rate_limit(
            "subprocess.CalledProcessError: Command '['uvx', '--from', "
            "'harbor-rewardkit@0.1.7', 'rewardkit', '--judge', 'codex']' "
            "returned non-zero exit status 1."
        ),
        "a rewardkit crash without quota evidence is infrastructure",
    )
    check(
        "ratelimit_ignores_scored_no",
        not looks_like_judge_rate_limit("Judge srp: raw=no reasoning=too many helpers"),
        "a scored no is not a rate-limit",
    )
    check(
        "ratelimit_ignores_uvx_warmup_timeout",
        not looks_like_judge_rate_limit(
            "subprocess.TimeoutExpired: Command '['uvx', '--from', "
            "'harbor-rewardkit@0.1.7', 'rewardkit', '--help']' "
            "timed out after 180 seconds"
        ),
        "a warmup timeout is infrastructure, not provider quota or a scored no",
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

    backend_schema = {
        "type": "object",
        "properties": {
            "score": {"type": "string", "enum": ["yes", "no"]},
            "reasoning": {"type": "string"},
        },
        "required": ["score", "reasoning"],
        "additionalProperties": False,
    }
    reordered = reasoning_first_schema(backend_schema)
    check(
        "backend_schema_keeps_contract",
        reordered == backend_schema
        and list(reordered["properties"]) == ["reasoning", "score"]
        and list(backend_schema["properties"]) == ["score", "reasoning"],
        "the backend schema keeps types and required fields without mutating input",
    )
    with tempfile.TemporaryDirectory() as tmp:
        temp_root = Path(tmp)
        real_cli = temp_root / "codex"
        real_cli.write_text(
            "#!/usr/bin/env python3\nimport json, sys\nprint(json.dumps(sys.argv[1:]))\n",
            encoding="utf-8",
        )
        real_cli.chmod(0o755)
        schema_path = temp_root / "response schema.json"
        saved_path = os.environ.get("PATH", "")
        os.environ["PATH"] = f"{temp_root}{os.pathsep}{saved_path}"
        try:
            with codex_reasoning_on_path():
                for flag in ["--output-schema", "--output-schema="]:
                    schema_path.write_text(json.dumps(backend_schema), encoding="utf-8")
                    argv = ["exec", "a quoted prompt with spaces", "-m", "test-model"]
                    argv += ([flag, str(schema_path)] if flag == "--output-schema"
                             else [flag + str(schema_path)])
                    proc = subprocess.run(["codex", *argv], capture_output=True, text=True, check=True)
                    rewritten = json.loads(schema_path.read_text(encoding="utf-8"))
                    check(
                        "codex_schema_wrapper_" + ("separate" if flag == "--output-schema" else "equals"),
                        json.loads(proc.stdout) == argv
                        and list(rewritten["properties"]) == ["reasoning", "score"]
                        and rewritten == backend_schema,
                        "schema order changes while multi-word argv and scoring semantics survive",
                    )
                proc = subprocess.run(["codex", "--version"], capture_output=True, text=True, check=True)
                check("codex_wrapper_probe", json.loads(proc.stdout) == ["--version"],
                      "calls without a schema pass through to the real CLI")
            check("codex_wrapper_restores_path", os.environ["PATH"].split(os.pathsep)[0] == tmp,
                  "the temporary CLI wrapper restores PATH after use")
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
        parsing = lower.split("## parsing_dispatch", 1)[1].split("## domain_validation", 1)[0]
        validation = lower.split("## domain_validation", 1)[1].split("## shared_decisions", 1)[0]
        sharing = lower.split("## shared_decisions", 1)[1].split("## verdict", 1)[0]
        srp_checks = [
            ("srp_single_outer_parser", "one outer parsing boundary" in parsing,
             "public dispatch receives converted values through one outer parser"),
            ("srp_parser_owns_conversion", "token conversion" in parsing and "convert tokens after routing" in parsing,
             "token conversion belongs to parsing, never post-routing dispatch"),
            ("srp_parser_composition", "permitted composition" in parsing and "inside" in parsing,
             "smaller form parsers compose inside the outer parsing boundary"),
            ("srp_dispatch_forwards_unchanged", "forwards converted values unchanged" in parsing,
             "dispatch forwards converted arguments unchanged"),
            ("srp_operations_own_work", "operations own arithmetic" in parsing and "state changes" in parsing,
             "separate operations own calculations and mutations"),
            ("srp_direct_reads_allowed", "reading/formatting existing state needs no pass-through getter" in parsing,
             "direct reads and formatting require no artificial operation wrapper"),
            ("srp_prints_separately_scored", "do not grade docstrings, prints" in lower,
             "commenting and logging are separate policies"),
            ("srp_domain_owner_called", "called domain" in validation and "operations call applicable validators" in validation,
             "operations call domain validators before work, even for one caller"),
            ("srp_conversion_vs_domain", "lexical token grammar" in validation and "after successful conversion remain domain" in validation,
             "lexical conversion differs from predicates on converted numbers"),
            ("srp_operation_not_own_validator", "operation that calculates or mutates state is not its own separate validator" in validation,
             "calculation/mutation helpers call separate rule owners"),
            ("srp_equivalent_rules_shared", "equivalent decisions have one shared called owner" in sharing,
             "equivalent related rules share their called owner"),
            ("srp_classifications_shared", "sharing only the validator does not share the classification" in sharing,
             "shared acceptance alone does not share equivalent calculations"),
            ("srp_distinct_work_independent", "opposing updates sharing storage need no common helper" in sharing,
             "distinct operations need no artificial shared calculation"),
            ("srp_source_witness_required", "citation: relative/path.py:line" in lower and "missing evidence alone proves no violation" in lower,
             "NO needs actual source evidence and missing evidence is not a violation"),
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
                "logging_first_statement_named_params",
                "first statement after the docstring" in text and "every parameter" in text,
                "the entry print is first and includes every named parameter",
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
        "inlined source counts as reading the file" in filled
        and "truncated or omitted" in filled
        and "Do not answer no merely because" in filled,
        "prompt accepts complete inlined source and requires tools for gaps",
    )

    with tempfile.TemporaryDirectory(prefix="llm-native-completion-") as raw:
        trace = Path(raw) / "session.jsonl"
        trace.write_text("\n".join(json.dumps(event) for event in (
            {"type": "response_item", "payload": {"type": "function_call", "name": "exec_command",
                "call_id": "call-1", "arguments": "python3 evaluate.py"}},
            {"type": "event_msg", "payload": {"type": "item_completed", "item": {
                "type": "AgentMessage", "content": "invented PASS"}}},
            {"type": "event_msg", "payload": {"type": "item_completed", "item": {
                "type": "CommandExecution", "id": "exec-1", "command": ["python3", "evaluate.py"],
                "status": "completed", "aggregated_output": "all checks completed", "exit_code": 0}}},
        )) + "\n")
        native, limit = parse_native_tool_records(trace, include_command_events=True)
        legacy, legacy_limit = parse_native_tool_records(trace)
        check(
            "prompt_native_async_completion",
            len(native) == 2 and native[-1][0] == 3
            and native[-1][1].get("aggregated_output") == "all checks completed"
            and native[-1][1].get("exit_code") == 0
            and len(legacy) == 1 and limit is None and legacy_limit is None
            and "Recorded native command completion: status=completed exit_code=0"
                in format_native_tool_records("sessions/fixture.jsonl", native, preserve_tail=True),
            "prompt native evidence retains actual deferred command completion, excludes claims, and preserves default parsing",
        )

    native_records = [(index, {"type": "function_call_output", "call_id": f"call-{index}",
                               "output": f"record-{index} " + "x" * 15000}) for index in range(30)]
    context = format_native_tool_records("sessions/fixture.jsonl", native_records, preserve_tail=True)
    check(
        "prompt_native_keeps_final_execution",
        "record-0 " in context and "record-29 " in context
        and context.index("record-0 ") < context.index("record-29 ")
        and "omitted" in context.lower() and len(context.encode("utf-8")) < 81000,
        "bounded prompt chronology retains its beginning and final execution with explicit middle omission",
    )

    multiline_input = 'const patch = ' + json.dumps("*** Update File: eval.py\n-old input\n+new input\n") + ';'
    decoded_context = format_native_tool_records("sessions/patch.jsonl", [
        (1, {"type": "custom_tool_call", "input": multiline_input})], preserve_tail=True)
    check(
        "prompt_native_multiline_source_readable",
        "Decoded multiline string literals" in decoded_context
        and "*** Update File: eval.py\n-old input\n+new input\n" in decoded_context
        and multiline_input in decoded_context,
        "prompt patch previews preserve raw evidence and readable decoded source within the existing budget",
    )

    command_records = [(index, {"type": "function_call", "input": f"command-{index} " + "y" * 15000})
                       for index in range(30)]
    command_context = format_native_tool_records("sessions/commands.jsonl", command_records, preserve_tail=True)
    check(
        "prompt_native_tail_after_long_commands",
        "command-0 " in command_context and "command-29 " in command_context
        and command_context.index("command-0 ") < command_context.index("command-29 ")
        and "Native middle records omitted" in command_context
        and len(command_context.encode("utf-8")) < 81000,
        "long original commands retain initial and final execution evidence within the prompt preview budget",
    )

    prefix_context = format_native_tool_records("sessions/fixture.jsonl", native_records)
    check(
        "native_default_prefix_preserved",
        "record-0 " in prefix_context and "record-29 " not in prefix_context
        and "Native inline budget reached at sessions/fixture.jsonl:" in prefix_context,
        "other judges retain the existing prefix-only native preview",
    )

    with tempfile.TemporaryDirectory(prefix="llm-prompt-artifacts-") as raw:
        root = Path(raw)
        records = root / ".log" / "evidence"
        records.mkdir(parents=True)
        for index in range(60):
            (records / f"call-{index:03}.txt").write_text("recorded call reply\n")
        (records / "results.json").write_text('{"calls": 12, "failures": []}\n')
        (root / "prompt.md").write_text("Main prompt text\n")
        (root / "judge.md").write_text("Judge prompt text\n")
        (root / "cases.json").write_text('[]\n')
        (root / "eval").mkdir()
        (root / "eval" / "run_eval.py").write_text("# Saved runnable evaluation\n")
        context = workspace_prompt_context(root)
        sources = ["### prompt.md\n", "### judge.md\n", "### cases.json\n", "### eval/run_eval.py\n"]
        check(
            "prompt_artifacts_before_call_records",
            all(source in context for source in sources)
            and "### .log/evidence/results.json\n" in context
            and min(context.index(source) for source in sources) > context.index("### .log/evidence/results.json"),
            "source keeps collection priority and is rendered after call records as authoritative current evidence",
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
        with patch("llm_judge.workspace.native_tool_context", return_value="Native chronology only"), \
                patch("llm_judge.workspace.debugging_trace_context", return_value="Duplicate JSON chronology"), \
                patch("llm_judge.workspace.commit_source_context", return_value="Unrelated Git history") as git_context:
            prompt_evidence = pin_workspace_python("Score {criteria}", root, listed, "prompt_engineering")
        check(
            "prompt_single_native_chronology",
            "Native chronology only" in prompt_evidence and "Duplicate JSON chronology" not in prompt_evidence
            and prompt_evidence.index("### temperature.py") > prompt_evidence.index("Native chronology only")
            and "Unrelated Git history" not in prompt_evidence and not git_context.called,
            "prompt judging uses one native timeline followed by authoritative current source",
        )
        with patch("llm_judge.workspace.native_tool_context", return_value=""), \
                patch("llm_judge.workspace.debugging_trace_context", return_value="Fallback JSON chronology"):
            prompt_evidence = pin_workspace_python("Score {criteria}", root, listed, "prompt_engineering")
        check(
            "prompt_chronology_fallback",
            "Fallback JSON chronology" in prompt_evidence,
            "prompt judging retains observed command evidence when native logs are unavailable",
        )
        original_log = "Original task-log evidence: want: independently expected result"
        with patch("llm_judge.workspace.original_task_logs_context", return_value=original_log):
            for judge_name in ("debug", "testing", "commenting"):
                evidence = pin_workspace_python("Score it.\n{criteria}\n", root, listed, judge_name)
                check(
                    "original_logs_routed_" + judge_name,
                    (original_log in evidence) == (judge_name in {"debug", "testing"}),
                    "original regression logs reach debug and testing, without unrelated judge context",
                )
        with patch("llm_judge.workspace.original_task_logs_context", return_value=original_log):
            evidence = pin_workspace_python("Score {criteria}", root, listed, "prompt_engineering")
        check(
            "prompt_original_logs_after_final_source",
            evidence.index(original_log) > evidence.index("### temperature.py") and evidence.count(original_log) == 1,
            "literal original prompt failure logs remain visible after current source without duplication",
        )
        check(
            "prompt_policy_after_quoted_evidence",
            evidence.endswith("Score {criteria}") and evidence.count("Score {criteria}") == 1,
            "prompt judge instructions appear once after quoted evidence and original logs",
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
        passing_mapping = [{
            "name": "feature_commits", "reward": 0.0,
            "reasoning": "All requested Features have distinct working commits; score yes.",
        }]
        check(
            "retry_contradictory_feature_no",
            unreliable_score_reason(passing_mapping, listed_keys)
            == "contradictory_no:feature_commits",
            "a no verdict with a passing mapping is retried",
        )
        for case_name, reasoning, expected in [
            ("retry_final_no_violation", "I find no criterion violation: every Feature has its own working commit.", "contradictory_no:feature_commits"),
            ("retry_final_retraction", "The ledger might split a sentence. Thus this is not a violation; all rows match.", "contradictory_no:feature_commits"),
            ("retry_terminal_no_violation_evidenced", "The capability maps to its own commit; no violation is evidenced.", "contradictory_no:feature_commits"),
            ("keep_earlier_no_violation_evidenced", "No violation is evidenced. However, the later capability was bundled.", None),
            ("keep_conditional_no_violation_evidenced", "If no violation is evidenced, this passes. The ledger actually omits a sentence.", None),
            ("keep_later_real_violation", "This is not a violation of the first Feature. The next Feature is bundled, so the criterion fails.", None),
            ("keep_conditional_reasoning", "If I find no criterion violation, I will pass it. The ledger actually splits a sentence.", None),
        ]:
            check(
                case_name,
                unreliable_score_reason([
                    {"name": "feature_commits", "reward": 0.0, "reasoning": reasoning}
                ], listed_keys) == expected,
                "final contradictions retry; later and conditional failures remain scored",
            )
        for case_name, source, reasoning, expected in [
            ("retry_invented_request_period", "It should store a value) and may read it.", 'The source has a period after “value)” and starts another sentence.', "request_boundary_conflict:feature_commits"),
            ("keep_actual_request_period", "It should store a value). It should read it.", 'The source has a period after “value)” and starts another sentence.', None),
            ("keep_conditional_period_claim", "It should store a value) and may read it.", 'If the source has a period after “value)”, it is a separate sentence.', None),
        ]:
            check(
                case_name,
                unreliable_score_reason([
                    {"name": "feature_commits", "reward": 0.0, "reasoning": reasoning}
                ], listed_keys, request_text=source) == expected,
                "literal request punctuation is checked without deriving Feature counts",
            )
        history_helper = root / "bank.py"
        history_helper.write_text(
            "def _account_history(name):\n"
            "    result = name\n"
            "    print(result)\n"
            "    return result\n",
            encoding="utf-8",
        )
        alleged_fallthrough = [{
            "name": "entry_exit_prints", "reward": 0.0,
            "reasoning": "`_account_history` has a reachable normal fallthrough "
            "with no return, so its implicit None exit is not printed.",
        }]
        check(
            "retry_source_conflict_final_return",
            unreliable_score_reason(
                alleged_fallthrough, listed_keys, judge_name="logging",
                python_files=[history_helper],
            ) == "source_conflict:entry_exit_prints:_account_history",
            "an implicit-exit claim contradicted by a final return is retried",
        )
        history_helper.write_text(
            "def _account_history(name):\n"
            "    result = name\n"
            "    print(result)\n",
            encoding="utf-8",
        )
        check(
            "allow_real_fallthrough",
            unreliable_score_reason(
                alleged_fallthrough, listed_keys, judge_name="logging",
                python_files=[history_helper],
            ) is None,
            "a real implicit exit remains a scored failure",
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
            and prompt_text.rindex('"reasoning"') < prompt_text.rindex('"score"')
            and "def convert():" in prompt_text
            and (work / "judge.toml").is_file(),
            "temp rewardkit dir lists real Python and supplies the shared reasoning-first criteria example",
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
            model="gpt-6-luna",
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

    # Runner: python3 verifier/run_llm_judge.py --self-test (from evals/).
    # Reproduce the archived E2BIG crash through the public rewardkit runner.
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        package = root / "rewardkit"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "agents.py").write_text(
            "class CodexCLI:\n"
            "    def build_command(self, prompt, schema, allowed_tools=()):\n"
            "        return ['codex', 'exec', prompt, '--model', 'fixture model']\n",
            encoding="utf-8",
        )
        cli = root / "codex"
        cli.write_text(
            f"#!{sys.executable}\n"
            "import hashlib, json, os, sys\n"
            "payload = sys.stdin.read() if sys.argv[2] == '-' else sys.argv[2]\n"
            "print(json.dumps({'argv': sys.argv[1:], 'transport_dir': "
            "os.environ.get('ACC_JUDGE_PROMPT_DIR'), 'digest': "
            "hashlib.sha256(payload.encode('utf-8')).hexdigest()}))\n",
            encoding="utf-8",
        )
        cli.chmod(0o755)
        # The installed rewardkit command has this basename and import boundary.
        runner = root / "rewardkit-bin" / "rewardkit"
        runner.parent.mkdir()
        runner.write_text(
            f"#!{sys.executable}\n"
            "import json, subprocess, sys\n"
            "from pathlib import Path\n"
            "from rewardkit.agents import CodexCLI\n"
            "args = sys.argv[1:]\n"
            "prompt = (Path(args[0]) / 'prompt.md').read_text(encoding='utf-8')\n"
            "proc = subprocess.run(CodexCLI().build_command(prompt, {}), "
            "capture_output=True, text=True, check=True)\n"
            "Path(args[args.index('--output') + 1]).write_text(proc.stdout)\n",
            encoding="utf-8",
        )
        runner.chmod(0o755)
        work = root / "judge"
        work.mkdir()
        prompt = "Full evidence with spaces, quotes and \nUnicode: é漢字\n" * 5000
        (work / "prompt.md").write_text(prompt, encoding="utf-8")
        output = root / "reward.json"
        with patch.dict(os.environ, {
            "PATH": f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
            "PYTHONPATH": str(root),
        }), patch("llm_judge.rewardkit.rewardkit_command", return_value=[str(runner)]), \
                patch("llm_judge.rewardkit.ensure_rewardkit_cli"):
            try:
                with codex_reasoning_on_path():
                    run_rewardkit(work=work, output=output, backend="codex",
                                  model="fixture model", workspace=root, timeout=30)
                result = json.loads(output.read_text())
                ok = (result['argv'] == ['exec', '-', '--model', 'fixture model']
                      and result['digest'] == hashlib.sha256(prompt.encode('utf-8')).hexdigest()
                      and not Path(result['transport_dir']).exists())
            except subprocess.CalledProcessError:
                ok = False
        check("codex_large_prompt_transport", ok,
              "complete evidence above Linux's per-argument limit reaches stdin unchanged")
        (work / "prompt.md").write_text("small prompt with spaces", encoding="utf-8")
        with patch.dict(os.environ, {
            "PATH": f"{root}{os.pathsep}{os.environ.get('PATH', '')}",
            "PYTHONPATH": str(root),
        }), patch("llm_judge.rewardkit.rewardkit_command", return_value=[str(runner)]), \
                patch("llm_judge.rewardkit.ensure_rewardkit_cli"):
            run_rewardkit(work=work, output=output, backend="claude-code",
                          model="fixture model", workspace=root, timeout=30)
        result = json.loads(output.read_text())
        check("other_backend_transport_unchanged",
              result['argv'] == ['exec', 'small prompt with spaces', '--model', 'fixture model']
              and result['transport_dir'] is None,
              "the Codex transport adapter does not change other backend launches")

    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} llm-judge self-test(s) failed", flush=True)
        print(1)
        return 1
    print(f"{len(cases)}/{len(cases)} llm-judge self-tests passed", flush=True)
    print(0)
    return 0
