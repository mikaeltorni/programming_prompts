"""Detect confirmed provider quota failures in eval archives."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

# Verifier stdout markers. Do not scan agent trajectories — those can
# mention HTTP 429 without the *judge* having been rate-limited.
# Harbor's wrapper log (21-trial.log) is different: when the *coding*
# agent dies on quota, Harbor writes ApiRateLimitError there. Codex
# workspace-empty errors land in exception.txt as NonZeroAgentExitCodeError
# with "out of credits". Count both as a rate-limit skip, not a skill no.
from verifier.llm_judge.ratelimit import (
    has_credit_exhaustion, looks_like_judge_rate_limit, parse_provider_output,
)


def looks_like_coding_agent_quota(text: str) -> bool:
    """Parse and classify explicit empty-credit diagnostics from a coding agent.

    Parameters: text - raw Harbor exception or trial output.
    Returns: whether the shared provider classifier reports exhausted credits.
    """
    print(f"text={text}")
    normalized = parse_provider_output(text)
    result = has_credit_exhaustion(normalized)
    print(result)
    return result


def read_verifier_reports(trial_dir: Path) -> list[str]:
    """Read existing verifier reports from the shared live/archive locations.

    Parameters: trial_dir - live or archived Harbor trial directory.
    Returns: available verifier report texts, without classifying their contents.
    """
    print(f"trial_dir={trial_dir}")
    result = []
    for relative in (
        "10-test-stdout.txt", "verifier/10-test-stdout.txt",
        "verifier/test-stdout.txt", "logs/verifier/test-stdout.txt",
    ):
        try:
            result.append((trial_dir / relative).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    print(result)
    return result


def parse_archive_reward(payload: dict) -> float | None:
    """Convert an archived scalar reward without interpreting completion.

    Parameters: payload - decoded reward or metadata object.
    Returns: converted scalar reward, or None when the object has no numeric reward.
    """
    print(f"payload={payload}")
    try:
        result = float(payload.get("reward"))
    except (TypeError, ValueError):
        result = None
    print(result)
    return result


def is_completed_reward(score: float | None) -> bool:
    """Classify a converted completed reward for every archive failure route.

    Parameters: score - converted reward or None when unavailable.
    Returns: whether the reward establishes successful completion.
    """
    print(f"score={score}")
    result = score is not None and score >= 1.0
    print(result)
    return result


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
        score = parse_archive_reward(payload)
        completed = completed or is_completed_reward(score)
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
    for text in read_verifier_reports(trial_dir):
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
