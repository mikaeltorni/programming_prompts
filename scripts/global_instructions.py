#!/usr/bin/env python3
"""Assemble selected policy sources into managed global instruction files."""

from __future__ import annotations

import os
import argparse
import re
import sys
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


SOURCE_ROOTS = {
    "original": "skills",
    "v2": "programming_prompt_rewritten_with_evals/prompts/programming-skills",
    "linux": "plugins/linux-desktop-configuration/skills",
}


def discover_sources(root: Path) -> dict[str, Path]:
    """Discover family-qualified policy names from the unchanged source tree."""
    return {
        f"{family}:{path.parent.name}": path
        for family, relative in SOURCE_ROOTS.items()
        for path in sorted((root / relative).glob("*/SKILL.md"))
    }


def select_instructions(root: Path, names: Iterable[str]) -> tuple[Instruction, ...]:
    """Resolve comma-list names, rejecting unknown or ambiguous selections."""
    sources = discover_sources(root)
    result = []
    seen = set()
    for name in names:
        matches = [key for key in sources if key == name or key.split(":", 1)[1] == name]
        if name in sources:
            matches = [name]
        if len(matches) != 1:
            raise ValueError(f"unknown or ambiguous skill {name!r}; use a family:name from --list")
        key = matches[0]
        if key in seen:
            continue
        seen.add(key)
        marker_key = key if key.startswith("v2:") else key.split(":", 1)[1]
        result.append(Instruction(marker_key, sources[key].read_text(encoding="utf-8")))
    return tuple(result)


def main(argv: list[str] | None = None) -> int:
    """Build a native file or a Harbor transport bundle with explicit selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skills", help="comma-separated skill names; empty selects none")
    parser.add_argument("--list", action="store_true", help="list family-qualified source names")
    destinations = parser.add_mutually_exclusive_group()
    destinations.add_argument("--output", type=Path, help="global Markdown destination")
    destinations.add_argument("--bundle-dir", type=Path, help="Harbor transport directory")
    parser.add_argument("--runtime", choices=["codex", "claude", "cc", "cca", "ca"])
    parser.add_argument("--config-home", type=Path, help="explicit native instance home")
    args = parser.parse_args(argv)
    try:
        if args.list:
            print("\n".join(discover_sources(args.source_root)))
            return 0
        if args.skills is None:
            parser.error("--skills is required (use --skills '' to clear managed policies)")
        if not args.output and not args.bundle_dir and not args.runtime:
            parser.error("choose --output, --bundle-dir, or --runtime")
        instructions = select_instructions(args.source_root, (name.strip() for name in args.skills.split(",") if name.strip()))
        owned = [key if key.startswith("v2:") else key.split(":", 1)[1] for key in discover_sources(args.source_root)]
        if args.bundle_dir:
            args.bundle_dir.mkdir(parents=True, exist_ok=True)
            # Harbor requires SKILL.md to discover a transport directory. The
            # harness consumes only instructions.md and never registers this skill.
            (args.bundle_dir / "SKILL.md").write_text(
                "---\nname: global-instructions\ndescription: Transport for generated global instructions.\n---\n",
                encoding="utf-8",
            )
            (args.bundle_dir / "instructions.md").write_text(render_instructions(instructions), encoding="utf-8")
        else:
            destination = args.output or instruction_path(args.runtime, args.config_home)
            write_instructions(destination, instructions, owned_keys=owned)
        return 0
    except (OSError, ValueError) as exc:
        print(f"global-instructions: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
