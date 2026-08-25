#!/usr/bin/env python3
"""Host Docker hygiene and slot lock for Harbor eval jobs.

See ``docker_ipam/cli.py`` for the command list. Default live coding-trial
cap is ``EVAL_LLM_MAX_CONCURRENT=2``. ``prune`` removes leftover Harbor
containers, networks, unused trial images, and dangling BuildKit cache.
"""

from docker_ipam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
