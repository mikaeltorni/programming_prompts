"""Policy tests for the GitHub portfolio-scan dispatch skill.

The scan is only useful if an agent can keep going until the run is complete:
the per-repository release-readiness rubric must add up to 100, every criterion
must carry a point value, and the prompt must stay an audit — it must not edit
the scanned trees or start an SEO pass. These tests parse the rubric out of the
Markdown and pin those invariants.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DISPATCH_DIR = REPO_ROOT / "dispatch-skills"
SKILL_PATH = DISPATCH_DIR / "github-portfolio-scan" / "SKILL.md"

# "### A. Standalone product story — 20"
CATEGORY_PATTERN = re.compile(r"^### ([A-Z])\. (.+?) — (\d+)$", re.MULTILINE)
# "- **A1 (5) Definitional sentence.** ..."
CRITERION_PATTERN = re.compile(r"^- \*\*([A-Z])(\d+) \((\d+)\)", re.MULTILINE)
# "| P1 | Claims the code does not support | −5 |"
PENALTY_PATTERN = re.compile(r"^\| (P\d+) \| (.+?) \| −(\d+) \|$", re.MULTILINE)

TOTAL_POINTS = 100


def skill_text() -> str:
    """Return the raw portfolio-scan skill prompt."""
    return SKILL_PATH.read_text(encoding="utf-8")


def normalized_skill_text() -> str:
    """Return the prompt with runs of whitespace collapsed to single spaces."""
    return " ".join(skill_text().split())


def criteria_with_descriptions() -> list[tuple[str, int, int, str]]:
    """Return every rubric criterion as ``(letter, index, points, description)``."""
    text = skill_text()
    criteria: list[tuple[str, int, int, str]] = []
    matches = list(CRITERION_PATTERN.finditer(text))

    for position, match in enumerate(matches):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        body = text[match.start() : end]
        heading = re.search(r"^#{2,3} ", body, re.MULTILINE)
        if heading:
            body = body[: heading.start()]
        criteria.append(
            (match.group(1), int(match.group(2)), int(match.group(3)), " ".join(body.split()))
        )

    return criteria


def test_portfolio_scan_skill_lives_in_the_dispatch_folder():
    assert SKILL_PATH.is_file()
    assert SKILL_PATH.parent.name == "github-portfolio-scan"


def test_portfolio_scan_rubric_categories_sum_to_one_hundred():
    categories = CATEGORY_PATTERN.findall(skill_text())

    assert len(categories) >= 6, "the rubric lost categories"
    assert sum(int(weight) for _, _, weight in categories) == TOTAL_POINTS


def test_portfolio_scan_rubric_criteria_sum_to_their_category_weight():
    text = skill_text()
    declared = {letter: int(weight) for letter, _, weight in CATEGORY_PATTERN.findall(text)}

    earned: dict[str, int] = {}
    for letter, _index, points in CRITERION_PATTERN.findall(text):
        earned[letter] = earned.get(letter, 0) + int(points)

    assert earned == declared


def test_portfolio_scan_rubric_criteria_are_numbered_without_gaps():
    seen: dict[str, list[int]] = {}
    for letter, index, _points in CRITERION_PATTERN.findall(skill_text()):
        seen.setdefault(letter, []).append(int(index))

    for letter, indexes in seen.items():
        assert indexes == list(range(1, len(indexes) + 1)), f"category {letter} is misnumbered"


def test_portfolio_scan_rubric_defines_penalties_that_subtract():
    penalties = PENALTY_PATTERN.findall(skill_text())

    assert len(penalties) >= 6
    assert all(int(points) > 0 for _, _, points in penalties)


def test_portfolio_scan_requires_evidence_before_awarding_points():
    content = normalized_skill_text()

    assert "Evidence or zero." in content
    assert "Never inflate a score." in content


def test_portfolio_scan_is_read_only_against_scanned_trees():
    content = normalized_skill_text()

    assert "Never edit, stage, commit, merge, push, or rewrite" in content
    assert "The audit is reported, never stored in a scanned repository." in content
    assert "Do not start editing repositories to raise their A–G scores in this skill." in content


def test_portfolio_scan_covers_any_directory_of_checkouts():
    content = normalized_skill_text()

    assert "Scan **any directory** of git checkouts" in content
    assert "If the user named a path, use it." in content
    assert "Inspect included checkouts one by one." in content


def test_portfolio_scan_defers_seo_and_forbids_ci():
    content = normalized_skill_text()

    assert "run `github-seo` as a separate dispatch" in content
    assert "Never add continuous integration" in content
    for _, _, _, description in criteria_with_descriptions():
        assert "CI workflow" not in description
        assert "topics" not in description.lower() or "GitHub topics" not in description


def test_portfolio_scan_defines_a_loop_with_a_stop_condition():
    content = normalized_skill_text()

    assert "### Stop condition" in content
    assert "the run score is 100/100" in content
    assert "the tier list is complete" in content


def test_portfolio_scan_run_score_is_completeness_not_an_average():
    content = normalized_skill_text()

    assert "The **measurable score for this dispatch** is completeness of the scan" in content
    assert "not the average of repository scores" in content


def test_portfolio_scan_ranks_forks_separately():
    content = normalized_skill_text()

    assert "Never present a fork as an original product." in content
    assert "Rank forks in a Fork tier." in content


def test_portfolio_scan_prefers_rg_over_grep_examples():
    content = skill_text()

    assert "rg -n" in content or "rg '" in content
    assert "grep -rn" not in content
