#!/usr/bin/env python3
"""Host Docker IPAM hygiene for parallel Harbor eval jobs.

Harbor creates one user-defined bridge per trial, named
``<session>__env_default``. Docker's default local-scope pools hand each of
those a whole ``/16`` (about 30 user-defined networks on the machine). A
dozen ``./run_benchmark.sh … -n 5`` terminals therefore exhaust IPAM
(``all predefined address pools have been fully subnetted``) and crash in
Harbor ``_prepare``.

This helper:

* prunes leftover empty Harbor trial networks (compose down missed them);
* estimates remaining IPAM slots from ``/etc/docker/daemon.json`` or Docker's
  built-in pools;
* holds a cross-process counting semaphore so concurrent wrappers wait
  instead of stampeding.

Stdout is machine-readable (slot counts / JSON). Diagnostics go to stderr.

Usage (from ``evals/``)::

    python3 docker_networks.py self-test
    python3 docker_networks.py prune
    python3 docker_networks.py acquire --slots 5 --holder STAMP --pid $$
    python3 docker_networks.py release --holder STAMP
"""

from __future__ import annotations

import argparse
import fcntl
import ipaddress
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Moby libnetwork/ipamutils local-scope defaults (Engine 28). Each Harbor
# trial consumes one subnet of ``size``.
DEFAULT_ADDRESS_POOLS: tuple[tuple[str, int], ...] = (
    ("172.17.0.0/16", 16),
    ("172.18.0.0/16", 16),
    ("172.19.0.0/16", 16),
    ("172.20.0.0/14", 16),
    ("172.24.0.0/14", 16),
    ("172.28.0.0/14", 16),
    ("192.168.0.0/16", 20),
)

# Same address space, /24 chunks: thousands of trial networks, 254 hosts each.
RECOMMENDED_ADDRESS_POOLS: tuple[tuple[str, int], ...] = (
    ("172.18.0.0/16", 24),
    ("172.19.0.0/16", 24),
    ("172.20.0.0/14", 24),
    ("172.24.0.0/13", 24),
    ("192.168.0.0/16", 24),
)

BUILTIN_NETWORKS = frozenset({"bridge", "host", "none"})
HARBOR_NETWORK_SUFFIX = "__env_default"
DAEMON_JSON_PATH = Path("/etc/docker/daemon.json")
SAFETY_MARGIN = 2
STALE_GRACE_SEC = 60.0
POLL_SEC = 1.0
WAIT_LOG_SEC = 15.0
POOL_EXHAUSTED_NEEDLE = "all predefined address pools have been fully subnetted"


def log(message: str) -> None:
    """Write one helper line to stderr (stdout stays machine-readable).

    Args:
        message: Text with no secrets.
    """
    print(f"docker_networks: {message}", file=sys.stderr, flush=True)


def subnet_count(base: str, size: int) -> int:
    """Return how many ``size``-prefix subnets fit in ``base``.

    Args:
        base: CIDR pool, e.g. ``172.20.0.0/14``.
        size: Child prefix length Docker allocates per network.

    Returns:
        Subnet count, or 0 when ``size`` is narrower than ``base``.
    """
    network = ipaddress.ip_network(base, strict=False)
    if size < network.prefixlen or size > network.max_prefixlen:
        return 0
    return 2 ** (size - network.prefixlen)


def pool_capacity(pools: tuple[tuple[str, int], ...] | list[tuple[str, int]]) -> int:
    """Sum of allocatable networks across IPAM pools.

    Args:
        pools: ``(base, size)`` pairs as in ``default-address-pools``.

    Returns:
        Total child subnets.
    """
    return sum(subnet_count(base, size) for base, size in pools)


def is_harbor_trial_network(name: str) -> bool:
    """Return True when *name* is Harbor's per-trial compose network.

    Args:
        name: Docker network name.
    """
    return name.endswith(HARBOR_NETWORK_SUFFIX)


def is_pool_exhausted_message(text: str) -> bool:
    """Return True when *text* is Docker's IPAM exhaustion error.

    Args:
        text: Exception message or compose log.
    """
    return POOL_EXHAUSTED_NEEDLE in text


def parse_daemon_pools(payload: dict[str, Any] | None) -> tuple[tuple[str, int], ...] | None:
    """Read ``default-address-pools`` from a daemon.json object.

    Args:
        payload: Parsed daemon.json, or None when the file is missing.

    Returns:
        Pool tuples, or None to use Docker's built-in defaults.
    """
    if not payload:
        return None
    raw = payload.get("default-address-pools")
    if not isinstance(raw, list) or not raw:
        return None
    out: list[tuple[str, int]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = item.get("base")
        size = item.get("size")
        if not isinstance(base, str):
            continue
        try:
            size_int = int(size)
        except (TypeError, ValueError):
            continue
        out.append((base, size_int))
    return tuple(out) if out else None


def merge_recommended_daemon_json(existing: dict[str, Any] | None) -> dict[str, Any]:
    """Return daemon.json with recommended pools, preserving other keys.

    Args:
        existing: Current daemon.json object, or None.

    Returns:
        New mapping safe to serialize.
    """
    data = dict(existing) if existing else {}
    data["default-address-pools"] = [
        {"base": base, "size": size} for base, size in RECOMMENDED_ADDRESS_POOLS
    ]
    return data


def slot_dir() -> Path:
    """Directory for the cross-process semaphore files.

    Returns:
        ``$HARBOR_DOCKER_SLOT_DIR`` or ``$XDG_RUNTIME_DIR/…``, else ``/tmp/…``.
    """
    override = os.environ.get("HARBOR_DOCKER_SLOT_DIR", "").strip()
    if override:
        path = Path(override)
        path.mkdir(parents=True, exist_ok=True)
        return path
    runtime = os.environ.get("XDG_RUNTIME_DIR", "").strip()
    base = Path(runtime) if runtime else Path("/tmp")
    path = base / "programming-prompts-harbor-docker"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _lock_path() -> Path:
    return slot_dir() / "slots.lock"


def _state_path() -> Path:
    return slot_dir() / "slots.json"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _load_state(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return {"holders": {}}
    if not isinstance(payload, dict):
        return {"holders": {}}
    holders = payload.get("holders")
    if not isinstance(holders, dict):
        payload["holders"] = {}
    return payload


def _reap_holders(state: dict[str, Any]) -> list[str]:
    """Drop holders whose process is gone. Returns reaped holder ids."""
    holders = state.setdefault("holders", {})
    dead: list[str] = []
    for holder_id, info in list(holders.items()):
        if not isinstance(info, dict):
            dead.append(holder_id)
            continue
        try:
            pid = int(info.get("pid") or 0)
        except (TypeError, ValueError):
            pid = 0
        if not _pid_alive(pid):
            dead.append(holder_id)
    for holder_id in dead:
        holders.pop(holder_id, None)
    return dead


def _with_lock(write: bool = True):
    """Context-manager-like lock using a nested function and try/finally."""

    class _Guard:
        def __enter__(self) -> Any:
            self.fh = _lock_path().open("a+", encoding="utf-8")
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX)
            self.state_path = _state_path()
            text = ""
            if self.state_path.is_file():
                text = self.state_path.read_text(encoding="utf-8")
            self.state = _load_state(text)
            return self.state

        def __exit__(self, *exc: object) -> None:
            try:
                if write:
                    self.state_path.write_text(
                        json.dumps(self.state, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8",
                    )
            finally:
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
                self.fh.close()

    return _Guard()


def reserved_slots(state: dict[str, Any], *, excluding: str = "") -> int:
    """Sum of slots held by live holders.

    Args:
        state: Semaphore JSON.
        excluding: Holder id to skip (the caller).
    """
    total = 0
    for holder_id, info in state.get("holders", {}).items():
        if holder_id == excluding or not isinstance(info, dict):
            continue
        try:
            total += max(0, int(info.get("slots") or 0))
        except (TypeError, ValueError):
            continue
    return total


def network_created_age_sec(created: str, *, now: datetime | None = None) -> float | None:
    """Seconds since Docker's ``Created`` stamp.

    Args:
        created: Inspect ``Created`` value.
        now: Clock override for tests.

    Returns:
        Age in seconds, or None when the stamp cannot be parsed.
    """
    text = created.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    # Docker may emit nanoseconds; datetime accepts microseconds.
    if "." in text:
        head, rest = text.split(".", 1)
        frac = ""
        tz = ""
        for index, char in enumerate(rest):
            if char.isdigit():
                frac += char
            else:
                tz = rest[index:]
                break
        frac = (frac + "000000")[:6]
        text = f"{head}.{frac}{tz}"
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    clock = now or datetime.now(timezone.utc)
    return max(0.0, (clock - stamp.astimezone(timezone.utc)).total_seconds())


def is_stale_harbor_network(
    name: str,
    container_count: int,
    created: str,
    *,
    grace_sec: float = STALE_GRACE_SEC,
    now: datetime | None = None,
) -> bool:
    """Return True when a Harbor trial network is empty and old enough to delete.

    Args:
        name: Docker network name.
        container_count: Attached containers.
        created: Inspect ``Created`` stamp.
        grace_sec: Do not delete networks younger than this (compose-up race).
        now: Clock override for tests.
    """
    if not is_harbor_trial_network(name):
        return False
    if container_count > 0:
        return False
    age = network_created_age_sec(created, now=now)
    if age is None:
        return True
    return age >= grace_sec


def user_defined_capacity(
    pools: tuple[tuple[str, int], ...] | None,
    *,
    docker0_subnet: str | None = "172.17.0.0/16",
) -> int:
    """User-defined networks the daemon can still allocate.

    Args:
        pools: Parsed daemon pools, or None for Docker defaults.
        docker0_subnet: Default-bridge subnet, which consumes one default-pool
            child when it sits inside those pools.

    Returns:
        Capacity excluding the default bridge when it occupies a pool subnet.
    """
    chosen = pools if pools is not None else DEFAULT_ADDRESS_POOLS
    total = pool_capacity(chosen)
    if not docker0_subnet:
        return total
    try:
        bridge = ipaddress.ip_network(docker0_subnet, strict=False)
    except ValueError:
        return total
    for base, size in chosen:
        parent = ipaddress.ip_network(base, strict=False)
        if bridge.version != parent.version:
            continue
        if bridge.prefixlen != size:
            continue
        if bridge.subnet_of(parent) or bridge == parent:
            return max(0, total - 1)
    return total


# --- live Docker (not used by self-test fixtures) ---


def _docker_json(args: list[str]) -> Any:
    import subprocess

    proc = subprocess.run(
        ["docker", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"docker {' '.join(args)} failed: {(proc.stderr or proc.stdout).strip()}"
        )
    text = proc.stdout.strip()
    if not text:
        return None
    return json.loads(text)


def load_daemon_json(path: Path = DAEMON_JSON_PATH) -> dict[str, Any] | None:
    """Read daemon.json when the file exists and is valid JSON.

    Args:
        path: Daemon config path.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        log(f"ignoring invalid JSON in {path}")
        return None
    return payload if isinstance(payload, dict) else None


def list_networks() -> list[dict[str, Any]]:
    """Return Docker network inspect objects (empty list when none)."""
    import subprocess

    proc = subprocess.run(
        ["docker", "network", "ls", "-q"],
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"docker network ls failed: {proc.stderr.strip()}")
    ids = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    if not ids:
        return []
    payload = _docker_json(["network", "inspect", *ids])
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def docker0_subnet(networks: list[dict[str, Any]]) -> str | None:
    """Default-bridge IPv4 subnet from inspect data.

    Args:
        networks: ``docker network inspect`` objects.
    """
    for net in networks:
        if net.get("Name") != "bridge":
            continue
        ipam = net.get("IPAM") or {}
        configs = ipam.get("Config") if isinstance(ipam, dict) else None
        if not isinstance(configs, list):
            return "172.17.0.0/16"
        for item in configs:
            if not isinstance(item, dict):
                continue
            subnet = item.get("Subnet")
            if isinstance(subnet, str) and ":" not in subnet:
                return subnet
        return "172.17.0.0/16"
    return "172.17.0.0/16"


def user_defined_count(networks: list[dict[str, Any]]) -> int:
    """Count non-builtin Docker networks.

    Args:
        networks: Inspect objects.
    """
    return sum(1 for net in networks if net.get("Name") not in BUILTIN_NETWORKS)


def harbor_trial_count(networks: list[dict[str, Any]]) -> int:
    """Count Harbor per-trial compose networks.

    Args:
        networks: Inspect objects.
    """
    return sum(
        1
        for net in networks
        if is_harbor_trial_network(str(net.get("Name") or ""))
    )


def occupied_slots(used: int, harbor_live: int, reserved: int) -> int:
    """Networks that count against IPAM for a new grant.

    Live Harbor nets that are already covered by this semaphore are not
    double-counted. Leftover Harbor nets (no holder) and unrelated
    user-defined nets still consume pool slots.

    Args:
        used: Non-builtin Docker networks.
        harbor_live: Names ending in ``__env_default``.
        reserved: Slots held by live wrapper processes.
    """
    foreign = max(0, used - harbor_live)
    leftovers = max(0, harbor_live - reserved)
    return foreign + reserved + leftovers


def prune_stale_networks(
    networks: list[dict[str, Any]] | None = None,
    *,
    grace_sec: float = STALE_GRACE_SEC,
    dry_run: bool = False,
) -> list[str]:
    """Delete empty Harbor trial networks older than *grace_sec*.

    Args:
        networks: Inspect objects; live Docker when omitted.
        grace_sec: Age gate so compose-up races are not deleted.
        dry_run: When True, only report names.

    Returns:
        Names that were (or would be) removed.
    """
    import subprocess

    nets = list_networks() if networks is None else networks
    now = datetime.now(timezone.utc)
    stale = []
    for net in nets:
        name = str(net.get("Name") or "")
        containers = net.get("Containers")
        count = len(containers) if isinstance(containers, dict) else 0
        created = str(net.get("Created") or "")
        if is_stale_harbor_network(
            name, count, created, grace_sec=grace_sec, now=now
        ):
            stale.append(name)
    removed: list[str] = []
    for name in stale:
        if dry_run:
            removed.append(name)
            continue
        proc = subprocess.run(
            ["docker", "network", "rm", name],
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            removed.append(name)
        else:
            log(f"could not remove {name}: {(proc.stderr or proc.stdout).strip()}")
    if removed:
        log(f"pruned {len(removed)} stale Harbor network(s): {', '.join(removed)}")
    else:
        log("no stale Harbor networks to prune")
    return removed


def current_capacity(*, daemon_path: Path = DAEMON_JSON_PATH) -> dict[str, int]:
    """Live IPAM snapshot: capacity, used, reserved, free.

    Args:
        daemon_path: daemon.json to read for custom pools.
    """
    networks = list_networks()
    pools = parse_daemon_pools(load_daemon_json(daemon_path))
    cap = user_defined_capacity(pools, docker0_subnet=docker0_subnet(networks))
    used = user_defined_count(networks)
    harbor_live = harbor_trial_count(networks)
    with _with_lock(write=True) as state:
        reaped = _reap_holders(state)
        if reaped:
            log(f"reaped {len(reaped)} dead slot holder(s)")
        reserved = reserved_slots(state)
    max_slots = max(1, cap - SAFETY_MARGIN)
    occupied = occupied_slots(used, harbor_live, reserved)
    free = max(0, max_slots - occupied)
    return {
        "capacity": cap,
        "used": used,
        "harbor_live": harbor_live,
        "reserved": reserved,
        "max_slots": max_slots,
        "free": free,
    }


def acquire_slots(
    slots: int,
    holder: str,
    pid: int,
    *,
    timeout_sec: float | None = None,
) -> int:
    """Block until *slots* (or fewer, if clamped) can be reserved.

    Prunes stale Harbor networks first. Clamps the request to ``max_slots``
    when ``-n`` exceeds IPAM. Waits while other wrappers hold the rest.

    Args:
        slots: Requested concurrent Harbor trials (``-n``).
        holder: Stable id for this job (run stamp + job name).
        pid: Owning shell pid; dead pids are reaped.
        timeout_sec: Optional wait limit; None waits indefinitely.

    Returns:
        Granted slot count (stdout of the CLI).
    """
    if slots < 1:
        raise ValueError("--slots must be >= 1")
    if not holder.strip():
        raise ValueError("--holder is required")
    prune_stale_networks()
    started = time.monotonic()
    last_log = 0.0
    while True:
        with _with_lock(write=True) as state:
            reaped = _reap_holders(state)
            if reaped:
                log(f"reaped {len(reaped)} dead slot holder(s)")
            try:
                networks = list_networks()
            except RuntimeError as exc:
                log(str(exc))
                networks = []
            pools = parse_daemon_pools(load_daemon_json())
            cap = user_defined_capacity(
                pools, docker0_subnet=docker0_subnet(networks) if networks else "172.17.0.0/16"
            )
            used = user_defined_count(networks) if networks else 0
            harbor_live = harbor_trial_count(networks) if networks else 0
            max_slots = max(1, cap - SAFETY_MARGIN)
            need = min(slots, max_slots)
            reserved = reserved_slots(state, excluding=holder)
            occupied = occupied_slots(used, harbor_live, reserved)
            free = max(0, max_slots - occupied)
            if need <= free or (
                holder in state["holders"]
                and int(state["holders"][holder].get("slots") or 0) == need
            ):
                state["holders"][holder] = {
                    "pid": pid,
                    "slots": need,
                    "host": socket.gethostname(),
                }
                if need < slots:
                    log(
                        f"clamped -n {slots} → {need} "
                        f"(Docker IPAM max_slots={max_slots} capacity={cap})"
                    )
                log(
                    f"acquired {need} slot(s) for {holder} "
                    f"(free {free - need}/{max_slots} after grant; "
                    f"docker user-defined={used}/{cap})"
                )
                return need
        now = time.monotonic()
        if timeout_sec is not None and now - started >= timeout_sec:
            raise TimeoutError(
                f"timed out waiting for {slots} Docker network slots "
                f"(capacity={cap} used={used} reserved={reserved})"
            )
        if now - last_log >= WAIT_LOG_SEC:
            log(
                f"waiting for {need} Docker network slot(s); "
                f"free={free} max={max_slots} used={used} reserved={reserved}"
            )
            last_log = now
            prune_stale_networks()
        time.sleep(POLL_SEC)


def release_slots(holder: str) -> None:
    """Drop *holder*'s reservation.

    Args:
        holder: Id passed to ``acquire_slots``.
    """
    with _with_lock(write=True) as state:
        info = state.get("holders", {}).pop(holder, None)
    if info:
        log(f"released {info.get('slots')} slot(s) for {holder}")
    else:
        log(f"no slot holder {holder} to release")


def _self_test() -> int:
    """Fixture checks for pool math, stale detection, and the slot file.

    Returns:
        0 when every case passes.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

    record(
        "default_pool_count",
        pool_capacity(DEFAULT_ADDRESS_POOLS) == 31,
        f"got {pool_capacity(DEFAULT_ADDRESS_POOLS)}",
    )
    record(
        "default_user_capacity",
        user_defined_capacity(None) == 30,
        f"got {user_defined_capacity(None)}",
    )
    recommended = pool_capacity(RECOMMENDED_ADDRESS_POOLS)
    record(
        "recommended_pool_count",
        recommended == 3840,
        f"got {recommended}",
    )
    record(
        "recommended_keeps_docker0",
        user_defined_capacity(RECOMMENDED_ADDRESS_POOLS) == 3840,
        "custom /24 pools do not include 172.17.0.0/16",
    )
    record(
        "subnet_count_slash16",
        subnet_count("172.18.0.0/16", 16) == 1,
        "one /16 per /16 pool",
    )
    record(
        "subnet_count_slash24",
        subnet_count("172.18.0.0/16", 24) == 256,
        "256 /24s per /16 pool",
    )
    record(
        "harbor_name",
        is_harbor_trial_network("todo__rj6kp52__env_default"),
        "trial compose network",
    )
    record(
        "not_harbor_bridge",
        not is_harbor_trial_network("bridge"),
        "builtin bridge",
    )
    record(
        "pool_message",
        is_pool_exhausted_message(
            "failed to create network x: " + POOL_EXHAUSTED_NEEDLE
        ),
        "needle match",
    )
    now = datetime(2026, 8, 16, 20, 0, tzinfo=timezone.utc)
    record(
        "stale_empty_old",
        is_stale_harbor_network(
            "calculator__abc__env_default",
            0,
            "2026-08-16T18:17:51.123456789Z",
            now=now,
        ),
        "hours-old leftover",
    )
    record(
        "fresh_empty_kept",
        not is_stale_harbor_network(
            "calculator__abc__env_default",
            0,
            "2026-08-16T19:59:50.000000000Z",
            now=now,
        ),
        "compose-up grace",
    )
    record(
        "busy_kept",
        not is_stale_harbor_network(
            "calculator__abc__env_default",
            1,
            "2026-08-16T18:17:51Z",
            now=now,
        ),
        "container attached",
    )
    merged = merge_recommended_daemon_json({"log-driver": "json-file"})
    record(
        "daemon_merge_preserves",
        merged.get("log-driver") == "json-file"
        and merged["default-address-pools"][0]["size"] == 24,
        "other keys kept; /24 pools set",
    )
    record(
        "parse_empty_daemon",
        parse_daemon_pools({}) is None,
        "missing key → built-in defaults",
    )
    parsed = parse_daemon_pools(merged)
    record(
        "parse_recommended",
        parsed == RECOMMENDED_ADDRESS_POOLS,
        str(parsed),
    )

    import subprocess
    import tempfile

    with tempfile.TemporaryDirectory(prefix="harbor-docker-slots-") as raw:
        os.environ["HARBOR_DOCKER_SLOT_DIR"] = raw
        dead = subprocess.Popen(["true"])
        dead.wait()
        with _with_lock(write=True) as state:
            state["holders"]["gone"] = {"pid": dead.pid, "slots": 3}
            state["holders"]["job-a"] = {"pid": os.getpid(), "slots": 5}
        with _with_lock(write=True) as state:
            reaped = _reap_holders(state)
            record(
                "reap_dead_pid",
                "gone" in reaped and "gone" not in state["holders"],
                f"reaped={reaped}",
            )
        record(
            "reserved_sum",
            reserved_slots(_load_state(_state_path().read_text(encoding="utf-8")))
            == 5,
            "job-a holds 5 after reap",
        )
    record(
        "occupied_leftovers_only",
        occupied_slots(used=8, harbor_live=8, reserved=0) == 8,
        "empty Harbor leftovers still consume the pool",
    )
    record(
        "occupied_reserved_before_compose",
        occupied_slots(used=0, harbor_live=0, reserved=25) == 25,
        "reservations count before networks exist",
    )
    record(
        "occupied_no_double_count",
        occupied_slots(used=25, harbor_live=25, reserved=25) == 25,
        "live Harbor nets already reserved count once",
    )

    failed = [(name, msg) for name, ok, msg in cases if not ok]
    for name, ok, msg in cases:
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {msg}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} docker_networks case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} docker_networks cases passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("self-test", help="Check pool math and stale-network fixtures")
    sub.add_parser("prune", help="Remove empty leftover Harbor trial networks")
    cap = sub.add_parser("capacity", help="Print IPAM snapshot as JSON")
    cap.add_argument(
        "--daemon-json",
        type=Path,
        default=DAEMON_JSON_PATH,
        help="daemon.json path (default: /etc/docker/daemon.json)",
    )

    acq = sub.add_parser("acquire", help="Reserve trial-network slots (blocks)")
    acq.add_argument("--slots", type=int, required=True)
    acq.add_argument("--holder", required=True)
    acq.add_argument("--pid", type=int, default=os.getpid())
    acq.add_argument("--timeout-sec", type=float, default=None)

    rel = sub.add_parser("release", help="Drop a slot reservation")
    rel.add_argument("--holder", required=True)

    rec = sub.add_parser(
        "recommended-daemon-json",
        help="Print daemon.json with /24 pools (merge existing file if present)",
    )
    rec.add_argument(
        "--daemon-json",
        type=Path,
        default=DAEMON_JSON_PATH,
        help="Existing daemon.json to merge (default: /etc/docker/daemon.json)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "self-test":
        return _self_test()
    if args.cmd == "prune":
        names = prune_stale_networks()
        print(len(names))
        return 0
    if args.cmd == "capacity":
        snap = current_capacity(daemon_path=args.daemon_json)
        print(json.dumps(snap, sort_keys=True))
        return 0
    if args.cmd == "acquire":
        try:
            granted = acquire_slots(
                args.slots,
                args.holder,
                args.pid,
                timeout_sec=args.timeout_sec,
            )
        except TimeoutError as exc:
            log(str(exc))
            return 1
        except ValueError as exc:
            log(str(exc))
            return 1
        print(granted)
        return 0
    if args.cmd == "release":
        release_slots(args.holder)
        return 0
    if args.cmd == "recommended-daemon-json":
        merged = merge_recommended_daemon_json(load_daemon_json(args.daemon_json))
        print(json.dumps(merged, indent=2, sort_keys=True))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
