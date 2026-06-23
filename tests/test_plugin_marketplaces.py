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


def test_direct_skills_have_no_plugin_manifests() -> None:
    """Prompt-only skills should not appear as standalone plugins."""
    assert {"commit", "setup-repository-guidelines"} <= direct_skill_names()
    assert not (ROOT / "plugins" / "commit-guidelines").exists()
    assert not (ROOT / "plugins" / "setup-repository-guidelines").exists()


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
