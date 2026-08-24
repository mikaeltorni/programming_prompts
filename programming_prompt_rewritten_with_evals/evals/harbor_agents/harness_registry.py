"""Registry and lookup helpers for Harbor coding-agent harnesses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from harbor_agents.clean_skills import (
    load_claude_version,
    load_codex_version,
    load_grok_version,
)

OauthKind = Literal["none", "claude", "grok"]


@dataclass(frozen=True)
class BindMount:
    """A Docker bind mount relative to the host home directory."""

    source_parts: tuple[str, ...]
    target: str
    optional: bool = False


REASONING_EFFORTS: tuple[str, ...] = ("low", "medium", "high")


@dataclass(frozen=True)
class HarnessSpec:
    """Metadata for one coding-agent harness."""

    id: str
    aliases: tuple[str, ...]
    import_path: str
    model_name: str
    eval_backend: str
    eval_model_name: str
    version_file: str
    path_prefixes: tuple[str, ...]
    extra_mounts: tuple[BindMount, ...]
    static_env: tuple[str, ...]
    oauth: OauthKind = "none"


# Codex auth is mounted for every coding harness so a default Codex judge can
# grade. ``mounts_json(*names)`` also unions each harness's extra mounts.
CODEX_AUTH_MOUNT = BindMount(
    source_parts=(".codex", "auth.json"),
    target="/root/.codex/auth.json",
)

HARNESSES: dict[str, HarnessSpec] = {
    "codex": HarnessSpec(
        id="codex",
        aliases=("codex", "openai", "gpt"),
        import_path="harbor_agents.benchmark_codex:BenchmarkCodex",
        model_name="openai/gpt-5.6-luna",
        eval_backend="codex",
        eval_model_name="gpt-5.6-luna",
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
        eval_backend="claude-code",
        eval_model_name="claude-opus-5",
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
        eval_backend="grok",
        eval_model_name="grok-4.6",
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
    """Return the harness names shown in CLI error messages.

    Parameters: None.

    Returns: Harness names formatted for an error message.
    """
    return "codex, cc, grok, both, or all"


def require_harness(name: str) -> HarnessSpec:
    """Return a harness specification or raise ``KeyError``.

    Parameters: name - canonical harness id.

    Returns: Matching harness specification.
    """
    spec = HARNESSES.get(name)
    if spec is None:
        raise KeyError(name)
    return spec


def identify_harness(*candidates: str) -> str:
    """Infer a harness id from job or trial directory names.

    Parameters: candidates - path components such as ``cc-skills__stamp``.

    Returns: Canonical harness id, or ``unknown`` when nothing matches.
    """
    for candidate in candidates:
        for spec in HARNESSES.values():
            if any(candidate.startswith(prefix) for prefix in spec.path_prefixes):
                return spec.id
    return "unknown"


def eval_backend(name: str) -> str:
    """Return the verifier backend for an eval agent.

    Parameters: name - canonical harness id.

    Returns: Verifier backend name.
    """
    return require_harness(name).eval_backend


def load_cli_version(name: str) -> str:
    """Load the pinned CLI version for a harness.

    Parameters: name - canonical harness id.

    Returns: Stripped CLI version pin.
    """
    spec = require_harness(name)
    loaders = {
        "codex-version.txt": load_codex_version,
        "claude-version.txt": load_claude_version,
        "grok-version.txt": load_grok_version,
    }
    return loaders[spec.version_file]()
