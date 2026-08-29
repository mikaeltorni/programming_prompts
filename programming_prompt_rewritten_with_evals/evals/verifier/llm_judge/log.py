"""Stderr diagnostics for the LLM judge (stdout stays JSON/CLI)."""

from __future__ import annotations

import sys


def log(message: str) -> None:
    """Write one verifier line to stderr.

    Args:
        message: Text with no secrets (tokens, keys, file contents).
    """
    print(f"llm_judge: {message}", file=sys.stderr, flush=True)
