#!/usr/bin/env bash
set -euo pipefail

python3 - <<'PY'
from pathlib import Path

Path("/app/todo.py").write_text(
    '''_ITEMS: list[str] = []


def parse_command(command: str) -> tuple[str, list[str]]:
    parts = command.strip().split()
    if not parts:
        raise ValueError("empty command")
    return parts[0], parts[1:]


def add_item(text_parts: list[str]) -> str:
    if not text_parts:
        raise ValueError("add requires text")
    text = " ".join(text_parts)
    _ITEMS.append(text)
    return f"added={len(_ITEMS)}"


def list_items() -> str:
    return f"items={','.join(_ITEMS)}"


def done_item(args: list[str]) -> str:
    if len(args) != 1:
        raise ValueError("done requires one index")
    index = int(args[0])
    if index < 1 or index > len(_ITEMS):
        raise ValueError("index out of range")
    text = _ITEMS.pop(index - 1)
    return f"done={text}"


def run_todo(command: str) -> str:
    action, args = parse_command(command)
    if action == "add":
        return add_item(args)
    if action == "list":
        if args:
            raise ValueError("list takes no arguments")
        return list_items()
    if action == "done":
        return done_item(args)
    raise ValueError(f"unsupported command: {action}")
''',
    encoding="utf-8",
)
PY
