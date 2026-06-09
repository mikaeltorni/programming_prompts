"""Tests for the Python dependency supply-chain policy."""

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "general-programming-guidelines"
    / "skills"
    / "programming-guidelines"
    / "SKILL.md"
)


def test_python_policy_requires_a_rolling_24_hour_release_delay():
    """New Python projects must reject packages published in the last 24 hours."""
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "new project" in content
    assert "adding Python to an existing project for the first time" in content
    assert "24 hours" in content
    assert "--exclude-newer" in content
    assert "UTC" in content


def test_plain_pip_must_install_only_from_a_hash_locked_export():
    """Pip must not independently resolve dependencies around the uv cooldown."""
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "pip must not resolve dependencies directly" in content
    assert "--require-hashes" in content
    assert "uv export" in content
