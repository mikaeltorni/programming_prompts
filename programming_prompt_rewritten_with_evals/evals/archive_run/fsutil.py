"""Provide filesystem and lenient JSON helpers."""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path


def _repair_redacted_reward(text: str) -> str:
    """Repair Harbor's unquoted redacted reward marker.

    Parameters: text - raw JSON text.

    Returns: JSON-compatible text.
    """
    if "[REDACTED]" not in text:
        return text
    return re.sub(
        r'("reward"\s*:\s*)\[REDACTED\](\.0\b)?',
        lambda match: f"{match.group(1)}1{match.group(2) or ''}",
        text,
    )


def load_json_lenient(path: Path) -> dict | None:
    """Load a JSON object while tolerating redacted rewards.

    Parameters: path - JSON file to read.

    Returns: decoded object, or ``None`` when unreadable or invalid.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(_repair_redacted_reward(text))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def copy_file(src: Path, dest: Path) -> None:
    """Copy a file while creating its destination directory.

    Parameters: src - source file; dest - destination file.

    Returns: nothing.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def copy_tree(src: Path, dest: Path) -> None:
    """Copy a directory tree, replacing the destination.

    Parameters: src - source directory; dest - destination directory.

    Returns: nothing.
    """
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=True, ignore_dangling_symlinks=True)


def write_json(path: Path, payload: object) -> None:
    """Write deterministic, indented JSON.

    Parameters: path - destination file; payload - JSON-compatible value.

    Returns: nothing.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def log(message: str) -> None:
    """Write an archive diagnostic to stderr.

    Parameters: message - diagnostic text.

    Returns: nothing.
    """
    print(f"archive: {message}", file=sys.stderr, flush=True)
