#!/usr/bin/env python3
"""Assemble selected policy sources into managed global instruction files."""

from __future__ import annotations

import os
import argparse
import re
import sys
import shutil
import tempfile
import tomllib
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
    homes = {
        "qwen": ".codex-qwen", "qa": ".codex-qwen",
        "openrouter": ".codex-openrouter", "oa": ".codex-openrouter",
        "nvidia": ".codex-nvidia", "na": ".codex-nvidia",
        "opencode": ".config/opencode", "oca": ".config/opencode",
        "grok": ".grok", "ga": ".grok",
    }
    if runtime in homes:
        default_home = Path.home() / homes[runtime]
        if runtime in {"grok", "ga"}:
            default_home = Path(os.environ.get("GROK_HOME") or default_home)
        root = config_home or default_home
        return root.expanduser() / "AGENTS.md"
    if runtime in {"cline", "cla"}:
        root = config_home or Path.home() / "Documents/Cline/Rules"
        return root.expanduser() / "global-instructions.md"
    if runtime in {"cursor", "cu"}:
        root = config_home or Path.home() / ".cursor"
        return root.expanduser() / "rules/agent-command-center-guidelines.mdc"
    raise ValueError(f"unsupported instruction runtime: {runtime}")


CODEX_RUNTIMES = {"codex", "ca", "qwen", "qa", "openrouter", "oa", "nvidia", "na"}


def ensure_codex_instruction_budget(config_home: Path, minimum: int = 1048576) -> bool:
    """Raise the native document budget without changing other TOML settings."""
    path = config_home / "config.toml"
    current = path.read_text(encoding="utf-8") if path.exists() else ""
    values = tomllib.loads(current)
    old = values.get("project_doc_max_bytes")
    if isinstance(old, int) and old >= minimum:
        return False
    if old is not None:
        updated = re.sub(r"(?m)^\s*project_doc_max_bytes\s*=.*$", f"project_doc_max_bytes = {minimum}", current, count=1)
    else:
        updated = f"project_doc_max_bytes = {minimum}\n" + current
    tomllib.loads(updated)
    path.parent.mkdir(parents=True, exist_ok=True)
    target = path.resolve() if path.is_symlink() else path
    descriptor, temporary = tempfile.mkstemp(prefix=".instruction-budget-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(updated)
        os.chmod(temporary, target.stat().st_mode & 0o777 if target.exists() else 0o600)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return True


@dataclass(frozen=True)
class Instruction:
    """A selected source and its stable managed-block identity."""

    key: str
    text: str
    source: str = ""

    def markers(self) -> tuple[str, str]:
        if not re.fullmatch(r"[A-Za-z0-9_.:-]+", self.key):
            raise ValueError(f"invalid instruction key: {self.key!r}")
        return (
            f"<!-- programming-prompts:{self.key}:start -->",
            f"<!-- programming-prompts:{self.key}:end -->",
        )


def policy_section(instruction: Instruction) -> str:
    """Render one complete policy with metadata and nested Markdown headings."""
    text = instruction.text.strip()
    metadata = ""
    if text.startswith("---\n"):
        parts = text.split("\n---", 1)
        if len(parts) != 2:
            raise ValueError(f"unclosed frontmatter: {instruction.key}")
        metadata, text = parts[0][4:], parts[1].lstrip("\n")
    lines = []
    fence = None
    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        if fence is None and not match:
            line = re.sub(r"^(#{1,6}) ", lambda m: "#" * min(6, len(m[1]) + 2) + " ", line)
        lines.append(line)
    header = f"## Policy: {instruction.key}\n"
    if instruction.source:
        header += f"\nSource: `{instruction.source}`\n"
    if metadata:
        header += "\nSource metadata:\n" + "\n".join(f"> {line}" for line in metadata.splitlines()) + "\n"
    return header + "\n" + "\n".join(lines)


def render_instructions(instructions: Iterable[Instruction]) -> str:
    """Combine full selected policy bodies in a comprehensive instruction file."""
    blocks = []
    seen = set()
    for instruction in instructions:
        start, end = instruction.markers()
        if instruction.key in seen:
            raise ValueError(f"duplicate instruction: {instruction.key}")
        if not instruction.text.strip():
            raise ValueError(f"empty instruction: {instruction.key}")
        seen.add(instruction.key)
        blocks.append(f"{start}\n{policy_section(instruction)}\n{end}")
    if not blocks:
        return ""
    start, end = Instruction("global-instructions", "").markers()
    overview = (
        f"{start}\n# Global agent instructions\n\n"
        "These selected policies are enabled for this session in every project. "
        "Selection explicitly invokes workflow when included. Apply the policies "
        "in their required order and within their stated scope. Their complete "
        "instructions are embedded below, so rereading SKILL.md files merely to "
        "load them is unnecessary. Resolve referenced supporting resources relative "
        "to each stated source file. Explicit user instructions take precedence.\n\n"
        "## Selected policies\n\n"
        + "\n".join(f"- `{key}`" for key in (item.split("programming-prompts:", 1)[1].split(":start", 1)[0] for item in blocks))
        + f"\n{end}"
    )
    return overview + "\n\n" + "\n\n".join(blocks) + "\n"


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
    for key in dict.fromkeys(("global-instructions", *owned_keys, *(item.key for item in instructions))):
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
        result.append(Instruction(marker_key, sources[key].read_text(encoding="utf-8"), str(sources[key].resolve())))
    return tuple(result)


def main(argv: list[str] | None = None) -> int:
    """Build a native file or a Harbor transport bundle with explicit selection."""
    parser = argparse.ArgumentParser(description=__doc__)
    checkout = Path(__file__).resolve().parents[1]
    default_root = os.environ.get("PROGRAMMING_PROMPTS_DIR") or (checkout if (checkout / "skills").is_dir() else Path.home() / "projects/programming_prompts")
    parser.add_argument("--source-root", type=Path, default=Path(default_root))
    parser.add_argument("--skills", help="comma-separated skill names; empty selects none")
    parser.add_argument("--list", action="store_true", help="list family-qualified source names")
    destinations = parser.add_mutually_exclusive_group()
    destinations.add_argument("--output", type=Path, help="global Markdown destination")
    destinations.add_argument("--bundle-dir", type=Path, help="Harbor transport directory")
    parser.add_argument("--runtime", choices=sorted(CODEX_RUNTIMES | {"claude", "cc", "cca", "grok", "ga", "opencode", "oca", "cline", "cla", "cursor", "cu"}))
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
            shutil.copyfile(Path(__file__), args.bundle_dir / "builder.py")
        else:
            destination = args.output or instruction_path(args.runtime, args.config_home)
            if destination.suffix == ".mdc" and not destination.exists():
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text('---\ndescription: "Global agent instructions"\nglobs:\nalwaysApply: true\n---\n\n', encoding="utf-8")
            write_instructions(destination, instructions, owned_keys=owned)
            if args.runtime in CODEX_RUNTIMES:
                ensure_codex_instruction_budget(destination.parent)
        return 0
    except (OSError, ValueError) as exc:
        print(f"global-instructions: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
