"""Validate project-prefixed worktree directory and branch names.

The worktree skill fixes two names for every task: the worktree directory leaf
``<project>_<type>-<feature>`` and its branch ``<type>/<project>_<feature>``.
Both encode the project, commit type, and feature so model or account names do
not become part of the worktree identity. This module parses both names and
reports every component that is missing, malformed, or inconsistent.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorktreeName:
    """Hold the components shared by a worktree leaf and its branch.

    Parameters: project - live repository basename; kind - conventional commit
    type; feature - descriptive task slug.

    Returns: immutable parsed name.
    """

    project: str
    kind: str
    feature: str


def _split_project(text: str, expected: str | None = None) -> tuple[str, str] | None:
    """Separate a project prefix from the remainder of a worktree name.

    Parameters: text - ``<project>_<rest>`` fragment; expected - live repository
    basename when known, allowing project names that contain underscores.

    Returns: project and remainder, or None when no underscore separates them.
    """
    if expected:
        prefix = f"{expected}_"
        if text.startswith(prefix) and text[len(prefix):]:
            return expected, text[len(prefix):]
    project, separator, rest = text.partition("_")
    if not separator or not project or not rest:
        return None
    return project, rest


def parse_leaf(leaf: str, expected_project: str | None = None) -> WorktreeName | None:
    """Parse a worktree directory leaf.

    Parameters: leaf - directory basename; expected_project - live repository
    basename when available.

    Returns: parsed components, or None when the leaf is not
    ``<project>_<type>-<feature>``.
    """
    split = _split_project(leaf, expected_project)
    if split is None:
        return None
    project, rest = split
    kind, separator, feature = rest.partition("-")
    if not separator or not kind or not feature:
        return None
    return WorktreeName(project, kind, feature)


def parse_branch(
    branch: str, expected_project: str | None = None
) -> WorktreeName | None:
    """Parse a task branch name.

    Parameters: branch - short or ``refs/heads`` branch name; expected_project -
    live repository basename when available.

    Returns: parsed components, or None when the branch is not
    ``<type>/<project>_<feature>``.
    """
    short = branch.removeprefix("refs/heads/")
    kind, separator, rest = short.partition("/")
    if not separator or not kind or not rest or "/" in rest:
        return None
    split = _split_project(rest, expected_project)
    if split is None:
        return None
    project, feature = split
    return WorktreeName(project, kind, feature)


def check_names(
    leaf: str, branch: str, expected_project: str
) -> list[str]:
    """Check a worktree leaf and branch against the project naming contract.

    Parameters: leaf - worktree directory basename; branch - its checked-out
    branch; expected_project - physical live checkout basename.

    Returns: one message per violated rule; empty when both names conform.
    """
    problems: list[str] = []
    parsed_leaf = parse_leaf(leaf, expected_project)
    parsed_branch = parse_branch(branch, expected_project)

    if parsed_leaf is None:
        problems.append(
            f"worktree directory {leaf!r} is not <project>_<type>-<feature>"
        )
    if parsed_branch is None:
        problems.append(
            f"branch {branch!r} is not <type>/<project>_<feature>"
        )
    if parsed_leaf is None or parsed_branch is None:
        return problems

    if parsed_leaf.project != expected_project:
        problems.append(
            f"project differs between directory ({parsed_leaf.project}) and "
            f"live checkout ({expected_project})"
        )
    if parsed_branch.project != expected_project:
        problems.append(
            f"project differs between branch ({parsed_branch.project}) and "
            f"live checkout ({expected_project})"
        )
    if parsed_leaf.project != parsed_branch.project:
        problems.append(
            f"project differs between directory ({parsed_leaf.project}) "
            f"and branch ({parsed_branch.project})"
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
    return problems
