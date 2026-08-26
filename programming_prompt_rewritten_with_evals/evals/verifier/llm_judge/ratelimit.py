"""Detect judge CLI rate-limit / API errors from rewardkit stderr."""

from __future__ import annotations

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


def looks_like_judge_rate_limit(text: str) -> bool:
    """Return whether judge CLI output is an API or rate-limit failure.

    Parameters: text - rewardkit stderr/stdout.

    Returns: true when the failure is quota/rate-limit, not a scored no.
    """
    if not text:
        return False
    lowered = text.lower()
    if "calledprocesserror" not in lowered and "exited with code 1" not in lowered:
        if "rate limit" not in lowered and "rate_limit" not in lowered:
            if "too many requests" not in lowered and " 429" not in lowered:
                return False
    return any(needle.lower() in lowered for needle in _RATE_LIMIT_NEEDLES)
