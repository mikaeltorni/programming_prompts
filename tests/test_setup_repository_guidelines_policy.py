"""Policy tests for setup repository routing guidance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = (
    ROOT
    / "skills"
    / "setup-repository-guidelines"
    / "SKILL.md"
)
GLOBAL_INSTRUCTIONS_PATH = (
    ROOT
    / "global-instructions"
    / "setup-repository-guidelines.md"
)


def test_setup_guidelines_scope_comes_from_manifest_clone_repos() -> None:
    """Repository-family membership should stay dynamic."""
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "Source that manifest in a Bash subprocess and read `CLONE_REPOS`" in content
    assert "Do not maintain a copied repository-name list" in content
    assert "New repositories\n   added to `CLONE_REPOS`" in content


def test_global_instructions_trigger_setup_guidelines_for_manifest_members() -> None:
    """Global agent instructions should invoke setup guidance for each member."""
    content = GLOBAL_INSTRUCTIONS_PATH.read_text(encoding="utf-8")

    assert "At the start of a software task" in content
    assert "installation_scripts/scripts/repository_manifest.sh" in content
    assert "`CLONE_REPOS` array" in content
    assert "invoke the `setup-repository-guidelines` skill before editing" in content
    assert "do not use a copied repository list" in content
