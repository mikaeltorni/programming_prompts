"""Policy tests for the general programming guidelines prompt."""

from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "general-programming-guidelines"
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


def test_general_guidelines_require_numbered_work_loop():
    """Software work should run through the full ordered work loop."""
    content = skill_text()

    assert "Run every software task through these numbered steps in order" in content
    # Step 1 must be creating the worktree, before any edit.
    assert "1. **Create an isolated worktree (do this first, before any edit).**" in content
    assert "2. **Capture scope.**" in content
    assert "3. **Inspect first.**" in content
    assert "4. **Plan and write tests first.**" in content
    assert "5. **Implement.**" in content
    assert "6. **Instrument and document the code you just wrote.**" in content
    assert "7. **Verify.**" in content
    assert "8. **Self-check and report.**" in content


def test_general_guidelines_definition_of_done_requires_logging_and_docs():
    """The done checklist should require logging and documentation coverage."""
    content = skill_text()

    assert "## Definition of Done" in content
    assert "New or changed action paths" in content
    assert "external calls are logged through the existing centralized logger" in content
    assert "New or changed public functions" in content
    assert "non-obvious\n      behavior are documented including their parameters" in content


def test_general_guidelines_exempt_static_prompt_files_from_forced_instrumentation():
    """Prompt content should not be treated like runtime code."""
    content = skill_text()

    assert "Do not force function-doc, logging, or API-style comments" in content
    assert "static prompt\n  files" in content


def test_general_guidelines_define_shell_logging_contracts():
    """Bash scripts should centralize logging without breaking output contracts."""
    content = skill_text()

    assert "For Bash and other shell scripts" in content
    assert "one sourced logging helper" in content
    assert "do not hardcode ad-hoc log helpers" in content
    assert "source the shared helper" in content
    assert "installer-compatible status and errors on stderr" in content
    assert "stdout must remain reserved for machine-readable output" in content


def test_general_guidelines_require_worktrees_by_default():
    """Agents should isolate changes unless the user requests the current checkout."""
    content = " ".join(skill_text().split())

    assert "Use a dedicated Git worktree and a new branch for every task by default" in content
    assert "only when the user explicitly requests it" in content


def test_general_guidelines_make_worktree_the_explicit_first_step():
    """Worktree creation must be Step 1 with a concrete command, not a buried aside.

    11 agents in a row skipped the worktree when it was one bullet in Scope and
    Safety; making it the numbered first step with the exact command is what
    drives consistent compliance.
    """
    content = skill_text()

    assert "## Start here — the non-negotiables" in content
    assert "Create a git worktree and branch first" in content
    # The concrete command must be present so weak models can copy it verbatim.
    assert "git worktree add ../<repo>-wt-<task> -b <task-branch>" in content
    # The Definition of Done must gate on the worktree too.
    assert "All edits were made on a dedicated git worktree branch" in content


def test_general_guidelines_description_shows_current_version_before_mandatory():
    """The skill picker must expose the current version before its mandate."""
    content = skill_text()

    assert "description: >-\n  v1.6.0 — Mandatory engineering workflow" in content
