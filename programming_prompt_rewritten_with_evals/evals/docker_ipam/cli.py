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
import json
import os
from pathlib import Path
from typing import Any

from .constants import DAEMON_JSON_PATH
from .live import (
    current_capacity,
    load_daemon_json,
    prune_stale_networks,
)
from .log import log
from .math import merge_recommended_daemon_json
from .self_test import _self_test
from .slots import acquire_slots, release_slots


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser.

    Parameters: none.

    Returns: configured argument parser.
    """
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
    return parser


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
        print(len(prune_stale_networks()))
        return 0
    if args.cmd == "capacity":
        print(json.dumps(current_capacity(daemon_path=args.daemon_json), sort_keys=True))
        return 0
    if args.cmd == "acquire":
        return _acquire(args)
    if args.cmd == "release":
        release_slots(args.holder)
        return 0
    if args.cmd == "recommended-daemon-json":
        merged = merge_recommended_daemon_json(load_daemon_json(args.daemon_json))
        print(json.dumps(merged, indent=2, sort_keys=True))
        return 0
    return 1
