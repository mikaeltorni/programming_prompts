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

from docker_ipam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
