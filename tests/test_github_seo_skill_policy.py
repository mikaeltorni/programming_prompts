"""Policy tests for the dispatch-skills folder and the GitHub SEO skill prompt.

The SEO prompt is only useful if its scoring rubric stays arithmetically sound:
an agent that keeps improving "until the score is perfect" needs the category
weights to add up to exactly 100, and needs every criterion to carry a point
value it can award. These tests parse the rubric out of the Markdown and check
that invariant, plus the structural rules that make a prompt dispatchable.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCH_DIR = REPO_ROOT / "dispatch-skills"
SEO_SKILL_PATH = DISPATCH_DIR / "github-seo" / "SKILL.md"

# "### A. Repository identity and metadata — 15"
CATEGORY_PATTERN = re.compile(r"^### ([A-Z])\. (.+?) — (\d+)$", re.MULTILINE)
# "- **A1 (3) About description.** ..."
CRITERION_PATTERN = re.compile(r"^- \*\*([A-Z])(\d+) \((\d+)\)", re.MULTILINE)
# "| P1 | Keyword stuffing ... | −5 |"
PENALTY_PATTERN = re.compile(r"^\| (P\d+) \| (.+?) \| −(\d+) \|$", re.MULTILINE)

TOTAL_POINTS = 100


def skill_text() -> str:
    """Return the raw SEO skill prompt."""
    return SEO_SKILL_PATH.read_text(encoding="utf-8")


def normalized_skill_text() -> str:
    """Return the SEO prompt with runs of whitespace collapsed to single spaces.

    Line wrapping in the prompt would otherwise break substring assertions on
    sentences that span two lines.
    """
    return " ".join(skill_text().split())


def dispatch_skill_paths() -> list[Path]:
    """Return every ``dispatch-skills/<name>/SKILL.md`` in the repository."""
    return sorted(DISPATCH_DIR.glob("*/SKILL.md"))


def test_dispatch_skills_folder_exists_with_a_readme():
    assert DISPATCH_DIR.is_dir()
    assert (DISPATCH_DIR / "README.md").is_file()


def test_seo_skill_lives_in_the_dispatch_folder():
    assert SEO_SKILL_PATH.is_file()
    assert SEO_SKILL_PATH in dispatch_skill_paths()


@pytest.mark.parametrize("skill_path", dispatch_skill_paths(), ids=lambda p: p.parent.name)
def test_dispatch_skill_front_matter_name_matches_its_directory(skill_path: Path):
    """The menu builds ``/<name>`` and ``$<name>`` from the directory name."""
    content = skill_path.read_text(encoding="utf-8")

    assert content.startswith("---\n")
    front_matter = content.split("---", 2)[1]
    name_match = re.search(r"^name: (.+)$", front_matter, re.MULTILINE)

    assert name_match is not None
    assert name_match.group(1).strip().strip('"') == skill_path.parent.name


@pytest.mark.parametrize("skill_path", dispatch_skill_paths(), ids=lambda p: p.parent.name)
def test_dispatch_skill_carries_no_plugin_manifest(skill_path: Path):
    """Dispatch skills are prompt-only; plugin manifests belong under plugins/."""
    plugin_dir = skill_path.parent.parent
    assert not (plugin_dir / ".claude-plugin").exists()
    assert not (plugin_dir / ".codex-plugin").exists()


@pytest.mark.parametrize("skill_path", dispatch_skill_paths(), ids=lambda p: p.parent.name)
def test_dispatch_skill_defers_isolation_policy_to_the_shared_guidelines(skill_path: Path):
    content = skill_path.read_text(encoding="utf-8")
    assert "general-programming-guidelines" in content


def test_seo_rubric_categories_sum_to_one_hundred():
    categories = CATEGORY_PATTERN.findall(skill_text())

    assert len(categories) >= 8, "the rubric lost categories"
    assert sum(int(weight) for _, _, weight in categories) == TOTAL_POINTS


def test_seo_rubric_criteria_sum_to_their_category_weight():
    text = skill_text()
    declared = {letter: int(weight) for letter, _, weight in CATEGORY_PATTERN.findall(text)}

    earned: dict[str, int] = {}
    for letter, _index, points in CRITERION_PATTERN.findall(text):
        earned[letter] = earned.get(letter, 0) + int(points)

    assert earned == declared


def test_seo_rubric_criteria_are_numbered_without_gaps():
    seen: dict[str, list[int]] = {}
    for letter, index, _points in CRITERION_PATTERN.findall(skill_text()):
        seen.setdefault(letter, []).append(int(index))

    for letter, indexes in seen.items():
        assert indexes == list(range(1, len(indexes) + 1)), f"category {letter} is misnumbered"


def test_seo_rubric_defines_penalties_that_subtract():
    penalties = PENALTY_PATTERN.findall(skill_text())

    assert len(penalties) >= 6
    assert all(int(points) > 0 for _, _, points in penalties)


def test_seo_skill_requires_evidence_before_awarding_points():
    content = normalized_skill_text()

    assert "Evidence or zero." in content
    assert "Never inflate the score." in content
    assert "never copy a previous round's score forward without re-verifying it" in content


def test_seo_skill_defines_a_tracked_scorecard_file():
    content = normalized_skill_text()

    assert "docs/seo-scorecard.md" in content
    assert "Round history" in content
    assert "Pending user actions" in content


def test_seo_skill_defines_a_continuous_loop_with_a_stop_condition():
    content = normalized_skill_text()

    assert "### Stop condition" in content
    assert "maintenance mode" in content
    assert '"nothing to do" is not a valid outcome' in content
    assert "There is no deadline" in content


def test_seo_skill_normalizes_the_total_when_criteria_are_not_applicable():
    content = normalized_skill_text()

    assert "N/A points leave the denominator" in content
    assert "round(100 × (earned − penalties) ÷ applicable_max)" in content


def test_seo_skill_forbids_fake_signals_and_unapproved_publishing():
    content = normalized_skill_text()

    assert "Never fake a signal." in content
    assert "Never keyword-stuff." in content
    assert "Never publish anything on the user's behalf" in content
    assert "Never rename the repository" in content


def test_seo_skill_prefers_rg_over_grep_examples():
    content = skill_text()

    assert "rg -n" in content
    assert "grep -rn" not in content
