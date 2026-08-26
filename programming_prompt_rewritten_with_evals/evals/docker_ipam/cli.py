"""Host Docker IPAM hygiene for parallel Harbor eval jobs.

Harbor creates one user-defined bridge per trial, named
``<session>__env_default``. Docker's default local-scope pools hand each of
those a whole ``/16`` (about 30 user-defined networks on the machine). A
dozen ``./run_benchmark.sh … -n 5`` terminals therefore exhaust IPAM
(``all predefined address pools have been fully subnetted``) and crash in
Harbor ``_prepare``.

This helper:

* prunes leftover Harbor trial containers, empty networks, and unused
  ``*__env-main`` image tags between jobs (``prune --keep-builder-cache``)
  so disk does not grow with every trial; BuildKit cache stays so the next
  job does not rebuild. Bare ``prune`` also drops dangling BuildKit cache
  when you need more disk;
* caps live coding trials machine-wide (default ``EVAL_LLM_MAX_CONCURRENT=10``)
  so ``-n 10`` is not clamped to two; set ``EVAL_LLM_MAX_CONCURRENT=2`` to
  restore the old quota-safe cap;
* estimates remaining IPAM slots from ``/etc/docker/daemon.json`` or Docker's
  built-in pools;
* holds a cross-process counting semaphore so concurrent wrappers wait
  instead of stampeding.

Stdout is machine-readable (slot counts / JSON). Diagnostics go to stderr.

Usage (from ``evals/``)::

    python3 docker_networks.py self-test
    python3 docker_networks.py prune --ipam-only
    python3 docker_networks.py prune
    python3 docker_networks.py acquire --slots 5 --holder STAMP --pid $$
    python3 docker_networks.py release --holder STAMP
    python3 docker_networks.py release --pid $$
    python3 docker_networks.py fair-share --jobs 4 --requested 5
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from .constants import DAEMON_JSON_PATH
from .hygiene import reclaim_docker_leftovers
from .live import (
    current_capacity,
    load_daemon_json,
)
from .log import log
from .math import fair_share_slots, merge_recommended_daemon_json
from .self_test import _self_test
from .slots import acquire_slots, release_slots, release_slots_for_pid


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Parameters: none.

    Returns: configured argument parser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("self-test", help="Check pool math and stale-network fixtures")
    prune = sub.add_parser(
        "prune",
        help="Remove leftover Harbor Docker state (full disk reclaim unless --ipam-only)",
    )
    prune.add_argument(
        "--ipam-only",
        action="store_true",
        help="Drop exited containers and empty networks only; keep images and BuildKit cache",
    )
    prune.add_argument(
        "--keep-builder-cache",
        action="store_true",
        help="Also drop unused Harbor trial image tags; keep BuildKit cache so the next job does not rebuild",
    )
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
    rel.add_argument("--holder", default="", help="Holder id passed to acquire")
    rel.add_argument("--pid", type=int, default=0, help="Drop every holder owned by this pid")

    share = sub.add_parser(
        "fair-share",
        help="Split free IPAM slots across parallel Harbor jobs (stdout: n workers free)",
    )
    share.add_argument("--jobs", type=int, required=True, help="How many Harbor jobs want to run")
    share.add_argument(
        "--requested",
        type=int,
        required=True,
        help="Each job's requested -n / --n-concurrent",
    )
    share.add_argument(
        "--free",
        type=int,
        default=None,
        help="Override live free-slot count (default: query Docker IPAM)",
    )

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
    return parser


def _fair_share(args: Any) -> int:
    """Print a uniform -n and worker-pool size for parallel Harbor jobs.

    Parameters: args - parsed fair-share arguments.

    Returns: process exit status.
    """
    try:
        free = args.free if args.free is not None else current_capacity()["free"]
        n_concurrent, workers = fair_share_slots(free, args.jobs, args.requested)
    except (RuntimeError, ValueError) as exc:
        log(str(exc))
        return 1
    log(
        f"fair-share jobs={args.jobs} requested={args.requested} "
        f"free={free} → -n {n_concurrent} workers={workers}"
    )
    print(f"{n_concurrent} {workers} {free}")
    return 0


def _acquire(args: Any) -> int:
    """Run the acquire command.

    Parameters: args - parsed command arguments.

    Returns: process exit status.
    """
    try:
        granted = acquire_slots(
            args.slots,
            args.holder,
            args.pid,
            timeout_sec=args.timeout_sec,
        )
    except (TimeoutError, ValueError) as exc:
        log(str(exc))
        return 1
    print(granted)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Dispatch a Docker IPAM command.

    Parameters: argv - optional command arguments.

    Returns: process exit status.
    """
    args = _build_parser().parse_args(argv)
    if args.cmd == "self-test":
        return _self_test()
    if args.cmd == "prune":
        counts = reclaim_docker_leftovers(
            images=not args.ipam_only,
            builder_cache=not args.ipam_only and not args.keep_builder_cache,
        )
        print(json.dumps(counts, sort_keys=True))
        return 0
    if args.cmd == "capacity":
        print(json.dumps(current_capacity(daemon_path=args.daemon_json), sort_keys=True))
        return 0
    if args.cmd == "fair-share":
        return _fair_share(args)
    if args.cmd == "acquire":
        return _acquire(args)
    if args.cmd == "release":
        if args.holder:
            release_slots(args.holder)
            return 0
        if args.pid:
            release_slots_for_pid(args.pid)
            return 0
        log("release requires --holder or --pid")
        return 1
    if args.cmd == "recommended-daemon-json":
        merged = merge_recommended_daemon_json(load_daemon_json(args.daemon_json))
        print(json.dumps(merged, indent=2, sort_keys=True))
        return 0
    return 1
