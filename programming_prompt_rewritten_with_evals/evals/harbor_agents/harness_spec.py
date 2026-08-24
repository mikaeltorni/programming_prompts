"""Compatibility API and CLI for Harbor harness metadata.

The registry, normalization, and mount concerns live in sibling modules. This
shim remains executable by path and keeps historical imports working.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from harbor_agents.harness_mounts import _mount_dict, mounts_json
from harbor_agents.harness_normalize import (
    _normalize_one_harness,
    _parse_csv_tokens,
    normalize_eval_agents,
    normalize_harness,
    resolve_eval_efforts,
    resolve_eval_models,
    zip_eval_overrides,
)
from harbor_agents.harness_registry import (
    GROUPS,
    HARNESSES,
    REASONING_EFFORTS,
    BindMount,
    HarnessSpec,
    OauthKind,
    choices_help,
    eval_backend,
    identify_harness,
    load_cli_version,
    require_harness,
)


def _self_test() -> int:
    """Exercise normalization, override zipping, and mount union.

    Parameters: None.

    Returns: Zero when all checks pass, otherwise one.
    """
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
    payload = json.loads(
        mounts_json("cc", "grok", home=Path("/tmp/missing-home"))
    )
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
        print(
            f"{len(failed)}/{len(cases)} harness_spec self-test(s) failed",
            file=sys.stderr,
        )
        return 1
    print(
        f"{len(cases)}/{len(cases)} harness_spec self-tests passed",
        file=sys.stderr,
    )
    return 0


def _cli(argv: list[str]) -> int:
    """Dispatch the compatibility CLI used by the bash runner.

    Parameters: argv - command-line argument vector.

    Returns: Process exit code.
    """
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
        unknown = argv[2] if len(argv) > 2 else ""
        print(f"Internal error: unknown harness '{unknown}'", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv))
