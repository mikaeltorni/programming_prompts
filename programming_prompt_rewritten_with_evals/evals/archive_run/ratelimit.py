"""Detect LLM-judge rate-limit / API errors in eval archives."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

# Verifier stdout markers. Do not scan agent trajectories — those can
# mention HTTP 429 without the *judge* having been rate-limited.
_RATE_LIMIT_NEEDLES = (
    '"is_error"',
    "is_error",
    "rate limit",
    "rate_limit",
    "ratelimit",
    "too many requests",
    "overloaded",
    'duration_api_ms":0',
    "duration_api_ms\":0",
)


def looks_like_judge_rate_limit(text: str) -> bool:
    """Return whether verifier/judge output is an API or rate-limit failure.

    Parameters: text - judge stderr/stdout or trial test log.

    Returns: true when a judge CLI error looks like quota/rate-limit, not a scored no.
    """
    if not text:
        return False
    lowered = text.lower()
    if "calledprocesserror" not in lowered and "exited with code 1" not in lowered:
        if "rate limit" not in lowered and "rate_limit" not in lowered:
            if "too many requests" not in lowered and " 429" not in lowered:
                return False
    return any(needle.lower() in lowered for needle in _RATE_LIMIT_NEEDLES)


def trial_is_ratelimited(trial_dir: Path) -> bool:
    """Return whether a trial's judge pass was rate-limited.

    Parameters: trial_dir - Harbor trial directory (live or archived).

    Returns: true when reward JSON is flagged or verifier stdout matches.
    """
    for relative in ("01-reward.json", "verifier/reward.json"):
        payload = load_json_lenient(trial_dir / relative) or {}
        if payload.get("ratelimit") is True:
            return True
        error = str(payload.get("error") or "").lower()
        if "ratelimit" in error or error in {"rate_limit", "rate-limit"}:
            return True
    for relative in (
        "10-test-stdout.txt",
        "verifier/10-test-stdout.txt",
        "verifier/test-stdout.txt",
        "logs/verifier/test-stdout.txt",
    ):
        path = trial_dir / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if looks_like_judge_rate_limit(text):
            return True
    return False
