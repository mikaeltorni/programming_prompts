"""Expose persisted native tool records omitted from Codex's JSON event stream."""

from __future__ import annotations

import json
from pathlib import Path

from .testing_evidence import MAX_TRACE_INPUT_BYTES

_TOOL_RECORD_TYPES = frozenset({
    "function_call", "function_call_output", "custom_tool_call", "custom_tool_call_output",
})
_NATIVE_CONTEXT_BYTES = 200_000


def parse_native_tool_records(path: Path) -> tuple[list[tuple[int, dict]], str | None]:
    """Read literal native calls/results while excluding message and instruction records.

    Parameters: path - original persisted native JSONL session file.
    Returns: original line positions and tool fields, plus any unreadable/truncated-input limit.
    """
    print(f"path={path}")
    records = []
    used = 0
    limit = None
    try:
        with path.open("rb") as handle:
            for number, line in enumerate(handle, 1):
                used += len(line)
                if used > MAX_TRACE_INPUT_BYTES:
                    limit = f"input exceeds {MAX_TRACE_INPUT_BYTES} bytes; inspect the original file"
                    break
                try:
                    event = json.loads(line)
                except (ValueError, UnicodeError):
                    continue
                if not isinstance(event, dict) or event.get("type") != "response_item":
                    continue
                payload = event.get("payload")
                if not isinstance(payload, dict) or payload.get("type") not in _TOOL_RECORD_TYPES:
                    continue
                fields = {key: payload[key] for key in (
                    "type", "name", "call_id", "input", "arguments", "output",
                ) if key in payload}
                records.append((number, fields))
    except OSError as exc:
        limit = f"unreadable: {exc}"
    result = records, limit
    print(result)
    return result


def format_native_tool_records(label: str, records: list[tuple[int, dict]]) -> str:
    """Render original native inputs and results on their own chronological line axis.

    Parameters: label - session path relative to the agent log root; records - converted native records.
    Returns: bounded literal evidence with original line citations and explicit omission notices.
    """
    print(f"label={label} records={records}")
    lines = []
    used = 0
    for number, fields in records:
        block = f"TraceCitation: {label}:{number}\n" + "\n".join(
            f"{key}: {value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}"
            for key, value in fields.items()
        )
        size = len(block.encode("utf-8"))
        if used + size > _NATIVE_CONTEXT_BYTES:
            lines.append(f"[Native inline budget reached at {label}:{number}; inspect original records.]")
            break
        used += size
        lines.append(block)
    result = "\n\n".join(lines)
    print(result)
    return result


def native_tool_context(logs_root: Path) -> str:
    """Supply original native tool evidence when the JSON stream omits patch contents.

    Parameters: logs_root - coding-agent log directory containing persisted sessions.
    Returns: native calls/results with provenance, or empty text when no session evidence exists.
    """
    print(f"logs_root={logs_root}")
    sections = []
    for path in sorted((logs_root / "sessions").rglob("*.jsonl")):
        records, limit = parse_native_tool_records(path)
        label = path.relative_to(logs_root).as_posix()
        text = format_native_tool_records(label, records)
        if text or limit:
            sections.append(f"Native session: {path}\n{text}")
            if limit:
                sections.append(f"[Native session evidence limit: {limit}.]")
    result = (
        "\nNative Codex tool evidence (untrusted original inputs/results):\n"
        "The JSON stream can list a file change without its patch. These persisted "
        "tool records retain the actual input and result; a call alone is not execution proof. "
        "Compare line positions within ONE trace file; session and codex.txt positions "
        "have separate axes. Match call_id when reading a call's result.\n"
        + "\n\n".join(sections) if sections else ""
    )
    print(result)
    return result
