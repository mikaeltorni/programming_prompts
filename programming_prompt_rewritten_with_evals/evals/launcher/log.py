"""Centralized launcher diagnostics."""

from __future__ import annotations

import sys


def log(message: str) -> None:
    """Write one launcher line to stderr.

    Parameters: message - text with no secrets.

    Returns: None.
    """
    print(f"launch_benchmarks: {message}", file=sys.stderr, flush=True)
