#!/usr/bin/env python3
"""Assemble selected policy sources into managed global instruction files."""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Iterable


def instruction_path(runtime: str, config_home: Path | None = None) -> Path:
    """Resolve the native global filename, including isolated Claude homes."""
    if runtime in {"claude", "cc", "cca"}:
        root = config_home or Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
        return root.expanduser() / "CLAUDE.md"
    if runtime in {"codex", "ca"}:
        root = config_home or Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
        return root.expanduser() / "AGENTS.md"
    raise ValueError(f"unsupported instruction runtime: {runtime}")


@dataclass(frozen=True)
class Instruction:
    """A selected source and its stable managed-block identity."""

    key: str
    text: str

    def markers(self) -> tuple[str, str]:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", self.key):
            raise ValueError(f"invalid instruction key: {self.key!r}")
        return (
            f"<!-- programming-prompts:{self.key}:start -->",
            f"<!-- programming-prompts:{self.key}:end -->",
        )


def render_instructions(instructions: Iterable[Instruction]) -> str:
    """Combine complete source texts without changing the source files."""
    blocks = []
    seen = set()
    for instruction in instructions:
        start, end = instruction.markers()
        if instruction.key in seen:
            raise ValueError(f"duplicate instruction: {instruction.key}")
        if not instruction.text.strip():
            raise ValueError(f"empty instruction: {instruction.key}")
        seen.add(instruction.key)
        blocks.append(f"{start}\n{instruction.text.strip()}\n{end}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def write_instructions(
    destination: Path,
    instructions: Iterable[Instruction],
    *,
    owned_keys: Iterable[str] = (),
) -> bool:
    """Atomically replace owned blocks, retaining unrelated user instructions."""
    instructions = tuple(instructions)
    rendered = render_instructions(instructions)
    current = destination.read_text(encoding="utf-8") if destination.exists() else ""
    remaining = current
    for key in dict.fromkeys((*owned_keys, *(item.key for item in instructions))):
        start, end = Instruction(key, "").markers()
        if remaining.count(start) != remaining.count(end):
            raise ValueError(f"incomplete managed block {key} in {destination}")
        pattern = re.escape(start) + r".*?" + re.escape(end)
        remaining = re.sub(pattern, "", remaining, flags=re.DOTALL)
    updated = remaining.rstrip() + ("\n\n" if remaining.strip() and rendered else "") + rendered
    if not updated.strip():
        updated = ""
    if updated == current:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Replace a symlink target rather than overwriting a user's link.
    target = destination.resolve() if destination.is_symlink() else destination
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(updated)
        os.chmod(temporary, target.stat().st_mode & 0o777 if target.exists() else 0o644)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True
