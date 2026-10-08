"""Detect LLM-judge rate-limit / API errors in eval archives."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

# Verifier stdout markers. Do not scan agent trajectories — those can
# mention HTTP 429 without the *judge* having been rate-limited.
# Harbor's wrapper log (21-trial.log) is different: when the *coding*
# agent dies on quota, Harbor writes ApiRateLimitError there. Codex
# workspace-empty errors land in exception.txt as NonZeroAgentExitCodeError
# with "out of credits". Count both as a rate-limit skip, not a skill no.
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
_CODING_QUOTA_NEEDLES = (
    "out of credits",
    "workspace is out of credits",
    "ask your workspace owner to refill",
    "grok build usage balance exhausted",
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


def looks_like_coding_agent_quota(text: str) -> bool:
    """Return whether the coding agent died on empty provider credits.

    Parameters: text - Harbor exception.txt, trial.log, or archived copies.

    Returns: true when a provider refused the trial because its credit balance is empty.
    """
    if not text:
        return False
    lowered = text.lower()
    return any(needle in lowered for needle in _CODING_QUOTA_NEEDLES)


def trial_is_ratelimited(trial_dir: Path) -> bool:
    """Return whether a trial's judge pass was rate-limited.

    Parameters: trial_dir - Harbor trial directory (live or archived).

    Returns: true when reward JSON is flagged or verifier stdout matches.
        A trial that already scored 1.0 is never a skip — Harbor may log
        ApiRateLimitError on a command it then retried successfully.
    """
    print(f"trial_dir={trial_dir}")
    completed = False
    for relative in ("01-reward.json", "verifier/reward.json",
                     "02-reward-details.json", "verifier/reward-details.json"):
        payload = load_json_lenient(trial_dir / relative) or {}
        reward = payload.get("reward")
        try:
            if reward is not None and float(reward) >= 1.0:
                completed = True
        except (TypeError, ValueError):
            pass
        details = reward if isinstance(reward, dict) else payload
        if details.get("ratelimit") is True:
            print(True)
            return True
        error = str(details.get("error") or "").lower()
        if "ratelimit" in error or error in {"rate_limit", "rate-limit"}:
            print(True)
            return True
    if completed:
        print(False)
        return False
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
            print(True)
            return True
    for relative in (
        "exception.txt",
        "20-exception.txt",
        "trial.log",
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
        if "ApiRateLimitError" in text or looks_like_coding_agent_quota(text):
            print(True)
            return True
    print(False)
    return False
