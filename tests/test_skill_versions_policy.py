"""Policy tests: every SKILL.md declares a semver prefix, and AGENTS.md requires bumps.

Skill pickers and installed copies read the YAML ``description`` first. The
repository keeps that prefix in ``vMAJOR.MINOR.PATCH —`` form (folded ``>-`` or
a single line). AGENTS.md owns the keep-updating rule so a later skill edit
cannot leave the number stale.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_PATH = REPO_ROOT / "AGENTS.md"

# Source skill trees only. Harbor trial archives under evals/runs/ copy SKILL.md
# into agent sessions and must not join this inventory.
SKILL_TREES = (
    REPO_ROOT / "skills",
    REPO_ROOT / "plugins",
    REPO_ROOT / "dispatch-skills",
    REPO_ROOT / "programming_prompt_rewritten_with_evals" / "prompts" / "programming-skills",
)

# Folded or single-line description must start with this once whitespace is collapsed.
VERSION_PREFIX = re.compile(r"^v\d+\.\d+\.\d+ —")


def skill_md_paths() -> list[Path]:
    """Return every source ``SKILL.md`` under the four owned skill trees.

    Parameters: none.

    Returns: sorted absolute paths to skill files.
    """
    paths: list[Path] = []
    for tree in SKILL_TREES:
        paths.extend(path for path in tree.rglob("SKILL.md") if ".git" not in path.parts)
    return sorted(paths)


def skill_description(path: Path) -> str:
    """Return the YAML ``description`` with wrapping collapsed to single spaces.

    Handles a folded ``description: >-`` block and a single-line ``description:``.
    The glob tests call this on real ``SKILL.md`` files, not fixtures.

    Parameters: path - a ``SKILL.md`` file.

    Returns: the description text, or raises AssertionError when front matter is missing.
    """
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
            return " ".join(chunks)
        assert rest, f"{relative}: single-line description is empty"
        return rest
    raise AssertionError(f"{relative}: YAML front matter has no description")


SKILL_PATHS = skill_md_paths()
SKILL_IDS = [str(path.relative_to(REPO_ROOT)) for path in SKILL_PATHS]


def test_skill_md_glob_lists_every_owned_tree():
    """The inventory must cover the four skill trees and list every path."""
    assert SKILL_IDS, "expected at least one SKILL.md"
    joined = "\n".join(SKILL_IDS)
    assert any(item.startswith("skills/") for item in SKILL_IDS), joined
    assert any(item.startswith("plugins/") for item in SKILL_IDS), joined
    assert not any("evals/runs/" in item for item in SKILL_IDS), joined
    assert any(item.startswith("dispatch-skills/") for item in SKILL_IDS), joined
    assert any(
        item.startswith("programming_prompt_rewritten_with_evals/prompts/programming-skills/")
        for item in SKILL_IDS
    ), joined
    for path in SKILL_PATHS:
        assert any(path.is_relative_to(tree) for tree in SKILL_TREES), path


@pytest.mark.parametrize("skill_path", SKILL_PATHS, ids=SKILL_IDS)
def test_every_skill_description_starts_with_semver(skill_path: Path):
    """Each skill description must open with ``vDIGITS.DIGITS.DIGITS —``."""
    description = skill_description(skill_path)
    assert VERSION_PREFIX.match(description), (
        f"{skill_path.relative_to(REPO_ROOT)}: description must start with "
        f"vMAJOR.MINOR.PATCH — ; got {description!r}"
    )


def test_agents_md_requires_bumping_skill_versions_when_skills_change():
    """The keep-updating rule must live in the real AGENTS.md, not a restated copy."""
    text = AGENTS_PATH.read_text(encoding="utf-8")
    content = " ".join(text.split())
    assert "vMAJOR.MINOR.PATCH" in content
    assert (
        "Skill versions must be bumped whenever those skills are updated" in content
    )
    assert "cannot leave versions stale" in content
    assert "YAML `description`" in text or "YAML ``description``" in text
