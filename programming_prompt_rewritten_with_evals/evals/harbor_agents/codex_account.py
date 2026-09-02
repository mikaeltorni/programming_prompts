"""Resolve the ACC-selected ChatGPT Codex home for Harbor trials.

Agent Command Center persists the last ``caN`` login in
``codex-instances.json``. Harbor must copy ``auth.json`` from that home so
eval jobs use the same ChatGPT account the operator selected.

Components:
  - ``tracker_state_dir`` / ``load_registry``: read ACC's instance file.
  - ``selected_codex_home``: absolute ``CODEX_HOME`` for the selected id.
  - ``selected_codex_auth``: ``auth.json`` under that home.
  - ``preflight_codex_account``: reject exhausted accounts before Harbor starts.
  - ``native_codex_env``: keep the probe's ``codex`` child in this terminal.
  - ``self_test``: sandbox checks that do not touch the operator's login.

Usage:
    python3 harbor_agents/codex_account.py          # print selected home
    python3 harbor_agents/codex_account.py --auth   # print auth.json path
    python3 harbor_agents/codex_account.py preflight
    python3 harbor_agents/codex_account.py self-test
"""

from __future__ import annotations

import json
import os
import select
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REGISTRY_NAME = "codex-instances.json"
PRIMARY_ID = 1
# Agent Command Center exports this for a numbered launch (``ca2``) and for
# ``ACC_CODEX_INSTANCE=2 ca``. It overrides the persisted registry selection
# for that process only, so a benchmark inherits the account it was started
# under instead of whichever id ``caN`` last persisted.
INSTANCE_ENV = "ACC_CODEX_INSTANCE"
PREFLIGHT_TIMEOUT_SECONDS = 15.0

# Agent Command Center installs a ``codex`` wrapper on PATH. Every launch that
# is not a ``--help``/``--version`` probe is re-dispatched into a detached tmux
# session with its own terminal window, labeled after the argv - so a plain
# ``codex app-server --stdio`` opens an idle "app server" window instead of
# answering on this process' pipes. These are ACC's own in-place markers: run
# the real binary here, register no agent session, and stay silent. They are
# inert on machines without ACC, so the benchmark keeps running in the terminal
# it was started from.
NATIVE_CODEX_ENV = {
    "AGENT_COMMAND_CENTER_RAW_LAUNCH": "1",
    "CODEX_AGENT_SKIP_TRACKER": "1",
    "ATTS_SUPPRESS_ANNOUNCEMENTS": "1",
}


def native_codex_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Return a child environment that runs ``codex`` in the current terminal.

    Parameters: env - optional base environment; defaults to a copy of
        ``os.environ``. The mapping passed in is never mutated.

    Returns: A new mapping with :data:`NATIVE_CODEX_ENV` applied on top, so an
        ACC-wrapped ``codex`` executes its native binary in place rather than
        spawning a tracked tmux session window.
    """
    merged = dict(os.environ if env is None else env)
    merged.update(NATIVE_CODEX_ENV)
    return merged


def codex_block_reason(rate_limits: dict) -> str | None:
    """Return why a live Codex account snapshot cannot start an eval.

    Parameters: rate_limits - ``rateLimits`` from
        ``account/rateLimits/read``.

    Returns: A stable reason string when the account is blocked, otherwise
        ``None``. Explicit backend reasons take precedence over percentage
        fallbacks so workspace-credit failures are not mislabeled as ordinary
        rolling-window exhaustion.
    """
    reached_type = rate_limits.get("rateLimitReachedType")
    if isinstance(reached_type, str) and reached_type:
        return reached_type
    if rate_limits.get("spendControlReached") is True:
        return "spend control reached"
    for window_name in ("primary", "secondary"):
        window = rate_limits.get(window_name)
        if not isinstance(window, dict):
            continue
        used = window.get("usedPercent")
        if isinstance(used, (int, float)) and used >= 100:
            return f"{window_name} usage window is {used:g}% used"
    individual = rate_limits.get("individualLimit")
    if isinstance(individual, dict) and individual.get("remainingPercent") == 0:
        return "individual spend limit has 0% remaining"
    return None


def _write_app_server_message(process: subprocess.Popen[bytes], message: dict) -> None:
    """Write one newline-delimited JSON request to a Codex app server."""
    if process.stdin is None:
        raise RuntimeError("Codex app-server stdin is unavailable")
    process.stdin.write(json.dumps(message, separators=(",", ":")).encode() + b"\n")
    process.stdin.flush()


def _read_app_server_response(
    process: subprocess.Popen[bytes], request_id: int, timeout: float
) -> dict:
    """Read one matching JSON response without consuming an LLM turn.

    Parameters: process - running Codex app server; request_id - response id;
        timeout - maximum seconds to wait.

    Returns: Parsed response object for ``request_id``.

    Raises: RuntimeError for EOF, protocol errors, or server errors;
        TimeoutError when the endpoint does not answer in time.
    """
    if process.stdout is None:
        raise RuntimeError("Codex app-server stdout is unavailable")
    deadline = time.monotonic() + timeout
    pending = b""
    while True:
        while b"\n" in pending:
            raw_line, pending = pending.split(b"\n", 1)
            if not raw_line.strip():
                continue
            try:
                payload = json.loads(raw_line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
            if payload.get("id") != request_id:
                continue
            if payload.get("error") is not None:
                raise RuntimeError(f"Codex app server returned {payload['error']}")
            return payload

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                f"Codex app server did not answer request {request_id}"
            )
        readable, _, _ = select.select([process.stdout], [], [], remaining)
        if not readable:
            continue
        chunk = os.read(process.stdout.fileno(), 65536)
        if not chunk:
            raise RuntimeError(
                f"Codex app server closed before answering request {request_id}"
            )
        pending += chunk


def read_codex_account_status(
    codex_home: Path | None = None,
    timeout: float = PREFLIGHT_TIMEOUT_SECONDS,
) -> dict:
    """Read the selected account's live limits without starting an LLM turn.

    Parameters: codex_home - optional Codex home; defaults to the ACC-selected
        instance. timeout - maximum seconds per app-server response.

    Returns: Result from Codex's ``account/rateLimits/read`` endpoint.

    Raises: OSError, RuntimeError, or TimeoutError when status cannot be read.
    """
    selected_home = codex_home or selected_codex_home()
    env = native_codex_env()
    env["CODEX_HOME"] = str(selected_home)
    command = [env.get("CODEX_BIN", "codex"), "app-server", "--stdio"]
    print(
        f"Codex account status: probing {command[0]} app-server in this "
        f"terminal home={selected_home}",
        file=sys.stderr,
    )
    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
        bufsize=0,
    )
    try:
        _write_app_server_message(
            process,
            {
                "id": 1,
                "method": "initialize",
                "params": {
                    "clientInfo": {
                        "name": "programming-prompts-eval-preflight",
                        "version": "1",
                    }
                },
            },
        )
        _read_app_server_response(process, 1, timeout)
        _write_app_server_message(process, {"method": "initialized"})
        _write_app_server_message(
            process,
            {"id": 2, "method": "account/rateLimits/read", "params": None},
        )
        response = _read_app_server_response(process, 2, timeout)
        result = response.get("result")
        if not isinstance(result, dict) or not isinstance(
            result.get("rateLimits"), dict
        ):
            raise RuntimeError("Codex account status omitted rateLimits")
        return result
    finally:
        if process.stdin is not None:
            process.stdin.close()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


def preflight_codex_account() -> int:
    """Fail fast when the ACC-selected Codex account cannot run evals.

    Parameters: None.

    Returns: 0 when usable, 1 when blocked, or 2 when status cannot be read.
        This check never consumes reset credits and never switches accounts.
    """
    instance_id = selected_instance_id()
    codex_home = selected_codex_home()
    print(
        f"Codex account preflight: ACC instance {instance_id} path={codex_home}",
        file=sys.stderr,
    )
    try:
        status = read_codex_account_status(codex_home)
    except (OSError, RuntimeError, TimeoutError) as exc:
        print(f"Codex account preflight failed: {exc}", file=sys.stderr)
        print(
            "Refusing to start Harbor without a verified Codex account; "
            "update/login Codex and retry.",
            file=sys.stderr,
        )
        return 2

    limits = status["rateLimits"]
    plan = limits.get("planType") or "unknown"
    primary = limits.get("primary") or {}
    secondary = limits.get("secondary") or {}
    primary_used = primary.get("usedPercent", "n/a")
    secondary_used = secondary.get("usedPercent", "n/a")
    print(
        "Codex account status: "
        f"plan={plan} primary_used={primary_used}% "
        f"secondary_used={secondary_used}%",
        file=sys.stderr,
    )
    reason = codex_block_reason(limits)
    if reason is None:
        print("Codex account preflight: usable", file=sys.stderr)
        return 0

    print(f"Codex account preflight: BLOCKED ({reason})", file=sys.stderr)
    upsell = status.get("rateLimitUpsell")
    if isinstance(upsell, dict) and isinstance(upsell.get("title"), str):
        print(upsell["title"], file=sys.stderr)
    reset_summary = status.get("rateLimitResetCredits")
    if isinstance(reset_summary, dict):
        available = reset_summary.get("availableCount", 0)
        if isinstance(available, int) and available > 0:
            print(
                f"Available rate-limit reset credits: {available} "
                "(not consumed automatically).",
                file=sys.stderr,
            )
    print(
        f"Choose a usable account with {INSTANCE_ENV}=<id> before retrying.",
        file=sys.stderr,
    )
    return 1


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
    """Return the ACC Codex instance id this run must use.

    ``ACC_CODEX_INSTANCE`` wins when set (``ca2`` and
    ``ACC_CODEX_INSTANCE=2 ca`` both export it), matching Agent Command
    Center's own ``resolve_selected_instance``. Otherwise the persisted
    registry selection is used. Without this override a benchmark launched
    from a ``ca2`` shell silently ran on the registry's account 1 - an
    out-of-credits team plan - and every trial scored zero.

    Parameters: home - optional user home; defaults to ``Path.home()``.

    Returns: Selected id, or ``1`` when nothing is registered.

    Raises: ValueError - when ``ACC_CODEX_INSTANCE`` is not a registered id.
        Failing loudly here is deliberate: a silent fallback to the wrong
        account is indistinguishable from a real all-zero benchmark result.
    """
    registry = load_registry(home)
    rows = _instance_rows(registry)
    by_id = {int(row["id"]): row for row in rows}

    raw = (os.environ.get(INSTANCE_ENV) or "").strip()
    if raw:
        try:
            requested = int(raw)
        except ValueError as exc:
            raise ValueError(
                f"{INSTANCE_ENV}={raw!r} is not a Codex instance id"
            ) from exc
        if rows and requested not in by_id:
            known = ", ".join(str(i) for i in sorted(by_id))
            raise ValueError(
                f"{INSTANCE_ENV}={requested} is not a registered Codex "
                f"instance (known ids: {known})"
            )
        return requested

    if not rows:
        return PRIMARY_ID
    try:
        selected = int(registry.get("selected", PRIMARY_ID))
    except (TypeError, ValueError):
        selected = PRIMARY_ID
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
    alone always copies the host ``~/.codex/auth.json``, which ignores ``ca2``.

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


# Stand-in for the ``codex`` CLI used by :func:`self_test`. It mimics the ACC
# wrapper's fork in the road: without the in-place markers it "dispatches" (the
# real wrapper opens a tmux session window and never answers), and with them it
# behaves like ``codex app-server --stdio`` on the inherited pipes.
FAKE_CODEX_CLI = """#!/usr/bin/env python3
import json
import os
import sys

if os.environ.get("AGENT_COMMAND_CENTER_RAW_LAUNCH") != "1":
    with open(os.environ["FAKE_CODEX_DISPATCH_MARKER"], "w") as handle:
        handle.write("dispatched to an ACC session window")
    sys.exit(0)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    message = json.loads(line)
    request_id = message.get("id")
    if request_id == 1:
        reply = {"id": 1, "result": {}}
    elif request_id == 2:
        reply = {"id": 2, "result": {"rateLimits": {"primary": {"usedPercent": 3}}}}
    else:
        continue
    sys.stdout.write(json.dumps(reply) + "\\n")
    sys.stdout.flush()
"""


def self_test() -> int:
    """Run sandbox checks for the ACC instance registry reader.

    Parameters: None.

    Returns: 0 when every check passes, 1 otherwise.
    """
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

    previous = os.environ.get("CODEX_AGENT_TRACKER_STATE_DIR")
    # The self-test is often run from a ``ca2`` shell, which exports
    # ACC_CODEX_INSTANCE. Clear it so the registry-selection checks below
    # assert on the registry, not on the operator's ambient account.
    previous_instance = os.environ.pop(INSTANCE_ENV, None)
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

            # ACC_CODEX_INSTANCE must override the persisted selection the
            # same way Agent Command Center's resolve_selected_instance does.
            payload["selected"] = 1
            (state / REGISTRY_NAME).write_text(json.dumps(payload), encoding="utf-8")
            check(
                "registry_selection_is_one_without_env",
                selected_instance_id(root) == 1,
                str(selected_instance_id(root)),
            )
            os.environ[INSTANCE_ENV] = "2"
            check(
                "env_override_wins_over_registry",
                selected_instance_id(root) == 2,
                str(selected_instance_id(root)),
            )
            check(
                "env_override_moves_auth_to_instance_two",
                selected_codex_auth(root) == extra / "auth.json",
                str(selected_codex_auth(root)),
            )
            check(
                "env_override_moves_harbor_env",
                any(
                    pair.endswith(str(extra / "auth.json"))
                    for pair in harbor_codex_auth_env(root)
                ),
                str(harbor_codex_auth_env(root)),
            )
            os.environ[INSTANCE_ENV] = "9"
            unknown_rejected = False
            try:
                selected_instance_id(root)
            except ValueError:
                unknown_rejected = True
            check(
                "unknown_env_instance_raises",
                unknown_rejected,
                "ValueError raised" if unknown_rejected else "no error raised",
            )
            os.environ[INSTANCE_ENV] = "not-an-id"
            garbage_rejected = False
            try:
                selected_instance_id(root)
            except ValueError:
                garbage_rejected = True
            check(
                "non_numeric_env_instance_raises",
                garbage_rejected,
                "ValueError raised" if garbage_rejected else "no error raised",
            )
            os.environ.pop(INSTANCE_ENV, None)
            check(
                "clearing_env_restores_registry_selection",
                selected_instance_id(root) == 1,
                str(selected_instance_id(root)),
            )

            healthy_limits = {
                "primary": {"usedPercent": 42},
                "secondary": {"usedPercent": 17},
                "spendControlReached": False,
                "rateLimitReachedType": None,
            }
            check(
                "healthy_rate_limits_are_usable",
                codex_block_reason(healthy_limits) is None,
                str(codex_block_reason(healthy_limits)),
            )
            depleted_limits = {
                **healthy_limits,
                "rateLimitReachedType": "workspace_member_credits_depleted",
            }
            check(
                "workspace_credit_depletion_blocks",
                codex_block_reason(depleted_limits)
                == "workspace_member_credits_depleted",
                str(codex_block_reason(depleted_limits)),
            )
            exhausted_window = {
                **healthy_limits,
                "primary": {"usedPercent": 100},
            }
            check(
                "exhausted_primary_window_blocks",
                codex_block_reason(exhausted_window)
                == "primary usage window is 100% used",
                str(codex_block_reason(exhausted_window)),
            )
            spend_control = {
                **healthy_limits,
                "spendControlReached": True,
            }
            check(
                "spend_control_blocks",
                codex_block_reason(spend_control) == "spend control reached",
                str(codex_block_reason(spend_control)),
            )

            # Regression: an ACC-wrapped ``codex`` must not re-dispatch the
            # preflight probe into a tmux session window. The fake CLI records
            # a dispatch when the in-place markers are absent and otherwise
            # answers the two JSON-RPC requests on its pipes.
            markers_seen = dict(native_codex_env({"PATH": "/usr/bin"}))
            check(
                "native_env_sets_in_place_markers",
                all(
                    markers_seen.get(key) == value
                    for key, value in NATIVE_CODEX_ENV.items()
                )
                and markers_seen.get("PATH") == "/usr/bin",
                str(sorted(markers_seen)),
            )
            base_env = {"PATH": "/usr/bin"}
            native_codex_env(base_env)
            check(
                "native_env_does_not_mutate_input",
                base_env == {"PATH": "/usr/bin"},
                str(base_env),
            )

            marker = Path(tmp) / "acc-dispatch.txt"
            fake_codex = Path(tmp) / "fake-codex"
            fake_codex.write_text(FAKE_CODEX_CLI, encoding="utf-8")
            fake_codex.chmod(0o755)
            previous_bin = os.environ.get("CODEX_BIN")
            os.environ["CODEX_BIN"] = str(fake_codex)
            os.environ["FAKE_CODEX_DISPATCH_MARKER"] = str(marker)
            try:
                status = read_codex_account_status(root, timeout=10.0)
            except (OSError, RuntimeError, TimeoutError) as exc:
                status = {"error": str(exc)}
            finally:
                os.environ.pop("FAKE_CODEX_DISPATCH_MARKER", None)
                if previous_bin is None:
                    os.environ.pop("CODEX_BIN", None)
                else:
                    os.environ["CODEX_BIN"] = previous_bin
            check(
                "probe_runs_without_acc_session_window",
                not marker.exists(),
                "dispatched to ACC" if marker.exists() else "ran in place",
            )
            check(
                "probe_reads_rate_limits_over_pipes",
                isinstance(status.get("rateLimits"), dict),
                str(status),
            )
    finally:
        if previous is None:
            os.environ.pop("CODEX_AGENT_TRACKER_STATE_DIR", None)
        else:
            os.environ["CODEX_AGENT_TRACKER_STATE_DIR"] = previous
        if previous_instance is None:
            os.environ.pop(INSTANCE_ENV, None)
        else:
            os.environ[INSTANCE_ENV] = previous_instance

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
    """Inspect or preflight the selected Codex account for Harbor wrappers.

    Parameters: argv - command-line argument vector.

    Returns: Process exit code.
    """
    if len(argv) > 1 and argv[1] in {"-h", "--help"}:
        print(
            "usage: codex_account.py [--auth] | preflight | self-test",
            file=sys.stderr,
        )
        return 0
    if len(argv) > 1 and argv[1] == "self-test":
        return self_test()
    if len(argv) > 1 and argv[1] == "preflight":
        return preflight_codex_account()
    if len(argv) > 1 and argv[1] in {"--auth", "auth"}:
        print(selected_codex_auth())
        return 0
    print(selected_codex_home())
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv))
