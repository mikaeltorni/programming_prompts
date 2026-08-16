"""Detect skip-inspect / invented-path scores and retry once.

Shared by every eval agent so Codex, Claude Code, and Grok apply the same
reliability gate. The retry token never includes secrets or file contents.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.log import log

MIN_RETRY_SECONDS = 40
_NOT_INSPECTED = re.compile(
    r"not inspected|withheld until|have not yet(?:\s+\w+){0,8}\s+inspect"
    r"|have not inspected|until the workspace python is inspected"
    r"|scoring is withheld|have not yet verified"
    r"|without (?:an? )?actual file",
    re.IGNORECASE,
)
_PY_MENTION = re.compile(
    r"(?:(?:\.{0,2}/)?[\w.-]+(?:/[\w.-]+)*)\.py",
    re.IGNORECASE,
)

AttemptFn = Callable[[str | None, int], tuple[str, list[dict[str, Any]]]]


def mentioned_python_paths(reasoning: str) -> list[str]:
    """Return ``.py`` paths cited in judge reasoning.

    Args:
        reasoning: Free-text ``reasoning`` field from an eval agent.

    Returns:
        Path-like strings in mention order (trailing punctuation stripped).
    """
    found: list[str] = []
    for match in _PY_MENTION.findall(reasoning):
        cleaned = match.rstrip(")'\".,;:")
        if cleaned:
            found.append(cleaned)
    return found


def _path_is_listed(mentioned: str, keys: set[str]) -> bool:
    """Return True when *mentioned* matches a listed workspace Python file."""
    text = mentioned.strip().lower()
    if text in keys:
        return True
    return Path(text).name.lower() in keys


def unreliable_score_reason(
    rows: list[dict[str, Any]], listed_keys: set[str]
) -> str | None:
    """Return why a failing score looks untrustworthy, or None.

    Triggers on skip-inspect wording or ``.py`` citations that are not in
    the workspace listing. Passing criteria are ignored.

    Args:
        rows: Parsed criterion scores.
        listed_keys: Lowercased names from ``listed_python_keys``.

    Returns:
        ``not_inspected:<criterion>`` or ``wrong_path:<criterion>:<file>``.
    """
    for row in rows:
        if float(row["reward"]) >= 1.0:
            continue
        reasoning = str(row.get("reasoning") or "")
        name = str(row["name"])
        if _NOT_INSPECTED.search(reasoning):
            return f"not_inspected:{name}"
        mentioned = mentioned_python_paths(reasoning)
        if not mentioned:
            continue
        if any(_path_is_listed(item, listed_keys) for item in mentioned):
            continue
        return f"wrong_path:{name}:{Path(mentioned[0]).name}"
    return None


def retry_prompt(prompt: str, reason: str) -> str:
    """Append a one-shot correction after an unusable first score.

    Args:
        prompt: Original judge prompt (files already listed).
        reason: Short token from :func:`unreliable_score_reason` (no secrets).

    Returns:
        Prompt text for the retry attempt.
    """
    return (
        prompt
        + "\n\nRETRY: the previous JSON score was unusable "
        + f"({reason}). Score ONLY the Python files listed above. "
        + "Do not invent app.py. Do not answer no because you have not "
        + "inspected — the source is in this prompt.\n"
    )


def run_until_reliable(
    *,
    listed_keys: set[str],
    timeout: int,
    attempt: AttemptFn,
) -> tuple[str, list[dict[str, Any]]]:
    """Run one judge attempt, then retry once on skip-inspect or invented paths.

    Args:
        listed_keys: Allowed ``.py`` citations from ``listed_python_keys``.
        timeout: Wall budget in seconds for both attempts combined.
        attempt: ``attempt(retry_reason_or_None, timeout_s) -> (raw, rows)``.
            First call uses ``reason=None`` and the full *timeout*. The retry
            call receives the reason token and remaining seconds.

    Returns:
        Raw stdout and parsed rows from the last attempt used.
    """
    started = time.monotonic()
    raw, rows = attempt(None, timeout)
    reason = unreliable_score_reason(rows, listed_keys)
    if reason is None:
        return raw, rows
    remaining = timeout - (time.monotonic() - started) - 5
    if remaining < MIN_RETRY_SECONDS:
        log(
            f"skip retry reason={reason} remaining_s={remaining:.0f} "
            f"min_s={MIN_RETRY_SECONDS}"
        )
        return raw, rows
    log(f"retrying judge once reason={reason} remaining_s={remaining:.0f}")
    raw_retry, rows_retry = attempt(reason, int(remaining))
    second = unreliable_score_reason(rows_retry, listed_keys)
    if second:
        log(f"retry still unreliable reason={second}")
    else:
        log("retry produced a usable score")
    return raw_retry, rows_retry
