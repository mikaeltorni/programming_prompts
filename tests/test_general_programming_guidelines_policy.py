"""Policy tests for the general programming guidelines prompt.

The guidelines skill owns the shared engineering Work Loop only. Feature
boundaries and commit sequencing belong to the `commits` skill, and worktree
isolation, merging, and consumer reapplication belong to the `worktree` skill.
These tests pin that ownership split from the guidelines side: the Work Loop
must stay intact, the delegation must stay explicit, and the retired commit and
worktree mechanics must not creep back in as a duplicated second source of
truth. `tests/test_delivery_skills_policy.py` covers the two owning skills.
"""

import re
from pathlib import Path


SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "general-programming-guidelines"
    / "SKILL.md"
)

WRAPPER_PATH = (
    Path(__file__).resolve().parents[1]
    / "global-instructions"
    / "general-programming-guidelines.md"
)


def skill_text() -> str:
    """Return the canonical general programming guidelines text."""
    return SKILL_PATH.read_text(encoding="utf-8")


def flat_skill_text() -> str:
    """Return the guidelines text with line wrapping collapsed.

    Assertions on sentences must not break when a paragraph is re-wrapped, so
    match against a single-space-joined form instead of the raw file.
    """
    return " ".join(skill_text().split())


def wrapper_text() -> str:
    """Return the always-on bootstrap wrapper text."""
    return WRAPPER_PATH.read_text(encoding="utf-8")


def test_general_guidelines_require_audit_when_completeness_is_challenged():
    """Completeness challenges should trigger audit and fixes, not caveats."""
    content = flat_skill_text()

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

    assert "## Work Loop" in content
    assert "1. **Capture scope.**" in content
    assert "2. **Inspect first.**" in content
    assert "3. **Plan and verify the baseline.**" in content
    assert "4. **Implement.**" in content
    assert "5. **Instrument and document.**" in content
    assert "6. **Verify.**" in content
    assert "7. **Deliver and self-check.**" in content
    # The steps must stay in that order in the file, not just be present.
    positions = [
        content.index(step)
        for step in (
            "1. **Capture scope.**",
            "2. **Inspect first.**",
            "3. **Plan and verify the baseline.**",
            "4. **Implement.**",
            "5. **Instrument and document.**",
            "6. **Verify.**",
            "7. **Deliver and self-check.**",
        )
    ]
    assert positions == sorted(positions)


def test_general_guidelines_declare_commits_and_worktree_skill_ownership():
    """Feature commits and worktree delivery are owned by the separate skills.

    Both used to be restated here, which let the copies drift apart. The
    guidelines must now name the owning skill instead of repeating its rules.
    """
    content = flat_skill_text()

    assert "## Skill ownership" in skill_text()
    assert "`commits` skill owns Feature boundaries" in content
    assert "commit sequencing, and commit verification" in content
    assert "`worktree` skill owns isolation" in content
    assert "project/instance paths, branch policy, merging, and consumer reapplication" in content
    # Delegation is an instruction to follow them, not an optional pointer.
    assert "Follow those selected skills alongside this engineering workflow" in content
    assert "this file does not duplicate their policies" in content
    # The Definition of Done must still gate on the selected skills.
    assert "Applicable selected skills and project instructions were followed" in content


def test_general_guidelines_do_not_duplicate_commit_and_worktree_mechanics():
    """The retired duplicate policy must not return to the guidelines skill.

    Anything a reader could follow without opening `commits`/`worktree` is a
    second source of truth. Concrete git recipes are the tell, so they must
    live only in the owning skills.
    """
    content = flat_skill_text()

    for retired in (
        "git worktree add",
        "git merge --no-ff",
        "git branch --show-current",
        ".worktrees/",
        "<type>(<worktree-name>): <summary>",
        "Never push",
    ):
        assert retired not in content, f"{retired!r} belongs to the owning skill"


def test_general_guidelines_name_the_skill_selector_command():
    """Applying the split must be reproducible on every harness.

    The three skills are selected independently, so the guidelines carry the
    exact ACC selector commands that enable and verify all of them at once.
    """
    content = flat_skill_text()

    assert (
        "acc pp enable --both --skill general-programming-guidelines,v2:commits,v2:worktree"
        in content
    )
    assert (
        "acc pp status --skill general-programming-guidelines,commits,worktree --check"
        in content
    )
    assert "ACC's installer baseline enables all three" in content


def test_general_guidelines_definition_of_done_requires_logging_and_docs():
    """The done checklist should require logging and documentation coverage."""
    content = flat_skill_text()

    assert "## Definition of Done" in skill_text()
    assert "Changed action paths and boundaries use the centralized logger" in content
    assert "Public helpers and non-obvious behavior are documented" in content
    assert "Relevant tests or direct prompt/document checks pass." in content
    assert "Consumers are verified and the final report states evidence and limits." in content


def test_general_guidelines_exempt_static_prompt_files_from_forced_instrumentation():
    """Prompt content should not be treated like runtime code."""
    content = flat_skill_text()

    assert "Do not force function-doc, logging, or API-style comments" in content
    assert "static prompt files" in content


def test_general_guidelines_define_shell_logging_contracts():
    """Bash scripts should centralize logging without breaking output contracts."""
    content = flat_skill_text()

    assert "For Bash and other shell scripts" in content
    assert "one sourced logging helper" in content
    assert "do not hardcode ad-hoc log helpers" in content
    assert "source the shared helper" in content
    assert "installer-compatible status and errors on stderr" in content
    assert "stdout must remain reserved for machine-readable output" in content


def test_general_guidelines_description_shows_current_version_before_mandatory():
    """The skill picker must expose the current version before its mandate."""
    assert re.search(
        r"description: >-\n  v\d+\.\d+\.\d+ — Mandatory engineering workflow", skill_text()
    )


def test_general_guidelines_respect_project_agents_and_claude_first():
    """Repository AGENTS.md / CLAUDE.md outrank conflicting skill and agent defaults."""
    content = skill_text()

    assert "## Project instructions first" in content
    assert "`AGENTS.md`" in content
    assert "`CLAUDE.md`" in content
    assert "take precedence" in content
    # Project files, then skill ownership, then the shared Work Loop.
    assert (
        content.index("## Project instructions first")
        < content.index("## Skill ownership")
        < content.index("## Work Loop")
    )
    # Delegating to project files must not become permission to skip this skill.
    assert "Do not skip this skill" in " ".join(content.split())


def test_wrapper_delegates_to_the_commits_and_worktree_skills():
    """The slim always-on wrapper must not contradict the ownership split.

    Hosts such as Grok read only the wrapper. It must send them to all three
    skills and must not carry a stale worktree/commit recipe of its own.
    """
    wrapper = " ".join(wrapper_text().split())

    assert "`commits` and `worktree` skills own Feature commits" in wrapper
    assert "worktree isolation/delivery" in wrapper
    assert (
        "acc pp enable --both --skill general-programming-guidelines,v2:commits,v2:worktree"
        in wrapper
    )
    assert "`AGENTS.md`" in wrapper and "`CLAUDE.md`" in wrapper
    assert "Respect the repository's" in wrapper
    # No duplicated mechanics, and no claim that the skill outranks project files.
    assert "git worktree add" not in wrapper
    assert "git merge --no-ff" not in wrapper
    assert "not optional, a fallback, or overridden by a" not in wrapper


def test_general_guidelines_require_silent_non_visual_tests():
    """Automated tests must not open interrupting GUI/console windows by default.

    Non-screenshot runs should mock spawn/launch at the defining module so a
    re-export-only patch cannot leave real kitty/terminal windows flashing.
    """
    content = skill_text()

    assert "Keep non-visual automated tests silent" in content
    assert "terminal emulators" in content
    assert "deliberate visual or screenshot" in content
    assert "Patch mocks at the defining module" in content
    assert "re-export" in content
    # Mock target guidance must name the failure mode (real launcher still runs).
    assert "defining module" in content
    assert "Popen" in content or "subprocess" in content


def test_wrapper_version_matches_the_skill_version():
    """The bootstrap wrapper must not drift from the skill version.

    Hosts such as Grok read the always-on wrapper, not the skill front matter,
    so a stale wrapper version makes agents report a version mismatch.
    """
    skill_version = re.search(
        r"description: >-\n  v(\d+\.\d+\.\d+) — Mandatory", skill_text()
    )
    assert skill_version is not None, "skill description must declare a version"
    version = skill_version.group(1)

    wrapper = wrapper_text()
    assert f"## General Programming Guidelines v{version} (always on)" in wrapper
    assert f"These are v{version} MANDATORY instructions" in wrapper
    # No other version string may survive in the wrapper.
    assert re.search(r"v(?!%s)\d+\.\d+\.\d+" % re.escape(version), wrapper) is None


def test_general_guidelines_forbid_unrequested_ci():
    """CI is opt-in: agents must never add pipelines or badges unprompted."""
    content = skill_text()

    assert "Never add CI to a repository unless the user explicitly asks" in content
    assert ".github/workflows/" in content
    assert "build-status badge" in content
    assert "leave it exactly as it is" in content


def test_ci_prohibition_is_carried_by_the_always_on_wrapper():
    """Hosts that only read the wrapper must still see the CI prohibition."""
    wrapper = " ".join(wrapper_text().split())

    assert "Never add CI" in wrapper
    assert "unless explicitly requested" in wrapper
    assert "leave existing CI unchanged" in wrapper
