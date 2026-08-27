"""Detect LLM-judge rate-limit / API errors in eval archives."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

# Verifier stdout markers. Do not scan agent trajectories — those can
# mention HTTP 429 without the *judge* having been rate-limited.
# Harbor's wrapper log (21-trial.log) is different: when the *coding*
# agent dies on quota, Harbor writes ApiRateLimitError there. Count
# that as a rate-limit skip, not a skill no.
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
_JUDGE_CLI_NEEDLES = (
    "rewardkit",
    "uvx",
    "agent cli",
    "--judge",
    "pool finished with failures",
)


def looks_like_judge_rate_limit(text: str) -> bool:
    """Return whether verifier/judge output is an API or rate-limit failure.

    Parameters: text - judge stderr/stdout or trial test log.

    Returns: true when a judge CLI error looks like quota/rate-limit, not a scored no.
    """
    if not text:
        return False
    lowered = text.lower()
    if (
        "rate limit" in lowered
        or "rate_limit" in lowered
        or "ratelimit" in lowered
        or "too many requests" in lowered
        or " 429" in lowered
        or "overloaded" in lowered
    ):
        return True
    crashed = (
        "calledprocesserror" in lowered or "exited with code 1" in lowered
    )
    if not crashed:
        return False
    if any(needle in lowered for needle in _JUDGE_CLI_NEEDLES):
        return True
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
    for relative in (
        "21-trial.log",
        "logs/agent/21-trial.log",
    ):
        path = trial_dir / relative
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "ApiRateLimitError" in text:
            return True
    return False
