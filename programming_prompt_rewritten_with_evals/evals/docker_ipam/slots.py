"""Cross-process slot semaphore for parallel Harbor jobs."""

from __future__ import annotations

import fcntl
import json
import os
import socket
import time
from pathlib import Path
from typing import Any

from .constants import (
    DEFAULT_N_WHEN_UNLIMITED,
    LLM_MAX_CONCURRENT_DEFAULT,
    LLM_MAX_CONCURRENT_UNLIMITED,
    POLL_SEC,
    SAFETY_MARGIN,
    WAIT_LOG_SEC,
)
from .log import log
from .math import (
    docker0_subnet,
    grant_trial_slots,
    harbor_trial_count,
    occupied_slots,
    parse_daemon_pools,
    user_defined_capacity,
    user_defined_count,
    wait_log_due,
)


def slot_dir() -> Path:
    """Locate and create the semaphore directory.

    Parameters: none.

    Returns: configured runtime directory for slot files.
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


def lock_path() -> Path:
    """Build the semaphore lock path.

    Parameters: none.

    Returns: lock-file path.
    """
    return slot_dir() / "slots.lock"


def state_path() -> Path:
    """Build the semaphore state path.

    Parameters: none.

    Returns: JSON state-file path.
    """
    return slot_dir() / "slots.json"


def pid_alive(pid: int) -> bool:
    """Check whether a process exists.

    Parameters: pid - process identifier.

    Returns: true when the process can be signaled.
    """
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_state(raw: str) -> dict[str, Any]:
    """Parse semaphore state with safe defaults.

    Parameters: raw - serialized JSON state.

    Returns: mapping containing a holders mapping.
    """
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


def reap_holders(state: dict[str, Any]) -> list[str]:
    """Remove holders whose process is gone.

    Parameters: state - semaphore state mapping.

    Returns: reaped holder identifiers.
    """
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
        if not pid_alive(pid):
            dead.append(holder_id)
    for holder_id in dead:
        holders.pop(holder_id, None)
    return dead


def with_lock(write: bool = True):
    """Create a context manager for locked semaphore state.

    Parameters: write - persist state when leaving the context.

    Returns: context manager yielding the state mapping.
    """

    class _Guard:
        def __enter__(self) -> Any:
            self.fh = lock_path().open("a+", encoding="utf-8")
            fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX)
            self.state_path = state_path()
            text = ""
            if self.state_path.is_file():
                text = self.state_path.read_text(encoding="utf-8")
            self.state = load_state(text)
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
    """Sum slots held by live holders.

    Parameters: state - semaphore state; excluding - holder identifier to skip.

    Returns: total reserved slots.
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


def live_run_stamps() -> set[str]:
    """Run stamps whose wrapper pid is still alive.

    Parameters: none.

    Returns: ``YYYY-MM-DD_HHMMSS_pid`` stamps from live slot holders.
    """
    stamps: set[str] = set()
    with with_lock(write=False) as state:
        for holder_id, info in state.get("holders", {}).items():
            if not isinstance(info, dict):
                continue
            try:
                pid = int(info.get("pid") or 0)
            except (TypeError, ValueError):
                continue
            if pid < 1 or not pid_alive(pid):
                continue
            stamp = str(holder_id).split(":", 1)[0].strip()
            if stamp:
                stamps.add(stamp)
    return stamps


def llm_max_concurrent() -> int:
    """Read the machine-wide coding-trial cap.

    Parameters: none.

    Returns: max live Harbor trials across every wrapper. Unset uses
        ``LLM_MAX_CONCURRENT_DEFAULT`` (one proven ``-k 20`` job). ``0`` or a
        negative ``EVAL_LLM_MAX_CONCURRENT`` disables the cap (IPAM only).
    """
    raw = os.environ.get("EVAL_LLM_MAX_CONCURRENT", "").strip()
    if not raw:
        return LLM_MAX_CONCURRENT_DEFAULT
    try:
        value = int(raw)
    except ValueError:
        log(f"ignoring invalid EVAL_LLM_MAX_CONCURRENT={raw!r}")
        return LLM_MAX_CONCURRENT_DEFAULT
    if value <= 0:
        log("EVAL_LLM_MAX_CONCURRENT<=0: LLM cap disabled")
        return LLM_MAX_CONCURRENT_UNLIMITED
    return value


def default_n_concurrent() -> int:
    """Harbor ``-n`` when the caller omitted the flag.

    Parameters: none.

    Returns: live coding-trial count when neither ``-n`` nor ``-k`` is
        available. Unset ``EVAL_LLM_MAX_CONCURRENT`` follows
        ``LLM_MAX_CONCURRENT_DEFAULT``. Disabled cap (``0``) returns
        ``DEFAULT_N_WHEN_UNLIMITED``; acquire still clamps that to free IPAM.
        Job wrappers prefer following ``-k`` instead of this helper.
    """
    cap = llm_max_concurrent()
    if cap == LLM_MAX_CONCURRENT_UNLIMITED:
        return DEFAULT_N_WHEN_UNLIMITED
    return cap


def _validate_request(slots: int, holder: str) -> None:
    """Validate a slot request.

    Parameters: slots - requested slots; holder - reservation identifier.

    Returns: none.
    """
    if slots < 1:
        raise ValueError("--slots must be >= 1")
    if not holder.strip():
        raise ValueError("--holder is required")


def _capacity_snapshot(
    state: dict[str, Any], holder: str, *, ignore_ipam: bool = False
) -> dict[str, int]:
    """Collect capacity data needed for a grant.

    Parameters: state - locked semaphore state; holder - requesting holder;
        ignore_ipam - skip Docker user-defined-network accounting (trials on
        docker0).

    Returns: capacity and occupancy values.
    """
    from .live import list_networks, load_daemon_json

    reaped = reap_holders(state)
    if reaped:
        log(f"reaped {len(reaped)} dead slot holder(s)")
    reserved = reserved_slots(state, excluding=holder)
    if ignore_ipam:
        return {
            "cap": LLM_MAX_CONCURRENT_UNLIMITED,
            "used": 0,
            "max_slots": LLM_MAX_CONCURRENT_UNLIMITED,
            "reserved": reserved,
            "free": LLM_MAX_CONCURRENT_UNLIMITED,
        }
    try:
        networks = list_networks()
    except RuntimeError as exc:
        log(str(exc))
        networks = []
    pools = parse_daemon_pools(load_daemon_json())
    cap = user_defined_capacity(
        pools,
        docker0_subnet=docker0_subnet(networks)
        if networks
        else "172.17.0.0/16",
    )
    used = user_defined_count(networks) if networks else 0
    harbor_live = harbor_trial_count(networks) if networks else 0
    max_slots = max(1, cap - SAFETY_MARGIN)
    occupied = occupied_slots(used, harbor_live, reserved)
    return {
        "cap": cap,
        "used": used,
        "max_slots": max_slots,
        "reserved": reserved,
        "free": max(0, max_slots - occupied),
    }


def _try_grant(
    state: dict[str, Any],
    requested: int,
    holder: str,
    pid: int,
    snapshot: dict[str, int],
) -> int | None:
    """Try to grant a request under the state lock.

    Parameters: state - locked semaphore state; requested - requested slots; holder - reservation identifier; pid - owning process; snapshot - capacity values.

    Returns: granted slots, or none when capacity is unavailable.
    """
    llm_cap = llm_max_concurrent()
    need = grant_trial_slots(
        requested,
        ipam_free=snapshot["free"],
        ipam_max=snapshot["max_slots"],
        reserved=snapshot["reserved"],
        llm_cap=llm_cap,
    )
    if need is None:
        return None
    already_granted = (
        holder in state["holders"]
        and int(state["holders"][holder].get("slots") or 0) == need
    )
    if already_granted:
        return need
    state["holders"][holder] = {
        "pid": pid,
        "slots": need,
        "host": socket.gethostname(),
    }
    if need < requested:
        log(
            f"clamped -n {requested} → {need} "
            f"(llm_cap={llm_cap} IPAM free={snapshot['free']} "
            f"max_slots={snapshot['max_slots']})"
        )
    if snapshot["cap"] == LLM_MAX_CONCURRENT_UNLIMITED:
        log(
            f"acquired {need} slot(s) for {holder} "
            f"(reserved others={snapshot['reserved']} llm_cap={llm_cap}; "
            "IPAM ignored, trials use docker0)"
        )
    else:
        log(
            f"acquired {need} slot(s) for {holder} "
            f"(reserved others={snapshot['reserved']} llm_cap={llm_cap}; "
            f"docker user-defined={snapshot['used']}/{snapshot['cap']})"
        )
    return need


def _wait_or_timeout(
    requested: int,
    timeout_sec: float | None,
    started: float,
    last_log: float,
    snapshot: dict[str, int],
) -> float:
    """Wait for another grant attempt or raise on timeout.

    Parameters: requested - requested slots; timeout_sec - optional wait limit; started - initial monotonic time; last_log - previous wait log time; snapshot - capacity values.

    Returns: updated previous-log time.
    """
    from .hygiene import reclaim_docker_leftovers

    now = time.monotonic()
    if timeout_sec is not None and now - started >= timeout_sec:
        raise TimeoutError(
            f"timed out waiting for {requested} Docker network slots "
            f"(capacity={snapshot['cap']} used={snapshot['used']} "
            f"reserved={snapshot['reserved']})"
        )
    llm_cap = llm_max_concurrent()
    if wait_log_due(now, last_log):
        log(
            f"waiting for coding-trial slot(s) requested={requested} "
            f"llm_cap={llm_cap} IPAM free={snapshot['free']} "
            f"reserved={snapshot['reserved']}"
        )
        last_log = now
        reclaim_docker_leftovers(images=True, builder_cache=False)
    time.sleep(POLL_SEC)
    return last_log


def acquire_slots(
    slots: int,
    holder: str,
    pid: int,
    *,
    timeout_sec: float | None = None,
    ignore_ipam: bool = False,
) -> int:
    """Reserve coding-trial slots, blocking as needed.

    Parameters: slots - requested concurrent trials; holder - reservation
        identifier; pid - owning process; timeout_sec - optional wait limit;
        ignore_ipam - do not clamp to Docker user-defined-network capacity
        (Harbor trials on docker0).

    Returns: granted slot count.
    """
    from .hygiene import reclaim_docker_leftovers

    _validate_request(slots, holder)
    reclaim_docker_leftovers(images=True, builder_cache=False)
    started = time.monotonic()
    last_log = started - WAIT_LOG_SEC
    snapshot: dict[str, int] = {}
    while True:
        with with_lock(write=True) as state:
            snapshot = _capacity_snapshot(
                state, holder, ignore_ipam=ignore_ipam
            )
            granted = _try_grant(state, slots, holder, pid, snapshot)
            if granted is not None:
                return granted
        last_log = _wait_or_timeout(
            slots, timeout_sec, started, last_log, snapshot
        )


def release_slots(holder: str) -> None:
    """Release a holder's reservation.

    Parameters: holder - identifier passed to acquire_slots.

    Returns: none.
    """
    with with_lock(write=True) as state:
        info = state.get("holders", {}).pop(holder, None)
    if info:
        log(f"released {info.get('slots')} slot(s) for {holder}")
    else:
        log(f"no slot holder {holder} to release")


def release_slots_for_pid(pid: int) -> int:
    """Release every holder owned by *pid*.

    Parameters: pid - process identifier stored at acquire time.

    Returns: number of holders dropped.
    """
    if pid <= 0:
        return 0
    dropped: list[tuple[str, Any]] = []
    with with_lock(write=True) as state:
        holders = state.get("holders", {})
        for holder_id, info in list(holders.items()):
            if not isinstance(info, dict):
                continue
            try:
                owner = int(info.get("pid") or 0)
            except (TypeError, ValueError):
                continue
            if owner == pid:
                dropped.append((holder_id, holders.pop(holder_id)))
    for holder_id, info in dropped:
        log(f"released {info.get('slots')} slot(s) for {holder_id} (pid={pid})")
    return len(dropped)
