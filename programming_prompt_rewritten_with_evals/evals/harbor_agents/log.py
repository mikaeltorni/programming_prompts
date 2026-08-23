"""Stderr diagnostics for harbor_agents CLI helpers.

Stdout stays reserved for machine-readable output (versions, JSON).
"""

from __future__ import annotations

import sys


def log(message: str) -> None:
    """Write one helper line to stderr.

    Args:
        message: Text with no secrets (tokens, keys, file contents).
    """
    print(f"harbor_agents: {message}", file=sys.stderr, flush=True)
