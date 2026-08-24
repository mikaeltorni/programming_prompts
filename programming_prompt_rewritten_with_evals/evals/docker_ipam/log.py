"""Centralized stderr diagnostics for Docker IPAM commands."""

import sys


def log(message: str) -> None:
    """Write one diagnostic line to stderr.

    Parameters: message - text containing no secrets.

    Returns: none.
    """
    print(f"docker_networks: {message}", file=sys.stderr, flush=True)
