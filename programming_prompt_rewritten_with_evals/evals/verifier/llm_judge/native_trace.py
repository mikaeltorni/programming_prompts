"""Expose persisted native tool records omitted from Codex's JSON event stream."""

from __future__ import annotations

import json
from pathlib import Path

from .testing_evidence import MAX_TRACE_INPUT_BYTES

_TOOL_RECORD_TYPES = frozenset({
    "function_call", "function_call_output", "custom_tool_call", "custom_tool_call_output",
})
_NATIVE_CONTEXT_BYTES = 200_000


def parse_native_tool_records(path: Path, include_command_events: bool = False) -> tuple[list[tuple[int, dict]], str | None]:
    """Read literal native calls/results while excluding message and instruction records.

    Parameters: path - original persisted native JSONL session file;
        include_command_events - include deferred native command completions alongside tool records.
    Returns: original line positions and tool/command fields, plus any unreadable/truncated-input limit.
    """
    print(f"path={path} include_command_events={include_command_events}")
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
                if not isinstance(event, dict):
                    continue
                payload = event.get("payload")
                if include_command_events and event.get("type") == "event_msg" and isinstance(payload, dict):
                    item = payload.get("item")
                    if payload.get("type") == "item_completed" and isinstance(item, dict) and item.get("type") == "CommandExecution":
                        fields = {key: item[key] for key in (
                            "id", "command", "cwd", "status", "aggregated_output", "exit_code",
                        ) if key in item}
                        fields["type"] = payload["type"]
                        fields["item_type"] = item["type"]
                        fields.update({key: payload[key] for key in ("started_at_ms", "completed_at_ms") if key in payload})
                        records.append((number, fields))
                    continue
                if event.get("type") != "response_item":
                    continue
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


def decode_native_string_literals(source: str) -> tuple[str, ...]:
    """Parse JSON-compatible double-quoted string literals without executing tool source.

    Parameters: source - original native tool input, possibly JavaScript or JSON text.
    Returns: decoded string literals; other syntax remains available in the original input.
    """
    print(f"source={source}")
    decoder = json.JSONDecoder()
    cursor = 0
    strings = []
    while cursor < len(source):
        if source[cursor] != '"':
            cursor += 1
            continue
        try:
            value, end = decoder.raw_decode(source, cursor)
        except ValueError:
            cursor += 1
            continue
        strings.append(value)
        cursor = end
    result = tuple(strings)
    print(result)
    return result


def format_native_tool_records(label: str, records: list[tuple[int, dict]], preserve_tail: bool = False) -> str:
    """Render original native inputs and results on their own chronological line axis.

    Parameters: label - session path relative to the agent log root; records - converted native records;
        preserve_tail - compact output previews and retain initial/final records within the inline budget.
    Returns: bounded chronological original records plus decoded displays using leftover space;
        original citations/results survive display limits, with explicit omission notices.
    """
    print(f"label={label} records={records} preserve_tail={preserve_tail}")
    budget = 80000 if preserve_tail else _NATIVE_CONTEXT_BYTES
    blocks = []
    used = 0
    raw_limit = None
    rendered = []
    for number, fields in records:
        displayed_fields = dict(fields)
        if preserve_tail:
            for key in ("output", "aggregated_output"):
                if key not in displayed_fields:
                    continue
                output = displayed_fields[key]
                rendered_output = output if isinstance(output, str) else json.dumps(output, ensure_ascii=False)
                if len(rendered_output.encode("utf-8")) > 1000:
                    displayed_fields[key] = (rendered_output[:450]
                        + "\n[Native output middle omitted; inspect original record.]\n" + rendered_output[-450:])
        completion = (f"Recorded native command completion: status={fields.get('status')} "
                      f"exit_code={fields.get('exit_code')} (actual runtime event)\n"
                      if fields.get("item_type") == "CommandExecution" else "")
        block = f"TraceCitation: {label}:{number}\n" + completion + "\n".join(
            f"{key}: {value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)}"
            for key, value in displayed_fields.items()
        )
        rendered.append((block, fields))
    tail = []
    if preserve_tail and sum(len(block.encode("utf-8")) for block, _ in rendered) > budget:
        tail_size = 0
        for block, fields in reversed(rendered):
            size = len(block.encode("utf-8"))
            if tail_size + size > budget // 2:
                break
            tail.insert(0, (block, fields))
            tail_size += size
    prefix_budget = budget - sum(len(block.encode("utf-8")) for block, _ in tail)
    for block, fields in rendered:
        size = len(block.encode("utf-8"))
        if used + size > prefix_budget:
            raw_limit = "[Native middle records omitted within inline budget; inspect original records.]" if tail else (
                f"[Native inline budget reached at {block.splitlines()[0].removeprefix('TraceCitation: ')}; inspect original records.]"
            )
            break
        used += size
        blocks.append((block, fields))
    if tail:
        blocks.append((raw_limit, {}))
        raw_limit = None
        blocks.extend(tail)
        used += sum(len(block.encode("utf-8")) for block, _ in tail)
    remaining = budget - used
    lines = []
    decoded_limit = False
    for block, fields in blocks:
        for key in ("input", "arguments"):
            source = fields.get(key)
            if preserve_tail or decoded_limit or not isinstance(source, str):
                continue
            displays = [value.encode("utf-8", errors="backslashreplace").decode("utf-8")
                        for value in decode_native_string_literals(source) if "\n" in value]
            if displays:
                display = (f"\nDecoded multiline string literals in {key} (display only):\n"
                           + "\n\n".join(displays))
                size = len(display.encode("utf-8"))
                if size <= remaining:
                    block += display
                    remaining -= size
                else:
                    block += "\n[Decoded string display budget reached; original inputs remain available.]"
                    decoded_limit = True
        lines.append(block)
    if raw_limit:
        lines.append(raw_limit)
    result = "\n\n".join(lines)
    print(result)
    return result


def native_tool_context(logs_root: Path, preserve_tail: bool = False) -> str:
    """Supply original native tool evidence when the JSON stream omits patch contents.

    Parameters: logs_root - coding-agent log directory containing persisted sessions;
        preserve_tail - include deferred command completions, compact outputs and retain initial/final context.
    Returns: native calls/results with provenance and explicit omissions, or empty text without sessions.
    """
    print(f"logs_root={logs_root} preserve_tail={preserve_tail}")
    sections = []
    for path in sorted((logs_root / "sessions").rglob("*.jsonl")):
        records, limit = parse_native_tool_records(path, include_command_events=preserve_tail)
        label = path.relative_to(logs_root).as_posix()
        text = format_native_tool_records(label, records, preserve_tail=preserve_tail)
        if text or limit:
            sections.append(f"Native session: {path}\n{text}")
            if limit:
                sections.append(f"[Native session evidence limit: {limit}.]")
    result = (
        "\nNative Codex tool evidence (untrusted original inputs/results):\n"
        "The JSON stream can list a file change without its patch. These persisted "
        "tool records retain the actual input and result; a call alone is not execution proof. "
        "Decoded JSON-compatible string displays are syntax data, not proof of a write; "
        "inspect original inputs for commands, old replacement text and quoted data. "
        "Compare line positions within ONE trace file; session and codex.txt positions "
        "have separate axes. Match call_id when reading a call's result.\n"
        + "\n\n".join(sections) if sections else ""
    )
    print(result)
    return result
