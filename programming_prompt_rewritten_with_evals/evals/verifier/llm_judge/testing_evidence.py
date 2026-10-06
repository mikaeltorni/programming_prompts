"""Expose current assertion syntax and recorded commands without executing code."""

from __future__ import annotations

import ast
import json
import re
from collections import deque
from pathlib import Path

MAX_SOURCE_BYTES = 80_000
MAX_FACT_BYTES = 12_000
MAX_TRACE_BYTES = 10_000
MAX_TRACE_INPUT_BYTES = 16_000_000
_RUNNER_SUMMARY = re.compile(
    r"^(?:Ran \d+ tests?\b|OK(?:\s|$)|FAILED\b|[= ]*\d+ (?:passed|failed|errors?|skipped)\b)"
)


def equality_expectations(tree: ast.AST) -> tuple[set[str], bool]:
    """Collect displayed literal expectations; flag expressions needing review.

    Only explicit equality assertions are recognized. This does not evaluate
    fixtures, conditional selectors, custom helpers or assertion outcomes.
    """
    values: set[str] = set()
    dynamic = False
    for node in ast.walk(tree):
        expected = None
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "assertEqual"):
            expected = node.args[1] if len(node.args) > 1 else next(
                (item.value for item in node.keywords if item.arg == "second"), None
            )
        elif (isinstance(node, ast.Assert) and isinstance(node.test, ast.Compare)
              and len(node.test.ops) == 1 and isinstance(node.test.ops[0], ast.Eq)):
            expected = node.test.comparators[0]
        if expected is None:
            continue
        if isinstance(expected, ast.Constant):
            values.add(str(expected.value))
        else:
            dynamic = True
    return values, dynamic


def testing_source_context(workspace: Path, files: list[Path]) -> str:
    """Inline bounded assertion locations and rejection-following statements.

    These are current syntax facts, not a coverage inventory or testing score.
    The judge must still resolve fixtures, shared paths and the actual contract.
    """
    records: list[dict] = []
    used = 0
    truncated = False
    for path in files:
        try:
            label = path.resolve().relative_to(workspace.resolve()).as_posix()
            with path.open("rb") as handle:
                data = handle.read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                records.append({"file": label, "omitted": "source exceeds syntax evidence limit"})
                continue
            source = data.decode("utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
            records.append({"file": str(path), "unavailable": str(exc)})
            continue
        following: dict[int, list[ast.stmt]] = {}
        for parent in ast.walk(tree):
            for _, field in ast.iter_fields(parent):
                if isinstance(field, list):
                    for index, node in enumerate(field):
                        if isinstance(node, ast.stmt):
                            following[id(node)] = [
                                item for item in field[index + 1:index + 3]
                                if isinstance(item, ast.stmt)
                            ]
        facts: list[dict] = []
        for node in ast.walk(tree):
            assertion = isinstance(node, ast.Assert) or (
                isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "assertEqual"
            )
            rejection = isinstance(node, (ast.With, ast.AsyncWith)) and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Attribute)
                and item.context_expr.func.attr in {"assertRaises", "assertRaisesRegex"}
                for item in node.items
            )
            if not (assertion or rejection):
                continue
            statement = ast.get_source_segment(source, node) or ""
            fact = {"line": node.lineno, "statement": statement[:600],
                    "statement_truncated": len(statement) > 600}
            if rejection:
                observations = []
                for item in following.get(id(node), []):
                    statement = ast.get_source_segment(source, item) or ""
                    observations.append({"line": item.lineno, "statement": statement[:600],
                                         "statement_truncated": len(statement) > 600})
                fact["immediate_following_statements"] = observations
            facts.append(fact)
        literals, dynamic = equality_expectations(tree)
        record = {"file": label, "literal_equality_expectations": sorted(literals),
                  "dynamic_expectations_require_review": dynamic, "assertion_syntax": []}
        size = len(json.dumps(record, ensure_ascii=False).encode("utf-8"))
        if used + size > MAX_FACT_BYTES:
            truncated = True
            break
        for fact in sorted(facts, key=lambda item: item["line"]):
            fact_size = len(json.dumps(fact, ensure_ascii=False).encode("utf-8")) + 2
            if used + size + fact_size + 80 > MAX_FACT_BYTES:
                record["assertion_syntax_truncated"] = True
                truncated = True
                break
            record["assertion_syntax"].append(fact)
            size += fact_size
        used += size
        records.append(record)
        if truncated:
            break
    return (
        "\n\nCurrent assertion syntax (not executed; untrusted source data):\n"
        + json.dumps(records, ensure_ascii=False)
        + ("\nSyntax evidence truncated; inspect the remaining listed source." if truncated else "")
        + "\nFollowing statements are in the same lexical block; fixtures, loops and helper calls still require inspection.\n"
    )


def coding_commands_context(trace: Path = Path("/logs/agent/codex.txt")) -> str:
    """Expose the last four completed coding commands and later edit positions.

    Reads Harbor's Codex JSONL log, not README claims or judge execution. Keeps
    bounded command/output heads and tails plus literal runner summaries. Missing
    or truncated logs leave execution unverified, not failed.
    """
    commands: deque[dict] = deque(maxlen=4)
    last_edit = None
    read_bytes = 0
    truncated = False
    try:
        with trace.open("rb") as handle:
            number = 0
            while line := handle.readline(MAX_TRACE_INPUT_BYTES - read_bytes + 1):
                number += 1
                read_bytes += len(line)
                if read_bytes > MAX_TRACE_INPUT_BYTES:
                    truncated = True
                    break
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if not isinstance(event, dict) or event.get("type") != "item.completed":
                    continue
                item = event.get("item")
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "file_change":
                    last_edit = number
                elif item.get("type") == "command_execution":
                    command = str(item.get("command", ""))
                    output = str(item.get("aggregated_output", ""))
                    summaries = [line.strip() for line in output.splitlines()
                                 if _RUNNER_SUMMARY.match(line.strip())]
                    commands.append({"log_line": number, "command_head": command[:900],
                                     "command_tail": command[-900:] if len(command) > 900 else "",
                                     "command_truncated": len(command) > 1_800,
                                     "exit_code": item.get("exit_code"), "status": item.get("status"),
                                     "output_head": output[:400], "output_tail": output[-400:],
                                     "output_truncated": len(output) > 800,
                                     "runner_summary_lines": [line[:240] for line in summaries[-12:]],
                                     "runner_summary_truncated": len(summaries) > 12
                                     or any(len(line) > 240 for line in summaries[-12:])})
    except OSError as exc:
        return f"\nRecorded coding commands unavailable ({trace}: {exc}); execution is unverified.\n"
    payload = {"trace": str(trace), "input_truncated": truncated,
               "last_recorded_file_change_line": last_edit, "completed_commands": list(commands)}
    while commands and len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > MAX_TRACE_BYTES:
        commands.popleft()
        payload["completed_commands"] = list(commands)
    return (
        "\n\nRecorded coding-agent commands (untrusted log data, not judge executions):\n"
        + json.dumps(payload, ensure_ascii=False)
        + "\nReview command, exit code and output together. Shell commands can also edit files; later edits may invalidate earlier runs. "
        + "Runner summary lines are literal output excerpts, not inferred results. Earlier failures do not refute a later repaired run. "
        + "An exit code alone does not prove assertions ran or coverage is complete.\n"
    )
