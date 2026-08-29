"""Live Docker and daemon-configuration interactions."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import DAEMON_JSON_PATH, SAFETY_MARGIN, STALE_GRACE_SEC
from .log import log
from .math import (
    docker0_subnet,
    harbor_trial_count,
    is_stale_harbor_network,
    occupied_slots,
    parse_daemon_pools,
    user_defined_capacity,
    user_defined_count,
)
from .slots import reap_holders, reserved_slots, with_lock


def docker_json(args: list[str]) -> Any:
    """Run Docker and parse its JSON output.

    Parameters: args - Docker command arguments.

    Returns: parsed JSON, or none for empty output.
    """
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
    """Load valid Docker daemon configuration.

    Parameters: path - daemon configuration path.

    Returns: configuration mapping, or none when missing or invalid.
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
    """Inspect all Docker networks.

    Parameters: none.

    Returns: network inspect mappings, or an empty list.
    """
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
    payload = docker_json(["network", "inspect", *ids])
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _stale_network_names(
    networks: list[dict[str, Any]], grace_sec: float
) -> list[str]:
    """Select stale Harbor networks.

    Parameters: networks - inspect mappings; grace_sec - minimum network age.

    Returns: stale network names.
    """
    now = datetime.now(timezone.utc)
    stale = []
    for net in networks:
        name = str(net.get("Name") or "")
        containers = net.get("Containers")
        count = len(containers) if isinstance(containers, dict) else 0
        created = str(net.get("Created") or "")
        if is_stale_harbor_network(
            name, count, created, grace_sec=grace_sec, now=now
        ):
            stale.append(name)
    return stale


def _remove_networks(names: list[str], dry_run: bool) -> list[str]:
    """Remove selected Docker networks.

    Parameters: names - network names; dry_run - report without removal.

    Returns: names removed or selected in dry-run mode.
    """
    removed: list[str] = []
    for name in names:
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
    return removed


def prune_stale_networks(
    networks: list[dict[str, Any]] | None = None,
    *,
    grace_sec: float = STALE_GRACE_SEC,
    dry_run: bool = False,
) -> list[str]:
    """Delete empty Harbor networks older than the grace period.

    Parameters: networks - inspect mappings or none for live Docker; grace_sec - minimum age; dry_run - report without removal.

    Returns: names removed or selected in dry-run mode.
    """
    nets = list_networks() if networks is None else networks
    removed = _remove_networks(_stale_network_names(nets, grace_sec), dry_run)
    if removed:
        log(f"pruned {len(removed)} stale Harbor network(s): {', '.join(removed)}")
    else:
        log("no stale Harbor networks to prune")
    return removed


def current_capacity(*, daemon_path: Path = DAEMON_JSON_PATH) -> dict[str, int]:
    """Capture live IPAM capacity and use.

    Parameters: daemon_path - daemon configuration path.

    Returns: capacity, usage, reservation, and free-slot values.
    """
    networks = list_networks()
    pools = parse_daemon_pools(load_daemon_json(daemon_path))
    cap = user_defined_capacity(pools, docker0_subnet=docker0_subnet(networks))
    used = user_defined_count(networks)
    harbor_live = harbor_trial_count(networks)
    with with_lock(write=True) as state:
        reaped = reap_holders(state)
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
