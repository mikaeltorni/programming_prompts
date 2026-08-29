"""Build stable archive paths and slugs."""

from __future__ import annotations

import re


def slug(value: str, *, max_len: int = 80) -> str:
    """Convert text to a filesystem-safe slug.

    Parameters: value - text to normalize; max_len - maximum returned length.

    Returns: normalized slug or ``na`` for empty input.
    """
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9._+-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    if not text:
        return "na"
    return text[:max_len]


def _tasks_slug(tasks: list[str]) -> str:
    """Build the task portion of a run directory name.

    Parameters: tasks - requested task names.

    Returns: compact task slug.
    """
    if not tasks or tasks == ["all"]:
        return "all"
    value = "+".join(slug(task) for task in tasks)
    return f"{len(tasks)}-tasks" if len(value) > 60 else value


def build_run_dirname(
    *,
    timestamp: str,
    harnesses: list[str],
    mode: str,
    skills: list[str],
    separately: bool,
    tasks: list[str],
    attempts: int,
    concurrent: int,
    eval_agents: list[str] | None = None,
    extra: str = "",
) -> str:
    """Build a timestamp-sorted run directory name.

    Parameters: timestamp - run timestamp; harnesses - harness names; mode - benchmark mode; skills - evaluated skills; separately - whether skills ran separately; tasks - task names; attempts - attempts per task; concurrent - concurrency limit; eval_agents - judge agents; extra - optional suffix.

    Returns: archive directory name.
    """
    harness_part = "+".join(slug(item) for item in harnesses) or "na"
    skills_part = "+".join(slug(item) for item in skills) or "all"
    eval_part = "+".join(slug(item) for item in eval_agents) if eval_agents else "inherit"
    parts = [
        timestamp,
        f"harness-{harness_part}",
        f"evalagent-{eval_part}",
        f"mode-{slug(mode)}",
        f"skills-{skills_part}",
        f"separately-{'yes' if separately else 'no'}",
        f"tasks-{_tasks_slug(tasks)}",
        f"k{attempts}-n{concurrent}",
    ]
    if extra:
        parts.append(slug(extra))
    return "__".join(parts)
