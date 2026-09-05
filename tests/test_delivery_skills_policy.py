"""Policy tests for the two delivery skills: `commits` and `worktree`.

The general programming guidelines delegate Feature commits to `commits` and
isolation/merge/reapply to `worktree`, so these two files are now the only
source of truth for those rules. This module pins the parts that agents get
wrong most often — above all the worktree store layout, which must group each
task directory under its own project name:

    <project-parent>/.worktrees/<project>/<instance>_<type-feature>

A store that drops the `<project>` component collapses every repository's
worktrees into one flat directory, where task names from different projects
collide. `tests/test_general_programming_guidelines_policy.py` covers the
guidelines side of the same split.
"""

from pathlib import Path


SKILLS_DIR = (
    Path(__file__).resolve().parents[1]
    / "programming_prompt_rewritten_with_evals"
    / "prompts"
    / "programming-skills"
)

WORKTREE_PATH = SKILLS_DIR / "worktree" / "SKILL.md"
COMMITS_PATH = SKILLS_DIR / "commits" / "SKILL.md"


def flat(path: Path) -> str:
    """Return the skill text with line wrapping collapsed to single spaces."""
    return " ".join(path.read_text(encoding="utf-8").split())


def test_worktree_store_groups_task_directories_by_project_name():
    """The store path must carry the project name between `.worktrees` and the task."""
    content = flat(WORKTREE_PATH)

    assert "`<project-parent>/.worktrees/<project>/<instance>_<type-feature>`" in content
    assert "`<project>` is the physical live checkout's basename" in content
    # The worked example must show the project directory, not a flat store.
    assert ".worktrees/ widget/ codex-account-2_fix-parser/" in content
    # The copyable recipe must build the path from the resolved project basename.
    assert 'PROJECT="$(basename "$REPO")"' in content
    assert 'WT="$PARENT/.worktrees/$PROJECT/${INSTANCE}_${TYPE}-${FEATURE}"' in content
    assert 'BRANCH="$TYPE/${INSTANCE}_${FEATURE}"' in content
    assert 'git -C "$REPO" worktree add -b "$BRANCH" "$WT"' in content


def test_worktree_store_rejects_flat_and_nested_stores():
    """Symlinks and nesting must not redirect the store away from the project group."""
    content = flat(WORKTREE_PATH)

    # Resolve symlinks so `/app -> /Projects/app` still groups under `/Projects`.
    assert "Resolve symlinks first" in content
    assert "never `/.worktrees/` or `/app/.worktrees/`" in content
    assert "no existing symlink redirects it into the live repository" in content
    # A linked worktree is not a new project and must not nest another store.
    assert "do not treat the worktree directory as a new project or nest another store below it" in content
    # Multi-repository tasks each get their own project group.
    assert "create a worktree in each project's own `.worktrees/<project>/` group" in content
    assert "Never use `worktrees/` without the dot, or put the store inside a repository" in content


def test_worktree_instance_component_identifies_the_agent_home():
    """`<instance>` comes from the runtime home basename and stays branch-safe."""
    content = flat(WORKTREE_PATH)

    assert "`<instance>` identifies the agent home in use" in content
    assert "CODEX_HOME or CLAUDE_CONFIG_DIR" in content
    assert "Do not guess an account number" in content
    # Sanitizing keeps the instance valid as a Git branch component.
    assert "Strip leading dots and replace characters outside letters, digits, hyphens, and underscores" in content
    assert "use `agent` if empty" in content
    assert "Never use the full home path" in content


def test_worktree_owns_per_feature_merge_and_reapply():
    """Delivery per Feature: commit, merge --no-ff, verify ancestry, reapply."""
    content = flat(WORKTREE_PATH)

    assert "never make feature, fix, or documentation commits on the live default branch" in content
    assert "Determine the actual default branch from repository metadata" in content
    assert 'git merge --no-ff "$BRANCH"' in content
    assert 'git merge-base --is-ancestor "$(git -C "$WT" rev-parse HEAD)" HEAD' in content
    assert "Reapply the merged change through the project's installer, skill selector" in content
    assert "Every later commit, including a docs-only correction, needs its own merge and reapply" in content
    # Local delivery is required; publishing still is not.
    assert "Never push, publish, add remotes, or rewrite history unless the user explicitly requests it" in content


def test_worktree_defers_feature_splitting_to_the_commits_skill():
    """The two delivery skills must not restate each other's policy."""
    worktree = flat(WORKTREE_PATH)
    commits = flat(COMMITS_PATH)

    assert "Feature splitting and commit contents belong to the commits skill" in worktree
    assert "worktree location and merge policy belong to the applicable project instructions" in commits
    # The commits skill must not define its own store layout.
    assert ".worktrees/" not in commits


def test_commits_skill_requires_one_verified_commit_per_ledger_entry():
    """Each capability sentence becomes one ledger entry and one verified commit."""
    content = flat(COMMITS_PATH)

    assert "Copy each capability sentence verbatim into its own entry" in content
    assert 'A following "It should also …" sentence starts a new Feature' in content
    assert "Do not merge adjacent ledger entries" in content
    # The commit gate: verify, stage only this entry, commit as its own command.
    assert "Stage only its changes in the worktree" in content
    assert "Run `git commit` as its own command" in content
    assert "Read the new `HEAD`, confirm it advanced" in content
    assert "A statement that a Feature is tested or complete is not a commit" in content
    # No batching and no history rewriting to repair a commit.
    assert "Do not batch missing entries into one final commit" in content
    assert "Never rewrite history to repair a commit" in content


COMMIT_PLUGIN_PATH = (
    Path(__file__).resolve().parents[1]
    / "plugins"
    / "commit-guidelines"
    / "skills"
    / "commit"
    / "SKILL.md"
)


def test_commit_plugin_declares_the_salvage_scope_that_separates_it_from_commits():
    """The `commit` plugin and the `commits` skill must not rival each other.

    Both create commits and their names differ by one letter, so an agent with
    both selected could follow either. They disagree on where a commit boundary
    comes from: `commit` reads it out of an existing diff, `commits` decides it
    from the request before the diff exists. The plugin therefore has to state
    which situation it owns and hand the other one over.
    """
    content = flat(COMMIT_PLUGIN_PATH)

    assert "## Scope, and how this differs from the `commits` skill" in content
    # It owns pre-existing changes it did not author.
    assert "This skill is the **salvage** path" in content
    assert "You did not author those changes in this session" in content
    # Authoring hands over to `commits`, including the tie-break.
    assert "The separately selected `commits` skill is the **authoring** path" in content
    assert "Session is authoring the change → follow `commits`" in content
    assert "`commits` wins for anything it has a ledger entry for" in content
    # The description must carry the boundary too, since selection reads it first.
    assert "the `commits` skill owns that" in content


def test_commit_plugin_defers_isolation_to_the_worktree_skill():
    """Its validation checkout must not read as a competing worktree policy.

    The plugin creates a temporary detached worktree to test a staged snapshot.
    Without a boundary that looks like a second worktree layout rule, so it has
    to name `worktree` as the owner and mark its own checkout as throwaway.
    """
    content = flat(COMMIT_PLUGIN_PATH)

    assert (
        "Isolation, branch policy, merging, and reapplication belong to the `worktree` skill"
        in content
    )
    assert "a throwaway validation checkout, not a task worktree" in content
    assert "create it outside the repository and remove it in the same step" in content
