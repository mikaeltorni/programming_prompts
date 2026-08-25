#!/usr/bin/env python3
"""Host Docker hygiene and slot lock for Harbor eval jobs.

See ``docker_ipam/cli.py`` for the command list. Default live coding-trial
cap is ``EVAL_LLM_MAX_CONCURRENT=2``. Automatic reclaim is ``prune --ipam-only``
(exited containers and empty networks). Bare ``prune`` also drops unused
Harbor trial images and dangling BuildKit cache when you need disk back.
"""

from docker_ipam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
