#!/usr/bin/env python3
"""Host Docker hygiene and slot lock for Harbor eval jobs.

See ``docker_ipam/cli.py`` for the command list. Default live coding-trial
cap is unset (no LLM cap; Docker IPAM only). Omit Harbor ``-n`` to follow
``-k``. Automatic reclaim is
``prune --keep-builder-cache`` (exited containers, empty networks, unused
trial image tags; BuildKit cache kept). Bare ``prune`` also drops dangling
BuildKit cache when you need disk back.
"""

from docker_ipam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
