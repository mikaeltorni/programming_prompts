"""Pure calculations and predicates for Docker IPAM state."""

from __future__ import annotations

import ipaddress
from datetime import datetime, timezone
from typing import Any

from .constants import (
    BUILTIN_NETWORKS,
    DEFAULT_ADDRESS_POOLS,
    HARBOR_NETWORK_SUFFIX,
    POOL_EXHAUSTED_NEEDLE,
    RECOMMENDED_ADDRESS_POOLS,
    STALE_GRACE_SEC,
    WAIT_LOG_SEC,
)


def wait_log_due(now: float, last_log: float, interval: float = WAIT_LOG_SEC) -> bool:
    """Return whether a wait line is due.

    Parameters: now - current monotonic time; last_log - previous wait-line time; interval - minimum spacing in seconds.

    Returns: true when the interval has elapsed.
    """
    return now - last_log >= interval


def subnet_count(base: str, size: int) -> int:
    """Count child subnets in a pool.

    Parameters: base - CIDR pool; size - child prefix length.

    Returns: number of child subnets, or zero for an invalid child size.
    """
    network = ipaddress.ip_network(base, strict=False)
    if size < network.prefixlen or size > network.max_prefixlen:
        return 0
    return 2 ** (size - network.prefixlen)


def pool_capacity(pools: tuple[tuple[str, int], ...] | list[tuple[str, int]]) -> int:
    """Sum allocatable networks across pools.

    Parameters: pools - base and child-size pairs.

    Returns: total child subnet count.
    """
    return sum(subnet_count(base, size) for base, size in pools)


def is_harbor_trial_network(name: str) -> bool:
    """Identify a Harbor trial network name.

    Parameters: name - Docker network name.

    Returns: true when the name has Harbor's trial suffix.
    """
    return name.endswith(HARBOR_NETWORK_SUFFIX)


def is_pool_exhausted_message(text: str) -> bool:
    """Identify Docker's IPAM exhaustion message.

    Parameters: text - exception message or compose log.

    Returns: true when the exhaustion needle is present.
    """
    return POOL_EXHAUSTED_NEEDLE in text


def parse_daemon_pools(
    payload: dict[str, Any] | None,
) -> tuple[tuple[str, int], ...] | None:
    """Parse address pools from daemon configuration.

    Parameters: payload - parsed daemon configuration or none.

    Returns: valid pool tuples, or none to use Docker defaults.
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
    """Merge recommended pools into daemon configuration.

    Parameters: existing - current daemon configuration or none.

    Returns: new mapping preserving unrelated keys.
    """
    data = dict(existing) if existing else {}
    data["default-address-pools"] = [
        {"base": base, "size": size} for base, size in RECOMMENDED_ADDRESS_POOLS
    ]
    return data


def network_created_age_sec(
    created: str, *, now: datetime | None = None
) -> float | None:
    """Calculate a Docker network's age.

    Parameters: created - Docker Created timestamp; now - optional clock override.

    Returns: age in seconds, or none when parsing fails.
    """
    text = created.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
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
    """Identify an empty Harbor network old enough to delete.

    Parameters: name - network name; container_count - attached container count; created - Docker Created timestamp; grace_sec - minimum age; now - optional clock override.

    Returns: true when the network is a stale Harbor trial network.
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
    """Calculate user-defined network capacity.

    Parameters: pools - configured pools or none for defaults; docker0_subnet - default bridge subnet.

    Returns: capacity excluding a default bridge that occupies a pool child.
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


def fair_share_slots(free: int, job_count: int, requested: int) -> tuple[int, int]:
    """Split free IPAM slots across parallel Harbor jobs.

    Parameters: free - currently available slots; job_count - jobs that want
        to run; requested - each job's ``-n`` / ``--n-concurrent``.

    Returns: ``(n_concurrent_per_job, max_parallel_jobs)``. Each running job
        gets the same ``-n``. When there are fewer free slots than jobs, extra
        jobs wait in a worker queue of size ``max_parallel_jobs``.
    """
    if job_count < 1:
        raise ValueError("job_count must be >= 1")
    want = max(1, requested)
    if free < 1:
        return 1, 1
    per_job = max(1, min(want, free // job_count))
    if per_job * job_count > free:
        return 1, max(1, min(job_count, free))
    return per_job, job_count


def occupied_slots(used: int, harbor_live: int, reserved: int) -> int:
    """Calculate pool slots occupied for a new grant.

    Parameters: used - non-builtin networks; harbor_live - Harbor trial networks; reserved - semaphore reservations.

    Returns: occupied slots without double-counting reserved Harbor networks.
    """
    foreign = max(0, used - harbor_live)
    leftovers = max(0, harbor_live - reserved)
    return foreign + reserved + leftovers


def docker0_subnet(networks: list[dict[str, Any]]) -> str | None:
    """Read the default bridge IPv4 subnet.

    Parameters: networks - Docker network inspect objects.

    Returns: bridge subnet or Docker's conventional default.
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

    Parameters: networks - Docker network inspect objects.

    Returns: number of user-defined networks.
    """
    return sum(1 for net in networks if net.get("Name") not in BUILTIN_NETWORKS)


def harbor_trial_count(networks: list[dict[str, Any]]) -> int:
    """Count Harbor trial networks.

    Parameters: networks - Docker network inspect objects.

    Returns: number of Harbor per-trial networks.
    """
    return sum(
        1
        for net in networks
        if is_harbor_trial_network(str(net.get("Name") or ""))
    )
