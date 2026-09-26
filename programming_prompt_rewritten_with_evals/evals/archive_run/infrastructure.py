"""Recognize incomplete Harbor trials from their final exception."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

_INFRA_EXCEPTIONS = {
    "AgentTimeoutError": "agent timeout",
    "EnvironmentStartTimeoutError": "environment start timeout",
}


def trial_infrastructure_failure(trial_dir: Path) -> str | None:
    """Return a known infrastructure failure, or ``None`` for a scored trial.

    Parameters: trial_dir - live Harbor trial or archived ``jobs/*/trials/*``.

    Returns: short failure reason. The final traceback line is preferred because
        Harbor may redact unrelated JSON fields into invalid literals.
    """
    for name in ("exception.txt", "20-exception.txt"):
        try:
            exception_text = (trial_dir / name).read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            continue
        if "OAuth access token has expired" in exception_text:
            return "agent authentication expired"
        lines = exception_text.strip().splitlines()
        if not lines:
            continue
        final = lines[-1]
        for exception_type, reason in _INFRA_EXCEPTIONS.items():
            if final.startswith(f"harbor.trial.errors.{exception_type}:"):
                return reason

    for name in ("result.json", "00-trial-result.json"):
        payload = load_json_lenient(trial_dir / name) or {}
        info = payload.get("exception_info")
        if isinstance(info, dict):
            reason = _INFRA_EXCEPTIONS.get(str(info.get("exception_type") or ""))
            if reason:
                return reason
    return None
