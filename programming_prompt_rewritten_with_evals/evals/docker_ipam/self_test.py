"""Built-in fixture checks for Docker IPAM behavior."""

import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .constants import (
    DEFAULT_ADDRESS_POOLS,
    POOL_EXHAUSTED_NEEDLE,
    RECOMMENDED_ADDRESS_POOLS,
    WAIT_LOG_SEC,
)
from .math import (
    fair_share_slots,
    is_harbor_trial_network,
    is_pool_exhausted_message,
    is_stale_harbor_network,
    merge_recommended_daemon_json,
    occupied_slots,
    parse_daemon_pools,
    pool_capacity,
    subnet_count,
    user_defined_capacity,
    wait_log_due,
)
from .slots import load_state, reap_holders, release_slots_for_pid, reserved_slots, state_path, with_lock


def _self_test() -> int:
    """Run fixture checks for the extracted package.

    Parameters: none.

    Returns: zero when every case passes.
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

    with tempfile.TemporaryDirectory(prefix="harbor-docker-slots-") as raw:
        os.environ["HARBOR_DOCKER_SLOT_DIR"] = raw
        dead = subprocess.Popen(["true"])
        dead.wait()
        with with_lock(write=True) as state:
            state["holders"]["gone"] = {"pid": dead.pid, "slots": 3}
            state["holders"]["job-a"] = {"pid": os.getpid(), "slots": 5}
        with with_lock(write=True) as state:
            reaped = reap_holders(state)
            record(
                "reap_dead_pid",
                "gone" in reaped and "gone" not in state["holders"],
                f"reaped={reaped}",
            )
        record(
            "reserved_sum",
            reserved_slots(load_state(state_path().read_text(encoding="utf-8")))
            == 5,
            "job-a holds 5 after reap",
        )
        extra = subprocess.Popen(["sleep", "60"])
        try:
            with with_lock(write=True) as state:
                state["holders"]["job-b"] = {"pid": extra.pid, "slots": 2}
                state["holders"]["job-a"] = {"pid": os.getpid(), "slots": 5}
            dropped = release_slots_for_pid(extra.pid)
            record(
                "release_slots_for_pid",
                dropped == 1
                and "job-b"
                not in load_state(state_path().read_text(encoding="utf-8"))["holders"]
                and "job-a"
                in load_state(state_path().read_text(encoding="utf-8"))["holders"],
                f"dropped={dropped}",
            )
        finally:
            extra.terminate()
            extra.wait()
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
    record(
        "wait_log_immediate",
        wait_log_due(100.0, 100.0 - WAIT_LOG_SEC),
        "first wait logs immediately",
    )
    record(
        "wait_log_interval",
        not wait_log_due(100.0 + WAIT_LOG_SEC - 0.1, 100.0),
        "no wait spam inside the interval",
    )
    share_cases = (
        ((18, 4, 5), (4, 4), "four jobs share 18 slots under -n 5"),
        ((18, 4, 2), (2, 4), "do not inflate -n above the request"),
        ((20, 2, 5), (5, 2), "two jobs keep full -n 5"),
        ((3, 4, 5), (1, 3), "queue the fourth job when only 3 slots remain"),
        ((0, 4, 5), (1, 1), "block on a single worker when IPAM is empty"),
        ((5, 1, 5), (5, 1), "one job uses its requested -n"),
        ((5, 5, 5), (1, 5), "one slot each when jobs equal free slots"),
    )
    for (free, jobs, requested), expected, detail in share_cases:
        got = fair_share_slots(free, jobs, requested)
        record(
            f"fair_share_{free}_{jobs}_{requested}",
            got == expected,
            f"{detail}; got {got}",
        )
    share_cli = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve().parents[1] / "docker_networks.py"),
            "fair-share",
            "--jobs",
            "4",
            "--requested",
            "5",
            "--free",
            "18",
        ],
        check=False,
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parents[1]),
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
    )
    record(
        "fair_share_cli",
        share_cli.returncode == 0 and share_cli.stdout.strip() == "4 4 18",
        f"rc={share_cli.returncode} out={share_cli.stdout!r} err={share_cli.stderr!r}",
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
