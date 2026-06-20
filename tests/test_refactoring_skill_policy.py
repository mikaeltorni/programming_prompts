"""Policy tests for the refactoring skill prompt."""

from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "refactoring" / "SKILL.md"


def skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def test_refactoring_skill_supports_multi_repository_audits():
    content = skill_text()

    assert "multi-repository workspaces" in content
    assert "Inventory every repository first" in content
    assert "Run a second audit" in content


def test_refactoring_skill_prefers_rg_over_grep_examples():
    content = skill_text()

    assert "rg --files" in content
    assert "grep -rn" not in content


def test_refactoring_skill_does_not_tell_agents_to_pip_install_lint_tools():
    content = skill_text()

    assert "pip install flake8" not in content
    assert "Do not install new lint tools ad hoc" in content


def test_refactoring_skill_requires_explicit_commit_request():
    content = skill_text()

    assert "Do not commit changes unless the user explicitly asks for commits" in content
