#!/usr/bin/env python3
"""Compatibility entry: Grok judging is ``run_llm_judge.py --agent grok``.

Harbor and docs still call this file. ``--self-test`` runs the unified suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_llm_judge import main as llm_main


def main(argv: list[str] | None = None) -> int:
    """Forward to the unified LLM judge, defaulting ``--agent grok``."""
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        return llm_main(["--self-test"])
    if "--agent" not in args:
        args = ["--agent", "grok", *args]
    return llm_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
