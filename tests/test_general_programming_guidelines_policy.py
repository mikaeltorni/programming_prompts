"""Policy tests for the general programming guidelines prompt."""

import re
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
    # Feature scan is its own always-run step before plan/implement.
    assert "4. **Scan for Features" in content
    assert "5. **Plan and write tests first.**" in content
    assert "6. **Implement.**" in content
    assert "7. **Instrument and document the code you just wrote.**" in content
    assert "8. **Verify.**" in content
    assert "9. **Deliver: commit, merge, reload.**" in content
    assert "10. **Self-check and report.**" in content


def test_general_guidelines_require_separate_feature_scan_step():
    """Multi-step prompts must be scanned into Features as a dedicated Work Loop step.

    Agents that skip this step pile unrelated work into one commit or implement
    out of dependency order. The scan always runs — even when the result is a
    single Feature or none (docs/chore only).
    """
    content = skill_text()

    assert "4. **Scan for Features" in content
    assert "always run" in content.lower() or "Always run" in content
    assert "do not skip" in content.lower() or "Do not skip" in content
    # Classification vocabulary and outcome when no multi-feature split applies.
    assert "discrete **Features**" in content or "discrete Features" in content
    assert "none" in content.lower()  # record when none apply
    # Explicitly a separate step, not buried inside Plan/Implement.
    assert "separate step" in content.lower() or "its own numbered step" in content.lower() or "dedicated" in content.lower()


def test_general_guidelines_require_ordered_multi_feature_plan():
    """When multiple Features exist, plan implementation order before coding."""
    content = " ".join(skill_text().split())

    assert "two or more Features" in content or "multiple Features" in content
    assert "implementation order" in content
    # Dependencies first so intermediate commits stay buildable.
    assert "dependencies first" in content
    assert "buildable" in content or "working" in content


def test_general_guidelines_require_one_green_functional_commit_per_feature():
    """Each Feature is one self-contained commit that leaves the tree working."""
    content = " ".join(skill_text().split())

    assert "one self-contained" in content and "commit" in content
    # After each Feature commit the project must still work — no "broken until
    # the next commit" landings.
    assert "leave the program working" in content or "must still work" in content or "leaves the project" in content
    assert "Do not land a commit that only works after later" in content or (
        "only works after later" in content
    )


def test_general_guidelines_require_per_feature_verify_reload_and_logs():
    """After each Feature, verify with tests, always reapply/reload, and logs."""
    content = " ".join(skill_text().split())

    assert "Per-Feature verify" in content or "per-Feature verify" in content
    assert "monitor logs" in content or "Monitor logs" in content
    # Must happen before starting the next Feature.
    assert "before the next Feature" in content or "before starting the next" in content
    # Reload/reapply is mandatory after each Feature, not optional polish.
    assert "always reapply" in content.lower() or "Always reapply" in content


def test_general_guidelines_require_per_feature_commit_merge_and_reapply():
    """Each Feature must: commit on worktree → merge to master/main → reapply.

    Agents used to batch every Feature onto the worktree and merge only once at
    the end. The user-facing policy is step-by-step delivery: after each green
    Feature commit in the worktree, merge into the default branch and always
    reapply/reload consumers before starting the next Feature.
    """
    content = " ".join(skill_text().split())

    # Full delivery triad per Feature (not only after the last Feature).
    assert "after each Feature" in content.lower() or "After each Feature" in content
    assert "commit" in content.lower() and "worktree" in content.lower()
    assert "git merge --no-ff" in content
    assert "default branch" in content or "master/main" in content
    # Must not tell agents to keep mid-task Feature commits off master.
    assert "do not merge half-finished" not in content.lower()
    assert "mid-task Feature commits stay on the worktree" not in content
    # Reapply/reload is required every time, not deferred.
    assert "always reapply" in content.lower() or (
        "reapply" in content.lower() and "after each" in content.lower()
    )


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
    assert "git worktree add ../.worktrees/<repo>-wt-<task> -b <task-branch>" in content
    # Agents must prove cwd/branch before editing — create alone was not enough.
    assert "pwd" in content
    assert "git branch --show-current" in content
    assert "Hard gates before the first file edit" in content
    # Shared store is `.worktrees/` (leading dot), never bare `worktrees/`.
    assert "`.worktrees/` directory (leading dot)" in content
    assert "Never use `projects/worktrees/` (no dot)" in content
    # The Definition of Done must gate on the worktree too.
    assert "All edits were made on a dedicated git worktree branch" in content
    # Follow-up turns must not drift back to the live checkout.
    assert "Follow-up turns stayed in that same worktree" in " ".join(content.split())


def test_general_guidelines_description_shows_current_version_before_mandatory():
    """The skill picker must expose the current version before its mandate."""
    content = skill_text()

    assert "description: >-\n  v1.12.0 — Mandatory engineering workflow" in content


def test_general_guidelines_respect_project_agents_and_claude_first():
    """Repository AGENTS.md / CLAUDE.md outrank conflicting skill and agent defaults."""
    content = skill_text()

    assert "## Project instructions first" in content
    assert "`AGENTS.md`" in content
    assert "`CLAUDE.md`" in content
    assert "take precedence" in content
    # Project files come before the shared non-negotiables / Work Loop.
    assert content.index("## Project instructions first") < content.index(
        "## Start here — the non-negotiables"
    )


def test_general_guidelines_require_type_prefixed_worktree_names():
    """Worktree/branch names should use a conventional type prefix + feature."""
    content = " ".join(skill_text().split())

    assert "Name the worktree and branch with a type prefix" in content
    # Conventional types must be enumerated so agents pick the right one.
    for prefix in (
        "fix/", "feat/", "docs/", "refactor/", "test/", "chore/",
        "build/", "perf/", "ci/",
    ):
        assert prefix in content
    # The name must apply to both the branch and the worktree directory.
    assert "type/feature" in content
    assert "branch" in content and "worktree" in content


def test_general_guidelines_commit_finished_work_by_default():
    """Agents commit finished work without waiting to be asked."""
    content = " ".join(skill_text().split())

    assert "Commit your finished work by default" in content
    assert "you do not need to be asked" in content
    # Committing is default, but publishing to a remote still needs a request.
    assert "Never push, and never rewrite history" in content


def test_general_guidelines_require_commit_merge_reload_delivery():
    """Finished work must be committed, merged to the default branch, reloaded."""
    content = " ".join(skill_text().split())

    assert "Always finish the delivery step by step: commit in the worktree, merge into the default branch, then always reapply" in content
    assert "git merge --no-ff" in content
    assert "Deliver: commit, merge, reload" in content
    # Concrete merge recipe must live in the deliver step, not only Scope and Safety.
    assert "Merge into the default branch FROM the repository's live checkout" in content
    # Stopping after a worktree commit is explicitly a failure.
    assert "A worktree-only commit does **not** satisfy this item" in content
    assert 'Do not treat "do not push" as "do not merge."' in content
    # The Definition of Done must gate on the full delivery, not just the commit.
    assert (
        "The finished work was committed in the worktree, **merged into the default branch**"
        in content
    )
    assert "Nothing was pushed to a remote." in content


def test_wrapper_requires_worktree_proof_and_local_merge_not_push_ban():
    """The slim always-on wrapper must not contradict the full skill.

    Agents that only skim the wrapper used to see "never … merge into the default
    branch … unless the user asked," which blocked Step 8 delivery. The wrapper
    must require worktree proof and local merge while still banning remote push.
    """
    root = SKILL_PATH.resolve().parents[2]
    wrapper = (
        root / "global-instructions" / "general-programming-guidelines.md"
    ).read_text(encoding="utf-8")

    assert "pwd" in wrapper
    assert "git branch --show-current" in wrapper
    assert "git merge --no-ff" in wrapper
    assert "Local merge is required" in wrapper
    assert "`AGENTS.md`" in wrapper and "`CLAUDE.md`" in wrapper
    assert "Respect the repository's" in wrapper
    # Must not tell agents that merge requires user permission.
    assert "never push, merge into the default" not in wrapper.lower()
    assert "never push or rewrite" in wrapper.lower() or "Never push or rewrite" in wrapper
    # Must not claim the skill overrides project AGENTS/CLAUDE files.
    assert "not optional, a fallback, or overridden by a" not in wrapper


def test_general_guidelines_require_type_worktree_commit_messages():
    """Commit messages should be <type>(<worktree-name>): <summary>."""
    content = " ".join(skill_text().split())

    assert "Format each commit message as" in content
    assert "<type>(<worktree-name>): <summary>" in content
    # A concrete example ties the rule to the worktree name.
    assert "fix(worktree-policy): keep worktrees in the shared family store" in content


def test_wrapper_and_readme_versions_match_the_skill_version():
    """The bootstrap wrapper and README must not drift from the skill version.

    Hosts such as Grok read the always-on wrapper, not the skill front matter,
    so a stale wrapper version makes agents report a version mismatch.
    """
    root = SKILL_PATH.resolve().parents[2]

    skill_version = re.search(
        r"description: >-\n  v(\d+\.\d+\.\d+) — Mandatory", skill_text()
    )
    assert skill_version is not None, "skill description must declare a version"
    version = skill_version.group(1)

    wrapper = (
        root / "global-instructions" / "general-programming-guidelines.md"
    ).read_text(encoding="utf-8")
    assert f"## General Programming Guidelines v{version} (always on)" in wrapper
    assert f"These are v{version} MANDATORY instructions" in wrapper
    assert re.search(r"v(?!%s)\d+\.\d+\.\d+" % re.escape(version), wrapper) is None

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert f"Current version: **v{version}**." in readme
