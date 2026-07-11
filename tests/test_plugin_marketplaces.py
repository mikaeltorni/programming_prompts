"""Validate the standalone Codex and Claude plugin packaging.

Marketplace catalogs are intentionally absent: generation and installation are
owned by the sibling ``linux_codex_claude_code_setup`` repository. See AGENTS.md.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def plugin_names() -> set[str]:
    return {
        path.parent.parent.name
        for path in ROOT.glob("plugins/*/.codex-plugin/plugin.json")
    }


def direct_skill_names() -> set[str]:
    return {
        path.parent.name
        for path in ROOT.glob("skills/*/SKILL.md")
    }


def test_every_plugin_has_codex_claude_manifests_and_one_skill() -> None:
    """Each installable unit should expose one skill to both products."""
    names = plugin_names()
    assert names
    for name in names:
        root = ROOT / "plugins" / name
        codex = json.loads((root / ".codex-plugin" / "plugin.json").read_text())
        claude = json.loads((root / ".claude-plugin" / "plugin.json").read_text())
        skills = list(root.glob("skills/*/SKILL.md"))
        assert codex["name"] == name
        assert claude["name"] == name
        assert len(skills) == 1, f"{name} must package exactly one skill"


def test_requested_plugin_and_direct_skill_boundaries() -> None:
    """Commit is a plugin; guidelines/init/refactoring/setup are direct skills."""
    assert {
        "general-programming-guidelines",
        "init-project",
        "refactoring",
        "setup-repository-guidelines",
    } <= direct_skill_names()
    assert (ROOT / "plugins" / "commit-guidelines" / ".codex-plugin" / "plugin.json").is_file()
    assert not (ROOT / "plugins" / "setup-repository-guidelines").exists()
    assert not (ROOT / "plugins" / "general-programming-guidelines").exists()


def test_general_programming_guidelines_global_tag_stays_slim() -> None:
    """The always-on tag must point at the skill without bloating context."""
    tag = ROOT / "global-instructions" / "general-programming-guidelines.md"
    text = tag.read_text(encoding="utf-8")
    assert "general-programming-guidelines" in text
    assert "skill" in text.lower()
    assert len(text.splitlines()) <= 10, "global tag must stay slim"
    assert "## Work Loop" not in text, "full skill body belongs in SKILL.md only"


def test_repository_contains_no_marketplace_catalogs() -> None:
    """Marketplace generation is owned by linux_codex_claude_code_setup."""
    assert not list(ROOT.rglob("marketplace.json"))
    assert not (ROOT / ".claude-plugin").exists()
    assert not (ROOT / ".agents").exists()


def test_repository_contains_no_installer_implementation() -> None:
    """Installation logic belongs to linux_codex_claude_code_setup."""
    assert not (ROOT / "install.sh").exists()
    assert not (ROOT / "installer").exists()
    assert not (ROOT / "lib").exists()
    assert not (ROOT / "scripts").exists()
