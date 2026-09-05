"""Policy tests for setup repository routing guidance."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = (
    ROOT
    / "skills"
    / "setup-repository-guidelines"
    / "SKILL.md"
)


def test_setup_guidelines_scope_comes_from_manifest_clone_repos() -> None:
    """Repository-family membership should stay dynamic."""
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "Source that manifest in a Bash subprocess and read `CLONE_REPOS`" in content
    assert "Do not maintain a copied repository-name list" in content
    assert "New repositories\n   added to `CLONE_REPOS`" in content


def test_setup_guidelines_invoked_only_on_request_or_new_project() -> None:
    """The skill must not auto-trigger on every task; only on request or a new project."""
    content = SKILL_PATH.read_text(encoding="utf-8")

    assert "Mandatory for every software task" not in content
    assert "mandatory for every task" in content
    assert "completely new project" in content
    assert "explicitly requests" in content


def test_setup_guidelines_no_managed_global_instruction_block() -> None:
    """The auto-trigger global-instruction file must be gone (skill-only now)."""
    global_instructions = (
        ROOT
        / "global-instructions"
        / "setup-repository-guidelines.md"
    )

    assert not global_instructions.exists()
    # global-instructions/ itself may exist: it carries the slim
    # general-programming-guidelines tag merged into every agent's
    # instruction file (see test_plugin_marketplaces.py). Only the
    # setup-repository auto-trigger file must stay gone.
    leftovers = {
        path.name for path in (ROOT / "global-instructions").glob("*.md")
    }
    assert leftovers <= {"general-programming-guidelines.md"}


def test_setup_guidelines_delegate_desktop_deployment_without_restating_it() -> None:
    """Deployment safety must point at `linux-configuration`, not paraphrase it.

    This skill used to name the owning skill and then repeat its reload and
    forbidden-action list anyway, which is the drift the delegation was meant to
    prevent: the paraphrase is what a reader acts on, and it ages independently
    of the owner.
    """
    content = " ".join(SKILL_PATH.read_text(encoding="utf-8").split())

    assert "`linux-configuration` skill owns deployment" in content
    assert "this skill deliberately does not restate its rules" in content.lower()
    # Only the repository-setup half stays here.
    assert "apply the narrowest owning installer and verify installed state against source" in content

    for retired in ("gnome-shell --replace", "Alt+F2 r", "xdotool", "session termination"):
        assert retired not in content, f"{retired!r} belongs to `linux-configuration`"
