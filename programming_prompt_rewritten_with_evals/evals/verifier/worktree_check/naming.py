"""Validate worktree directory and branch names against the layout contract.

The worktree skill fixes two names for every task: the worktree directory leaf
``<instance>_<type>-<feature>`` and its branch ``<type>/<instance>_<feature>``.
Both encode the same three components, so this module parses each name into a
:class:`WorktreeName` and reports every component that is missing, malformed, or
inconsistent between the two. ``runtime_instances`` resolves which instance
identifiers an agent home may legitimately produce.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

INSTANCE_FALLBACK = "agent"
HOME_ENV_VARS = ("CLAUDE_CONFIG_DIR", "CODEX_HOME", "AGENT_HOME")
_DISALLOWED = re.compile(r"[^A-Za-z0-9_-]")


@dataclass(frozen=True)
class WorktreeName:
    """Hold the three components shared by a worktree leaf and its branch.

    Parameters: instance - agent home identifier; kind - conventional commit
    type; feature - descriptive task slug.

    Returns: immutable parsed name.
    """

    instance: str
    kind: str
    feature: str


def sanitize_instance(raw: str) -> str:
    """Reduce an agent home name to its branch-safe instance identifier.

    Strips leading dots and replaces every character outside letters, digits,
    hyphens, and underscores, matching the skill's sanitization rule.

    Parameters: raw - agent home basename.

    Returns: sanitized instance, or the documented fallback when nothing remains.
    """
    cleaned = _DISALLOWED.sub("-", raw.lstrip("."))
    return cleaned or INSTANCE_FALLBACK


def runtime_instances(env: dict[str, str] | None = None) -> set[str] | None:
    """Resolve the instance identifiers the current agent home may use.

    Parameters: env - environment mapping to inspect; defaults to the process
    environment.

    Returns: accepted instance names, or None when no agent home is
    discoverable and any well-formed instance must be accepted.
    """
    source = os.environ if env is None else env
    names = {
        sanitize_instance(Path(value).name)
        for var in HOME_ENV_VARS
        if (value := source.get(var, "").strip())
    }
    if not names:
        return None
    names.add(INSTANCE_FALLBACK)
    return names


def _split_instance(text: str, known: set[str] | None) -> tuple[str, str] | None:
    """Separate an instance prefix from the remainder of a name.

    Prefers a known instance that underscores would otherwise split, then falls
    back to the first underscore.

    Parameters: text - ``<instance>_<rest>`` fragment; known - accepted instance
    names, if any.

    Returns: instance and remainder, or None when no underscore separates them.
    """
    for candidate in sorted(known or (), key=len, reverse=True):
        prefix = f"{candidate}_"
        if text.startswith(prefix) and text[len(prefix):]:
            return candidate, text[len(prefix):]
    instance, sep, rest = text.partition("_")
    if not sep or not instance or not rest:
        return None
    return instance, rest


def parse_leaf(leaf: str, known: set[str] | None = None) -> WorktreeName | None:
    """Parse a worktree directory leaf.

    Parameters: leaf - directory basename; known - accepted instance names.

    Returns: parsed components, or None when the leaf is not
    ``<instance>_<type>-<feature>``.
    """
    split = _split_instance(leaf, known)
    if split is None:
        return None
    instance, rest = split
    kind, sep, feature = rest.partition("-")
    if not sep or not kind or not feature:
        return None
    return WorktreeName(instance, kind, feature)


def parse_branch(branch: str, known: set[str] | None = None) -> WorktreeName | None:
    """Parse a task branch name.

    Parameters: branch - short or ``refs/heads`` branch name; known - accepted
    instance names.

    Returns: parsed components, or None when the branch is not
    ``<type>/<instance>_<feature>``.
    """
    short = branch.removeprefix("refs/heads/")
    kind, sep, rest = short.partition("/")
    if not sep or not kind or not rest or "/" in rest:
        return None
    split = _split_instance(rest, known)
    if split is None:
        return None
    instance, feature = split
    return WorktreeName(instance, kind, feature)


def check_names(
    leaf: str, branch: str, env: dict[str, str] | None = None
) -> list[str]:
    """Check a worktree leaf and branch against the naming contract.

    Parameters: leaf - worktree directory basename; branch - its checked-out
    branch; env - environment mapping used to resolve accepted instances.

    Returns: one message per violated rule; empty when both names conform.
    """
    known = runtime_instances(env)
    problems: list[str] = []
    parsed_leaf = parse_leaf(leaf, known)
    parsed_branch = parse_branch(branch, known)

    if parsed_leaf is None:
        problems.append(
            f"worktree directory {leaf!r} is not <instance>_<type>-<feature>"
        )
    if parsed_branch is None:
        problems.append(
            f"branch {branch!r} is not <type>/<instance>_<feature>"
        )
    if parsed_leaf is None or parsed_branch is None:
        return problems

    if parsed_leaf.instance != parsed_branch.instance:
        problems.append(
            f"instance differs between directory ({parsed_leaf.instance}) "
            f"and branch ({parsed_branch.instance})"
        )
    if parsed_leaf.kind != parsed_branch.kind:
        problems.append(
            f"type differs between directory ({parsed_leaf.kind}) "
            f"and branch ({parsed_branch.kind})"
        )
    if parsed_leaf.feature != parsed_branch.feature:
        problems.append(
            f"feature differs between directory ({parsed_leaf.feature}) "
            f"and branch ({parsed_branch.feature})"
        )
    if known is not None and parsed_leaf.instance not in known:
        problems.append(
            f"instance {parsed_leaf.instance!r} does not identify the agent home; "
            f"expected one of {', '.join(sorted(known))}"
        )
    return problems
