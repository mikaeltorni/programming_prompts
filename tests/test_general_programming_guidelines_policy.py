"""Policy tests for the general programming guidelines prompt."""

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "general-programming-guidelines"
    / "skills"
    / "programming-guidelines"
    / "SKILL.md"
)


def skill_text() -> str:
    """Return the canonical general programming guidelines text."""
    return SKILL_PATH.read_text(encoding="utf-8")


def test_general_guidelines_require_audit_when_completeness_is_challenged():
    """Completeness challenges should trigger audit and fixes, not caveats."""
    content = skill_text()

    assert "challenges completeness" in content
    assert "bounded compliance audit" in content
    assert "fix concrete gaps" in content


def test_general_guidelines_require_installed_import_contract_tests():
    """Installer/module refactors should guard against missing runtime imports."""
    content = skill_text()

    assert "installed Python entrypoints or helper modules" in content
    assert "project-local imports" in content
    assert "installer copy lists" in content
