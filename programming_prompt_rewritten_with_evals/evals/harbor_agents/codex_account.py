"""Resolve the ACC-selected ChatGPT Codex home for Harbor trials.

Agent Command Center persists the last ``caN`` / ``catN`` login in
``codex-instances.json``. Harbor must copy ``auth.json`` from that home so
eval jobs use the same ChatGPT account the operator selected.

Components:
  - ``tracker_state_dir`` / ``load_registry``: read ACC's instance file.
  - ``selected_codex_home``: absolute ``CODEX_HOME`` for the selected id.
  - ``selected_codex_auth``: ``auth.json`` under that home.
  - ``self_test``: sandbox checks that do not touch the operator's login.

Usage:
    python3 harbor_agents/codex_account.py          # print selected home
    python3 harbor_agents/codex_account.py --auth   # print auth.json path
    python3 harbor_agents/codex_account.py self-test
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

REGISTRY_NAME = "codex-instances.json"
PRIMARY_ID = 1


def tracker_state_dir(home: Path | None = None) -> Path:
    """Return the ACC tracker state directory that owns the instance registry.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Directory that should contain ``codex-instances.json``.
    """
    override = (os.environ.get("CODEX_AGENT_TRACKER_STATE_DIR") or "").strip()
    if override:
        return Path(override)
    preferred = (os.environ.get("AGENT_COMMAND_CENTER_STATE_DIR") or "").strip()
    if preferred:
        return Path(preferred)
    root = home or Path.home()
    xdg = (os.environ.get("XDG_STATE_HOME") or "").strip()
    if xdg:
        return Path(xdg) / "codex-agent-tracker"
    return root / ".local" / "state" / "codex-agent-tracker"


def load_registry(home: Path | None = None) -> dict:
    """Load ACC's Codex instance registry, or an empty object when missing.

    Parameters: home - optional user home used to locate tracker state.

    Returns: Parsed registry dict. Never raises for a missing file.
    """
    path = tracker_state_dir(home) / REGISTRY_NAME
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return raw if isinstance(raw, dict) else {}


def _instance_rows(registry: dict) -> list[dict]:
    """Return registry instance dicts that have a numeric id."""
    return [
        row
        for row in registry.get("instances") or []
        if isinstance(row, dict) and str(row.get("id", "")).isdigit()
    ]


def selected_instance_id(home: Path | None = None) -> int:
    """Return the persisted ACC Codex instance id.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Selected id, or ``1`` when nothing is registered.
    """
    registry = load_registry(home)
    rows = _instance_rows(registry)
    if not rows:
        return PRIMARY_ID
    try:
        selected = int(registry.get("selected", PRIMARY_ID))
    except (TypeError, ValueError):
        selected = PRIMARY_ID
    by_id = {int(row["id"]): row for row in rows}
    row = by_id.get(selected) or by_id.get(PRIMARY_ID) or rows[0]
    return int(row["id"])


def selected_codex_home(home: Path | None = None) -> Path:
    """Return the Codex home for the persisted ACC instance selection.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Absolute ``CODEX_HOME`` (``~/.codex`` when nothing is registered).
    """
    root = home or Path.home()
    registry = load_registry(root)
    rows = _instance_rows(registry)
    if not rows:
        return root / ".codex"
    selected = selected_instance_id(root)
    by_id = {int(row["id"]): row for row in rows}
    row = by_id.get(selected) or by_id.get(PRIMARY_ID) or rows[0]
    home_value = str(row.get("home") or "").strip()
    if home_value:
        return Path(home_value)
    return root / ".codex"


def selected_codex_auth(home: Path | None = None) -> Path:
    """Return ``auth.json`` under the selected Codex home.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Path to the selected account's ``auth.json``.
    """
    return selected_codex_home(home) / "auth.json"


def selected_codex_auth_parts(home: Path | None = None) -> tuple[str, ...]:
    """Return bind-mount source parts relative to ``home``.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Path parts such as ``('.codex', 'auth.json')`` or
        ``('.codex-account-2', 'auth.json')``. Absolute homes outside
        ``home`` fall back to ``('.codex', 'auth.json')``.
    """
    root = home or Path.home()
    auth = selected_codex_auth(root)
    try:
        rel = auth.relative_to(root)
    except ValueError:
        return (".codex", "auth.json")
    return rel.parts


def harbor_codex_auth_env(home: Path | None = None) -> tuple[str, ...]:
    """Return Harbor env pairs so trials upload the ACC-selected ``auth.json``.

    Harbor's Codex agent honors ``CODEX_AUTH_JSON_PATH`` first. ``CODEX_FORCE_AUTH_JSON``
    alone always copies the host ``~/.codex/auth.json``, which ignores ``cat2``.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Env lines for ``--ae``, including the selected auth path.
    """
    auth = selected_codex_auth(home)
    instance_id = selected_instance_id(home)
    print(
        f"Codex Harbor auth: ACC instance {instance_id} path={auth}",
        file=sys.stderr,
    )
    return (
        "CODEX_FORCE_AUTH_JSON=true",
        f"CODEX_AUTH_JSON_PATH={auth}",
    )


def self_test() -> int:
    """Run sandbox checks for the ACC instance registry reader.

    Parameters: None.

    Returns: 0 when every check passes, 1 otherwise.
    """
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

    previous = os.environ.get("CODEX_AGENT_TRACKER_STATE_DIR")
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "home"
            root.mkdir()
            state = root / ".local" / "state" / "codex-agent-tracker"
            extra = root / ".codex-account-2"
            extra.mkdir(parents=True)
            (extra / "auth.json").write_text("{}", encoding="utf-8")
            os.environ["CODEX_AGENT_TRACKER_STATE_DIR"] = str(state)
            check(
                "missing_registry_defaults",
                selected_codex_home(root) == root / ".codex",
                str(selected_codex_home(root)),
            )
            state.mkdir(parents=True)
            payload = {
                "version": 1,
                "selected": 2,
                "instances": [
                    {"id": 1, "home": str(root / ".codex")},
                    {"id": 2, "home": str(extra), "label": "main"},
                ],
            }
            (state / REGISTRY_NAME).write_text(json.dumps(payload), encoding="utf-8")
            check(
                "selected_home_is_instance_two",
                selected_codex_home(root) == extra,
                str(selected_codex_home(root)),
            )
            check(
                "selected_instance_id_is_two",
                selected_instance_id(root) == 2,
                str(selected_instance_id(root)),
            )
            check(
                "selected_auth_is_instance_two",
                selected_codex_auth(root) == extra / "auth.json",
                str(selected_codex_auth(root)),
            )
            check(
                "mount_parts_use_account_home",
                selected_codex_auth_parts(root) == (".codex-account-2", "auth.json"),
                str(selected_codex_auth_parts(root)),
            )
            env_pairs = harbor_codex_auth_env(root)
            check(
                "harbor_env_points_at_instance_two",
                any(pair.endswith(str(extra / "auth.json")) for pair in env_pairs),
                str(env_pairs),
            )
    finally:
        if previous is None:
            os.environ.pop("CODEX_AGENT_TRACKER_STATE_DIR", None)
        else:
            os.environ["CODEX_AGENT_TRACKER_STATE_DIR"] = previous

    failed = [name for name, ok, _ in cases if not ok]
    for name, ok, detail in cases:
        status = "ok" if ok else "FAIL"
        print(f"{status} {name}: {detail}", file=sys.stderr)
    if failed:
        print(f"{len(failed)}/{len(cases)} codex_account self-test(s) failed", file=sys.stderr)
        return 1
    print(f"{len(cases)}/{len(cases)} codex_account self-tests passed", file=sys.stderr)
    return 0


def _cli(argv: list[str]) -> int:
    """Print the selected Codex home or auth path for Harbor wrappers.

    Parameters: argv - command-line argument vector.

    Returns: Process exit code.
    """
    if len(argv) > 1 and argv[1] in {"-h", "--help"}:
        print("usage: codex_account.py [--auth] | self-test", file=sys.stderr)
        return 0
    if len(argv) > 1 and argv[1] == "self-test":
        return self_test()
    if len(argv) > 1 and argv[1] in {"--auth", "auth"}:
        print(selected_codex_auth())
        return 0
    print(selected_codex_home())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv))
