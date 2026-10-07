"""Policy tests: every SKILL.md declares a semver prefix, and AGENTS.md requires bumps.

Skill pickers and installed copies read the YAML ``description`` first. The
repository keeps that prefix in ``vMAJOR.MINOR.PATCH —`` form (folded ``>-`` or
a single line). AGENTS.md owns the keep-updating rule so a later skill edit
cannot leave the number stale, leave it unchanged, or decrease it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"

# Folded or single-line description must start with this once whitespace is collapsed.
VERSION_PREFIX = re.compile(r"^v\d+\.\d+\.\d+ —")

# Gitignored Harbor artifacts may still exist on disk under these prefixes.
_GENERATED_SKILL_PREFIXES = (
    ("programming_prompt_rewritten_with_evals", "evals", "runs"),
    ("programming_prompt_rewritten_with_evals", "evals", "tasks"),
    ("programming_prompt_rewritten_with_evals", "evals", ".generated"),
)


def skill_md_paths() -> list[Path]:
    """Return every owned repository ``SKILL.md``, excluding Git internals and generated Harbor copies.

    Parameters: none.

    Returns: sorted absolute paths to skill files.
    """
    print("parameters=none")
    owned: list[Path] = []
    for path in REPO_ROOT.rglob("SKILL.md"):
        if ".git" in path.parts:
            continue
        relative_parts = path.relative_to(REPO_ROOT).parts
        if any(
            relative_parts[: len(prefix)] == prefix
            for prefix in _GENERATED_SKILL_PREFIXES
        ):
            continue
        owned.append(path)
    result = sorted(owned)
    print(result)
    return result


def skill_description(path: Path) -> str:
    """Return the YAML ``description`` with wrapping collapsed to single spaces.

    Handles a folded ``description: >-`` block and a single-line ``description:``.
    The glob tests call this on real ``SKILL.md`` files, not fixtures.

    Parameters: path - a ``SKILL.md`` file.

    Returns: the description text, or raises AssertionError when front matter is missing.
    """
    print(f"path={path}")
    text = path.read_text(encoding="utf-8")
    relative = path.relative_to(REPO_ROOT)
    assert text.startswith("---\n"), f"{relative}: missing YAML front matter"
    parts = text.split("---", 2)
    assert len(parts) >= 3, f"{relative}: incomplete YAML front matter"
    front_matter = parts[1]
    lines = front_matter.splitlines()
    for index, line in enumerate(lines):
        if not line.startswith("description:"):
            continue
        rest = line[len("description:") :].strip()
        if rest in {">-", ">", "|-", "|"}:
            chunks: list[str] = []
            for continuation in lines[index + 1 :]:
                if continuation.startswith(" ") or continuation.startswith("\t"):
                    chunks.append(continuation.strip())
                    continue
                break
            assert chunks, f"{relative}: folded description is empty"
            result = " ".join(chunks)
            print(result)
            return result
        assert rest, f"{relative}: single-line description is empty"
        print(rest)
        return rest
    raise AssertionError(f"{relative}: YAML front matter has no description")


SKILL_PATHS = skill_md_paths()
SKILL_IDS = [str(path.relative_to(REPO_ROOT)) for path in SKILL_PATHS]


def test_skill_md_glob_lists_every_owned_tree():
    """The inventory must cover the four skill trees and list every path.

    Parameters: none.

    Returns: None.
    """
    print("parameters=none")
    assert SKILL_IDS, "expected at least one SKILL.md"
    joined = "\n".join(SKILL_IDS)
    assert any(item.startswith("skills/") for item in SKILL_IDS), joined
    assert any(item.startswith("plugins/") for item in SKILL_IDS), joined
    assert any(item.startswith("dispatch-skills/") for item in SKILL_IDS), joined
    assert any(
        item.startswith("programming_prompt_rewritten_with_evals/prompts/programming-skills/")
        for item in SKILL_IDS
    ), joined
    assert all(
        "evals/runs" not in item
        and "evals/tasks" not in item
        and "evals/.generated" not in item
        for item in SKILL_IDS
    ), joined
    print(None)


@pytest.mark.parametrize("skill_path", SKILL_PATHS, ids=SKILL_IDS)
def test_every_skill_description_starts_with_semver(skill_path: Path):
    """Each skill description must open with ``vDIGITS.DIGITS.DIGITS —``.

    Parameters: skill_path - a repository ``SKILL.md`` file.

    Returns: None.
    """
    print(f"skill_path={skill_path}")
    description = skill_description(skill_path)
    assert VERSION_PREFIX.match(description), (
        f"{skill_path.relative_to(REPO_ROOT)}: description must start with "
        f"vMAJOR.MINOR.PATCH — ; got {description!r}"
    )
    print(None)


def test_agents_md_requires_bumping_skill_versions_when_skills_change():
    """Require the real AGENTS.md Skill versions section to mandate a strict increase.

    Parameters: none.

    Returns: None.
    """
    print("parameters=none")
    assert AGENTS_PATH.is_file()
    assert AGENTS_PATH.name == "AGENTS.md"
    assert AGENTS_PATH.parent.resolve() == REPO_ROOT.resolve()
    text = AGENTS_PATH.read_text(encoding="utf-8")
    heading = "## Skill versions"
    assert heading in text
    section = text.split(heading, 1)[1]
    next_heading = re.search(r"\n## ", section)
    if next_heading:
        section = section[: next_heading.start()]
    content = " ".join(section.split())
    assert "vMAJOR.MINOR.PATCH" in content
    assert "YAML `description`" in section or "YAML ``description``" in section
    assert "strictly increased" in content
    assert "never left the same" in content
    assert "never decreased" in content
    assert "cannot leave versions stale" in content
    assert (
        "Keep an already-versioned skill at its current number unless "
        "its text also changes."
    ) in content
    print(None)
