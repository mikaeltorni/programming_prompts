"""Detect judge CLI rate-limit / API errors from rewardkit stderr."""

from __future__ import annotations

import subprocess

# Crashes and timeouts did not score the trial. run_llm_judge treats these
# as rate-limit skips, not a skill no. TimeoutExpired is not a TimeoutError.
JUDGE_CLI_FAILURES: tuple[type[BaseException], ...] = (
    subprocess.CalledProcessError,
    subprocess.TimeoutExpired,
    TimeoutError,
)

_RATE_LIMIT_NEEDLES = (
    '"is_error"',
    "is_error",
    "rate limit",
    "rate_limit",
    "ratelimit",
    "too many requests",
    "overloaded",
    'duration_api_ms":0',
)
_JUDGE_CLI_NEEDLES = (
    "rewardkit",
    "uvx",
    "agent cli",
    "--judge",
    "pool finished with failures",
    "timed out after",
    "timeoutexpired",
)


def looks_like_judge_rate_limit(text: str) -> bool:
    """Return whether judge CLI output is an API or rate-limit failure.

    Parameters: text - rewardkit stderr/stdout.

    Returns: true when the failure is quota/rate-limit, not a scored no.
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
        or "timed out after" in lowered
        or "timeoutexpired" in lowered
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
