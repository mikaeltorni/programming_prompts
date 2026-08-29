"""Tests for the Python dependency supply-chain policy."""

from pathlib import Path


PROGRAMMING_GUIDELINES_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "general-programming-guidelines"
    / "SKILL.md"
)

INIT_PROJECT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "init-project"
    / "SKILL.md"
)


def test_python_policy_requires_a_rolling_24_hour_release_delay():
    """New Python projects must reject packages published in the last 24 hours."""
    content = INIT_PROJECT_PATH.read_text(encoding="utf-8")

    assert "24 hours" in content
    assert "exclude-newer" in content
    assert "[tool.uv]" in content


def test_plain_pip_must_install_only_from_a_hash_locked_export():
    """Pip must not independently resolve dependencies around the uv cooldown."""
    content = INIT_PROJECT_PATH.read_text(encoding="utf-8")

    assert "pip install --require-hashes" in content
    assert "uv export" in content


def test_programming_guidelines_references_init_project():
    """Programming guidelines must reference init-project skill for Python."""
    content = PROGRAMMING_GUIDELINES_PATH.read_text(encoding="utf-8")

    assert "init-project" in content
    assert "exclude-newer" in content
    assert "supply-chain protection" in content
