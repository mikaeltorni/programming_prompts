#!/usr/bin/env python3
"""Host Docker hygiene and slot lock for Harbor eval jobs.

See ``docker_ipam/cli.py`` for the command list. Default live coding-trial
cap is 20 (one proven ``-k 20`` job). ``EVAL_LLM_MAX_CONCURRENT=0`` disables
it. Trials use Docker's default bridge
(``network_mode: bridge``); omit Harbor ``-n`` to follow ``-k``. Automatic reclaim is
``prune --keep-builder-cache`` (leftover containers including failed
``compose down``, empty networks, unused trial image tags; BuildKit cache
kept). Bare ``prune`` also drops dangling BuildKit cache when you need disk
back.
"""

from docker_ipam.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
