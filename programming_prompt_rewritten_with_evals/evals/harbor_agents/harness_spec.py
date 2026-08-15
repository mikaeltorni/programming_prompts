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


REASONING_EFFORTS: tuple[str, ...] = ("low", "medium", "high")


@dataclass(frozen=True)
class HarnessSpec:
    """Metadata for one coding-agent harness.

    Attributes:
        id: Canonical runner id (``codex``, ``cc``, ``grok``).
        aliases: CLI spellings that normalize to ``id``.
        import_path: Harbor ``agents[].import_path``.
        model_name: Default model id for generated job YAML.
        eval_backend: Rewardkit ``--judge`` name, or ``grok`` for the
            verifier's Grok CLI helper (rewardkit has no grok agent).
        eval_model_name: Default model id for the LLM/agent judge.
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
    eval_backend: str
    eval_model_name: str
    version_file: str
    path_prefixes: tuple[str, ...]
    extra_mounts: tuple[BindMount, ...]
    static_env: tuple[str, ...]
    oauth: OauthKind = "none"


# Codex auth is still mounted for every coding harness so a default
# evalAgent=codex (or an explicit mix that includes Codex) can grade.
# ``mounts_json(*names)`` also unions extra_mounts for each named harness.
_CODEX_AUTH_MOUNT = BindMount(
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


def _parse_csv_tokens(raw: str) -> tuple[str, ...]:
    """Split a comma-separated CLI value, dropping empty tokens.

    Args:
        raw: User input such as ``cc,codex`` or ``low``.

    Returns:
        Stripped tokens in order.
    """
    tokens: list[str] = []
    for part in raw.split(","):
        token = "".join(part.lower().split())
        if token:
            tokens.append(token)
    return tuple(tokens)


def _normalize_one_harness(token: str, *, raw: str) -> tuple[str, ...]:
    """Map one token to canonical harness ids (including ``both`` / ``all``).

    Args:
        token: Lowercased, whitespace-stripped token.
        raw: Original user input, used in error messages.

    Returns:
        Canonical harness ids.

    Raises:
        ValueError: When *token* is not a known alias or group.
    """
    if token in GROUPS:
        return GROUPS[token]
    for spec in HARNESSES.values():
        if token in spec.aliases:
            return (spec.id,)
    raise ValueError(f"Unknown harness '{raw}' (use {choices_help()})")


def normalize_harness(raw: str) -> tuple[str, ...]:
    """Map a CLI harness argument to one or more canonical ids.

    Args:
        raw: User input such as ``cc``, ``both``, ``cc,codex``, or empty.

    Returns:
        Canonical harness ids in run order (deduplicated).

    Raises:
        ValueError: When *raw* is not a known alias or group.
    """
    key = "".join(raw.lower().split())
    if key in GROUPS:
        return GROUPS[key]
    tokens = _parse_csv_tokens(raw)
    if not tokens:
        return GROUPS[""]
    ids: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for harness_id in _normalize_one_harness(token, raw=raw):
            if harness_id not in seen:
                ids.append(harness_id)
                seen.add(harness_id)
    return tuple(ids)


def normalize_eval_agents(raw: str) -> tuple[str, ...]:
    """Map an ``evalAgent=`` argument to canonical harness ids.

    Empty input means "inherit the coding harness" and returns ``()``.
    Unlike :func:`normalize_harness`, empty is not ``both``.

    Args:
        raw: User input such as ``cc``, ``cc,codex,grok``, ``all``, or empty.

    Returns:
        Canonical eval-agent ids in the order given, or an empty tuple
        when the caller should use the coding harness.

    Raises:
        ValueError: When a token is not a known alias or group.
    """
    tokens = _parse_csv_tokens(raw)
    if not tokens:
        print("evalAgent omitted: inherit coding harness", file=sys.stderr)
        return ()
    ids: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in GROUPS and token != "":
            mapped = GROUPS[token]
        else:
            mapped = _normalize_one_harness(token, raw=raw)
        for harness_id in mapped:
            if harness_id not in seen:
                ids.append(harness_id)
                seen.add(harness_id)
    print(f"evalAgent resolved to: {', '.join(ids)}", file=sys.stderr)
    return tuple(ids)


def zip_eval_overrides(
    agents: tuple[str, ...],
    raw: str,
    *,
    kind: str,
    defaults: tuple[str, ...],
    allowed: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Align a comma-separated override list with *agents*.

    One value applies to every agent. N values must match N agents.
    Empty *raw* uses *defaults* (one default per agent).

    Args:
        agents: Canonical eval-agent ids.
        raw: User input such as ``low`` or ``low,high``.
        kind: Label for errors (``evalAgentModel`` / ``evalAgentReasoningEffort``).
        defaults: Default value per agent, same length as *agents*.
        allowed: When set, each resolved value must be in this set.

    Returns:
        One resolved value per agent.

    Raises:
        ValueError: On length mismatch or a value not in *allowed*.
    """
    if len(defaults) != len(agents):
        raise ValueError(f"{kind}: internal defaults length mismatch")
    tokens = [part.strip() for part in raw.split(",")] if raw.strip() else []
    tokens = [part for part in tokens if part]
    if allowed is not None:
        tokens = [part.lower() for part in tokens]
    if not tokens:
        values = defaults
    elif len(tokens) == 1:
        values = tuple(tokens[0] for _ in agents)
    elif len(tokens) == len(agents):
        values = tuple(tokens)
    else:
        raise ValueError(
            f"{kind} has {len(tokens)} value(s) but evalAgent has "
            f"{len(agents)} agent(s); use one value or one per agent"
        )
    if allowed is not None:
        for value in values:
            if value not in allowed:
                raise ValueError(
                    f"{kind}={value!r} is not one of {', '.join(allowed)}"
                )
    return values


def resolve_eval_models(agents: tuple[str, ...], raw: str) -> tuple[str, ...]:
    """Return the judge model id for each eval agent.

    Args:
        agents: Canonical eval-agent ids.
        raw: ``evalAgentModel`` CLI value (may be empty).

    Returns:
        One model id per agent.
    """
    defaults = tuple(require_harness(name).eval_model_name for name in agents)
    return zip_eval_overrides(
        agents, raw, kind="evalAgentModel", defaults=defaults
    )


def resolve_eval_efforts(agents: tuple[str, ...], raw: str) -> tuple[str, ...]:
    """Return the judge reasoning effort for each eval agent.

    Args:
        agents: Canonical eval-agent ids.
        raw: ``evalAgentReasoningEffort`` CLI value (may be empty).

    Returns:
        One of ``low``, ``medium``, ``high`` per agent.
    """
    defaults = tuple("low" for _ in agents)
    return zip_eval_overrides(
        agents,
        raw,
        kind="evalAgentReasoningEffort",
        defaults=defaults,
        allowed=REASONING_EFFORTS,
    )


def eval_backend(name: str) -> str:
    """Return the verifier backend name for eval-agent *name*.

    Args:
        name: Canonical harness id.

    Returns:
        ``codex``, ``claude-code``, or ``grok``.
    """
    return require_harness(name).eval_backend


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


def mounts_json(*names: str, home: Path | None = None) -> str:
    """Return Harbor ``--mounts`` JSON for one or more harness ids.

    Unions auth binds for every named harness (coding agent + eval agents)
    and always includes Codex ``auth.json`` so a Codex judge can run.

    Args:
        *names: Canonical harness ids. At least one is required.
        home: Host home directory. Defaults to ``Path.home()``.

    Returns:
        A JSON array of bind-mount objects, de-duplicated by target.

    Raises:
        ValueError: When no harness id is given.
        KeyError: When a name is not a known harness.
    """
    if not names:
        raise ValueError("mounts requires at least one harness id")
    home = home or Path.home()
    mounts: list[dict[str, str | bool]] = []
    seen_targets: set[str] = set()

    def _append(mount: BindMount) -> None:
        item = _mount_dict(mount, home)
        if item is None:
            return
        target = str(item["target"])
        if target in seen_targets:
            return
        seen_targets.add(target)
        mounts.append(item)

    _append(_CODEX_AUTH_MOUNT)
    for name in names:
        spec = require_harness(name)
        for extra in spec.extra_mounts:
            _append(extra)
    return json.dumps(mounts)


def _self_test() -> int:
    """Check eval-agent parsing, model/effort zipping, and mount union."""
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {detail}", file=sys.stderr)

    check(
        "eval_inherit_empty",
        normalize_eval_agents("") == (),
        "empty evalAgent inherits coding harness",
    )
    check(
        "eval_csv_order",
        normalize_eval_agents("cc,codex,grok") == ("cc", "codex", "grok"),
        "comma list keeps order and aliases",
    )
    check(
        "eval_all_group",
        normalize_eval_agents("all") == ("codex", "cc", "grok"),
        "evalAgent=all expands like harness=all",
    )
    check(
        "eval_alias_claude",
        normalize_eval_agents("claude-code") == ("cc",),
        "claude-code alias maps to cc",
    )
    models = resolve_eval_models(("cc", "codex"), "")
    check(
        "eval_model_defaults",
        models == ("claude-opus-5", "gpt-5.6-luna"),
        f"defaults={models}",
    )
    models_one = resolve_eval_models(("cc", "codex"), "claude-opus-5")
    check(
        "eval_model_broadcast",
        models_one == ("claude-opus-5", "claude-opus-5"),
        "one model applies to every eval agent",
    )
    efforts = resolve_eval_efforts(("codex", "cc"), "low,high")
    check(
        "eval_effort_zip",
        efforts == ("low", "high"),
        f"efforts={efforts}",
    )
    unknown_ok = False
    try:
        normalize_eval_agents("not-a-harness")
    except ValueError:
        unknown_ok = True
    check("eval_unknown_rejected", unknown_ok, "unknown evalAgent token errors")
    effort_bad = False
    try:
        resolve_eval_efforts(("codex",), "extreme")
    except ValueError:
        effort_bad = True
    check("eval_effort_rejected", effort_bad, "invalid reasoning effort errors")
    length_bad = False
    try:
        resolve_eval_models(("cc", "codex"), "a,b,c")
    except ValueError:
        length_bad = True
    check(
        "eval_model_length",
        length_bad,
        "model list length must match evalAgent",
    )
    check(
        "eval_backend_cc",
        eval_backend("cc") == "claude-code",
        "cc eval backend is claude-code",
    )
    check(
        "eval_backend_grok",
        eval_backend("grok") == "grok",
        "grok eval backend is the CLI helper",
    )
    payload = json.loads(mounts_json("cc", "grok", home=Path("/tmp/missing-home")))
    targets = [item["target"] for item in payload]
    check(
        "mounts_union",
        "/root/.codex/auth.json" in targets
        and "/root/.claude/.credentials.json" in targets
        and "/root/.grok/auth.json" not in targets,
        f"targets={targets}",
    )
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} harness_spec self-test(s) failed", file=sys.stderr)
        return 1
    print(f"{len(cases)}/{len(cases)} harness_spec self-tests passed", file=sys.stderr)
    return 0


def _cli(argv: list[str]) -> int:
    """Dispatch ``python3 harness_spec.py <command> ...`` for the bash runner."""
    usage = (
        "usage: harness_spec.py normalize|eval-agents|eval-models|"
        "eval-efforts|eval-backend|field|version|mounts|oauth|static-env|"
        "choices|self-test"
    )
    if len(argv) < 2:
        print(usage, file=sys.stderr)
        return 2
    cmd = argv[1]
    try:
        if cmd == "choices":
            print(choices_help(), end="")
            return 0
        if cmd == "self-test":
            return _self_test()
        if cmd == "normalize":
            raw = argv[2] if len(argv) > 2 else ""
            print("\n".join(normalize_harness(raw)))
            return 0
        if cmd == "eval-agents":
            raw = argv[2] if len(argv) > 2 else ""
            agents = normalize_eval_agents(raw)
            if agents:
                print("\n".join(agents))
            return 0
        if cmd == "eval-models":
            agents = tuple(argv[2].split(",")) if len(argv) > 2 and argv[2] else ()
            raw = argv[3] if len(argv) > 3 else ""
            print(",".join(resolve_eval_models(agents, raw)), end="")
            return 0
        if cmd == "eval-efforts":
            agents = tuple(argv[2].split(",")) if len(argv) > 2 and argv[2] else ()
            raw = argv[3] if len(argv) > 3 else ""
            print(",".join(resolve_eval_efforts(agents, raw)), end="")
            return 0
        if cmd == "eval-backend":
            if len(argv) < 3:
                raise ValueError("eval-backend requires a harness id")
            print(eval_backend(argv[2]), end="")
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
            extra = tuple(argv[3:])
            print(mounts_json(name, *extra), end="")
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
