"""Single source of truth for Harbor eval harness metadata.

Kept free of Harbor imports so ``run_benchmark.sh`` can query it with the
system Python. Adding a harness means editing this module, not another
``case`` ladder in the runner.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from harbor_agents.clean_skills import (
    load_claude_version,
    load_codex_version,
    load_grok_version,
)

OauthKind = Literal["none", "claude", "grok"]


@dataclass(frozen=True)
class BindMount:
    """A Docker bind mount relative to the host home directory.

    Attributes:
        source_parts: Path pieces under ``Path.home()``.
        target: Absolute path inside the trial container.
        optional: When True, skip the mount if the host file is missing.
    """

    source_parts: tuple[str, ...]
    target: str
    optional: bool = False


@dataclass(frozen=True)
class HarnessSpec:
    """Metadata for one coding-agent harness.

    Attributes:
        id: Canonical runner id (``codex``, ``cc``, ``grok``).
        aliases: CLI spellings that normalize to ``id``.
        import_path: Harbor ``agents[].import_path``.
        model_name: Default model id for generated job YAML.
        version_file: Pin filename under ``evals/``.
        path_prefixes: Job/trial directory prefixes used in summaries.
        extra_mounts: Agent-auth binds in addition to the Codex judge mount.
        static_env: ``KEY=value`` pairs that contain no secrets.
        oauth: Which secret the runner must inject, if any.
    """

    id: str
    aliases: tuple[str, ...]
    import_path: str
    model_name: str
    version_file: str
    path_prefixes: tuple[str, ...]
    extra_mounts: tuple[BindMount, ...]
    static_env: tuple[str, ...]
    oauth: OauthKind = "none"


# Judges always use Codex (see judges/*/judge.toml).
_JUDGE_CODEX_MOUNT = BindMount(
    source_parts=(".codex", "auth.json"),
    target="/root/.codex/auth.json",
)

HARNESSES: dict[str, HarnessSpec] = {
    "codex": HarnessSpec(
        id="codex",
        aliases=("codex", "openai", "gpt"),
        import_path="harbor_agents.benchmark_codex:BenchmarkCodex",
        model_name="openai/gpt-5.6-luna",
        version_file="codex-version.txt",
        path_prefixes=("codex-",),
        extra_mounts=(),
        static_env=("CODEX_FORCE_AUTH_JSON=true",),
    ),
    "cc": HarnessSpec(
        id="cc",
        aliases=("cc", "claude", "claude-code", "claudecode", "anthropic"),
        import_path="harbor_agents.benchmark_claude_code:BenchmarkClaudeCode",
        model_name="claude-opus-5",
        version_file="claude-version.txt",
        path_prefixes=("cc-", "claude"),
        extra_mounts=(
            BindMount(
                source_parts=(".claude", ".credentials.json"),
                target="/root/.claude/.credentials.json",
            ),
        ),
        static_env=("CLAUDE_FORCE_OAUTH=true",),
        oauth="claude",
    ),
    "grok": HarnessSpec(
        id="grok",
        aliases=("grok", "xai", "grok-build", "grok-code", "grokcli"),
        import_path="harbor_agents.benchmark_grok:BenchmarkGrok",
        model_name="grok-4.6",
        version_file="grok-version.txt",
        path_prefixes=("grok-",),
        extra_mounts=(
            BindMount(
                source_parts=(".grok", "auth.json"),
                target="/root/.grok/auth.json",
                optional=True,
            ),
        ),
        static_env=(),
        oauth="grok",
    ),
}

# Empty / ``both`` stay Codex+Claude so existing commands do not start Grok.
_DEFAULT_GROUP: tuple[str, ...] = ("codex", "cc")
GROUPS: dict[str, tuple[str, ...]] = {
    "": _DEFAULT_GROUP,
    "both": _DEFAULT_GROUP,
    "all": ("codex", "cc", "grok"),
}


def choices_help() -> str:
    """Return the harness names shown in CLI error messages."""
    return "codex, cc, grok, both, or all"


def require_harness(name: str) -> HarnessSpec:
    """Return the spec for *name* or raise ``KeyError``.

    Args:
        name: Canonical harness id.

    Returns:
        The matching :class:`HarnessSpec`.
    """
    spec = HARNESSES.get(name)
    if spec is None:
        raise KeyError(name)
    return spec


def normalize_harness(raw: str) -> tuple[str, ...]:
    """Map a CLI harness argument to one or more canonical ids.

    Args:
        raw: User input such as ``cc``, ``both``, or empty.

    Returns:
        Canonical harness ids in run order.

    Raises:
        ValueError: When *raw* is not a known alias or group.
    """
    key = "".join(raw.lower().split())
    if key in GROUPS:
        return GROUPS[key]
    for spec in HARNESSES.values():
        if key in spec.aliases:
            return (spec.id,)
    raise ValueError(f"Unknown harness '{raw}' (use {choices_help()})")


def identify_harness(*candidates: str) -> str:
    """Infer a canonical harness id from job or trial directory names.

    Args:
        *candidates: Path components such as ``cc-skills__stamp``.

    Returns:
        A harness id, or ``unknown`` when nothing matches.
    """
    for candidate in candidates:
        for spec in HARNESSES.values():
            if any(candidate.startswith(prefix) for prefix in spec.path_prefixes):
                return spec.id
    return "unknown"


def load_cli_version(name: str) -> str:
    """Load the pinned CLI version for *name*.

    Args:
        name: Canonical harness id.

    Returns:
        The stripped version pin.
    """
    spec = require_harness(name)
    loaders = {
        "codex-version.txt": load_codex_version,
        "claude-version.txt": load_claude_version,
        "grok-version.txt": load_grok_version,
    }
    return loaders[spec.version_file]()


def _mount_dict(mount: BindMount, home: Path) -> dict[str, str | bool] | None:
    source = home.joinpath(*mount.source_parts)
    if mount.optional and not source.is_file():
        return None
    return {
        "type": "bind",
        "source": str(source),
        "target": mount.target,
        "read_only": True,
    }


def mounts_json(name: str, home: Path | None = None) -> str:
    """Return Harbor ``--mounts`` JSON for *name*.

    Args:
        name: Canonical harness id.
        home: Host home directory. Defaults to ``Path.home()``.

    Returns:
        A JSON array of bind-mount objects, always including Codex judge auth.
    """
    spec = require_harness(name)
    home = home or Path.home()
    mounts: list[dict[str, str | bool]] = []
    judge = _mount_dict(_JUDGE_CODEX_MOUNT, home)
    if judge is not None:
        mounts.append(judge)
    for extra in spec.extra_mounts:
        item = _mount_dict(extra, home)
        if item is not None:
            mounts.append(item)
    return json.dumps(mounts)


def _cli(argv: list[str]) -> int:
    """Dispatch ``python3 harness_spec.py <command> ...`` for the bash runner."""
    if len(argv) < 2:
        print("usage: harness_spec.py normalize|field|version|mounts|oauth|static-env|choices", file=sys.stderr)
        return 2
    cmd = argv[1]
    try:
        if cmd == "choices":
            print(choices_help(), end="")
            return 0
        if cmd == "normalize":
            raw = argv[2] if len(argv) > 2 else ""
            print("\n".join(normalize_harness(raw)))
            return 0
        if len(argv) < 3:
            raise ValueError(f"{cmd} requires a harness id")
        name = argv[2]
        spec = require_harness(name)
        if cmd == "field":
            field_name = argv[3]
            value = getattr(spec, field_name)
            if isinstance(value, tuple):
                print("\n".join(str(item) for item in value), end="")
            else:
                print(value, end="")
            return 0
        if cmd == "version":
            print(load_cli_version(name), end="")
            return 0
        if cmd == "mounts":
            print(mounts_json(name), end="")
            return 0
        if cmd == "oauth":
            print(spec.oauth, end="")
            return 0
        if cmd == "static-env":
            if spec.static_env:
                print("\n".join(spec.static_env))
            return 0
        print(f"unknown command {cmd!r}", file=sys.stderr)
        return 2
    except KeyError:
        print(f"Internal error: unknown harness '{argv[2] if len(argv) > 2 else ''}'", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv))
