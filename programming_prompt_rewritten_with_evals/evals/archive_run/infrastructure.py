"""Recognize incomplete Harbor trials from their final exception."""

from __future__ import annotations

from pathlib import Path

from .fsutil import load_json_lenient

_INFRA_EXCEPTIONS = {
    "AgentTimeoutError": "agent timeout",
    "AgentSetupTimeoutError": "agent setup timeout",
    "EnvironmentStartTimeoutError": "environment start timeout",
}


def trial_infrastructure_failure(trial_dir: Path) -> str | None:
    """Return a known infrastructure failure, or ``None`` for a scored trial.

    Parameters: trial_dir - live Harbor trial or archived ``jobs/*/trials/*``.

    Returns: short failure reason, or None for a scored trial. Prefer the final traceback because
        Harbor may redact unrelated JSON fields into invalid literals.
    """
    print(f"trial_dir={trial_dir}")
    startup_exceptions = []
    # An execution failure is causal even if recovery also wrote a judge error.
    for name in ("exception.txt", "20-exception.txt"):
        try:
            exception_text = (trial_dir / name).read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            continue
        if "harbor.trial.errors.NonZeroAgentExitCodeError:" in exception_text:
            startup_exceptions.append(("NonZeroAgentExitCodeError", exception_text))
        if "OAuth access token has expired" in exception_text:
            reason = "agent authentication expired"
            print(reason)
            return reason
        lines = exception_text.strip().splitlines()
        if not lines:
            continue
        final = lines[-1]
        for exception_type, reason in _INFRA_EXCEPTIONS.items():
            if final.startswith(f"harbor.trial.errors.{exception_type}:"):
                print(reason)
                return reason

    for name in ("result.json", "00-trial-result.json"):
        payload = load_json_lenient(trial_dir / name) or {}
        info = payload.get("exception_info")
        if isinstance(info, dict):
            startup_exceptions.append((str(info.get("exception_type") or ""),
                                       str(info.get("exception_message") or "")))
            reason = _INFRA_EXCEPTIONS.get(str(info.get("exception_type") or ""))
            if reason:
                print(reason)
                return reason
    for exception_type, message in startup_exceptions:
        if (exception_type == "NonZeroAgentExitCodeError"
                and "couldn't set model" in message.casefold()
                and "unknown model id" in message.casefold()):
            reason = "configured agent model unavailable"
            print(reason)
            return reason
    reward_paths = [
        trial_dir / "verifier" / "reward.json", trial_dir / "01-reward.json",
        trial_dir / "03-reward.json", *sorted(trial_dir.glob("03-reward-*.json")),
        trial_dir / "verifier" / "reward-details.json", trial_dir / "02-reward-details.json",
    ]
    for path in reward_paths:
        payload = load_json_lenient(path) or {}
        reward = payload.get("reward")
        details = reward if isinstance(reward, dict) else payload
        if details.get("error") == "judge_inconsistent":
            reason = "judge verdict inconsistent"
            print(reason)
            return reason
    print(None)
    return None
