"""Preserve the standalone Linux desktop policy contract."""

from pathlib import Path


LINUX_SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "linux-desktop-configuration"
    / "skills"
    / "linux-configuration"
    / "SKILL.md"
)


def test_linux_configuration_skill_carries_the_desktop_rules():
    """Delegation is only safe while the owning skill actually holds the rules.

    These assertions fail if a future edit trims the owner after the guidelines
    stopped restating it, which would otherwise delete the policy outright.
    """
    content = " ".join(LINUX_SKILL_PATH.read_text(encoding="utf-8").split())

    assert "xdotool key --clearmodifiers alt+F2" in content
    assert "gnome-shell --replace" in content
    assert "## Clean Installation Compatibility" in LINUX_SKILL_PATH.read_text(encoding="utf-8")
    assert "## Root-Optional Installers (avoid sudo)" in LINUX_SKILL_PATH.read_text(
        encoding="utf-8"
    )
