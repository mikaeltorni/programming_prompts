"""Exercise every supported worktree-layout outcome."""

from __future__ import annotations

import tempfile
from pathlib import Path

from .fixtures import (
    INITIAL_SUBJECT,
    add_worktree,
    init_empty_repo,
    merge_branch,
    run_command,
    write_python,
)
from .naming import check_names
from .rules import check_repo


def _feature(
    parent: Path,
    *,
    project: str = "app",
    store_project: str | None = None,
    store_name: str = ".worktrees",
    branch: str = "feat/app_calc",
    leaf: str = "app_feat-calc",
) -> tuple[Path, Path]:
    """Create an empty repo and a feature worktree.

    Parameters: parent - fixture parent; project - repo basename; store_project - store project folder; store_name - store directory name; branch - feature branch; leaf - worktree leaf.

    Returns: live repository and worktree paths.
    """
    repo = parent / project
    init_empty_repo(repo)
    wt = parent / store_name / (store_project or project) / leaf
    add_worktree(repo, wt, "-b", branch)
    return repo, wt


def _commit_file(
    wt: Path,
    filename: str = "calculator.py",
    message: str = "feat(calc): add calculator",
    body: str = "def run():\n    return 1\n",
) -> None:
    """Commit one Python file in a fixture worktree.

    Parameters: wt - worktree; filename - relative file path; message - commit subject; body - Python source.

    Returns: None.
    """
    write_python(wt / filename, body)
    run_command(wt, "git", "add", filename)
    run_command(wt, "git", "commit", "-m", message)


# name, expected conformance, worktree leaf, branch, project basename.
_NAME_CASES: list[tuple[str, bool, str, str, str]] = [
    ("name_pass_project_prefix", True, "app_fix-parser", "fix/app_parser", "app"),
    ("name_pass_project_with_underscore", True, "programming_prompts_fix-parser",
     "fix/programming_prompts_parser", "programming_prompts"),
    ("name_fail_model_prefix", False, "codex-account-2_fix-parser",
     "fix/codex-account-2_parser", "app"),
    ("name_fail_foreign_project", False, "someone_fix-parser",
     "fix/someone_parser", "app"),
    ("name_fail_nested_branch", False, "app_fix-parser", "fix/app/parser", "app"),
    ("name_fail_empty_feature", False, "app_fix-", "fix/app_", "app"),
]


def run_self_test() -> int:
    """Build pass/fail fixtures and check all expected outcomes.

    Parameters: None.

    Returns: zero when every fixture matches its expectation, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(
        name: str,
        expect_ok: bool,
        repo: Path,
    ) -> None:
        """Record one checker result.

        Parameters: name - case name; expect_ok - expected state; repo - fixture
        checkout.

        Returns: None.
        """
        got = check_repo(repo)
        ok = got.ok == expect_ok
        detail = (
            got.reasoning
            if ok
            else f"expected ok={expect_ok} got ok={got.ok}: {got.reasoning}"
        )
        cases.append((name, ok, detail))

    with tempfile.TemporaryDirectory(prefix="worktree-check-") as raw:
        root = Path(raw)

        repo, wt = _feature(root / "pass-sibling")
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        record("pass_sibling_store", True, repo)

        repo, wt = _feature(
            root / "fail-unmerged", branch="feat/agent_nomerge", leaf="agent_feat-nomerge"
        )
        _commit_file(wt, message="feat(calc): unmerged")
        record("fail_unmerged", False, repo)

        repo, wt = _feature(
            root / "pass-merge", branch="feat/app_todo", leaf="app_feat-todo"
        )
        _commit_file(wt, "todo.py", "feat(todo): add todo")
        run_command(
            repo, "git", "merge", "--no-ff", "feat/app_todo", "-m", "Merge feat/app_todo"
        )
        record("pass_after_merge", True, repo)

        repo, wt = _feature(
            root / "pass-incremental",
            branch="feat/app_counter",
            leaf="app_feat-counter",
        )
        _commit_file(
            wt, "parse.py", "feat(counter): parse helper", "def parse(x):\n    return x\n"
        )
        _commit_file(
            wt,
            "counter.py",
            "feat(counter): entrypoint",
            "def run_counter(c):\n    return c\n",
        )
        merge_branch(repo, "feat/app_counter")
        record("pass_incremental_commits", True, repo)

        repo = root / "fail-norepo" / "app"
        repo.mkdir(parents=True)
        write_python(repo / "calculator.py", "x = 1\n")
        record("fail_no_repo", False, repo)

        repo = root / "fail-noworktree" / "app"
        init_empty_repo(repo)
        _commit_file(repo, message="add calculator on master")
        record("fail_no_worktree", False, repo)

        parent = root / "fail-inside"
        repo = parent / "app"
        init_empty_repo(repo)
        wt = repo / ".worktrees" / "app" / "app_feat-inside"
        add_worktree(repo, wt, "-b", "feat/app_inside")
        _commit_file(wt, message="inside repo")
        record("fail_worktree_inside_repo", False, repo)

        repo, wt = _feature(
            root / "fail-nodot",
            store_name="worktrees",
            branch="feat/app_nodot",
            leaf="app_feat-nodot",
        )
        _commit_file(wt, message="wrong store name")
        record("fail_worktrees_no_dot", False, repo)

        repo, wt = _feature(
            root / "fail-wrongname",
            store_project="other",
            branch="feat/app_wrongname",
            leaf="app_feat-wrongname",
        )
        _commit_file(wt, message="wrong project folder")
        record("fail_wrong_project_name", False, repo)

        parent = root / "fail-master-branch"
        repo = parent / "app"
        init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "linked-master"
        add_worktree(repo, wt, "--detach")
        record("fail_worktree_on_master", False, repo)

        repo, _ = _feature(
            root / "fail-empty-wt", branch="feat/app_empty", leaf="app_feat-empty"
        )
        record("fail_no_extra_commit", False, repo)

        repo, wt = _feature(
            root / "fail-remote", branch="feat/app_push", leaf="app_feat-push"
        )
        _commit_file(wt, message="feat")
        run_command(
            repo,
            "git",
            "remote",
            "add",
            "origin",
            "https://example.invalid/repo.git",
        )
        record("fail_has_remote", False, repo)

        parent = root / "fail-home"
        repo = parent / "app"
        init_empty_repo(repo)
        wt = root / "fake-home" / ".worktrees" / "app" / "app_feat-home"
        add_worktree(repo, wt, "-b", "feat/app_home")
        _commit_file(wt, message="home store")
        record("fail_home_worktrees", False, repo)

        parent = root / "fail-nonempty-root"
        repo = parent / "app"
        repo.mkdir(parents=True)
        write_python(repo / "seed.py")
        run_command(repo, "git", "init", "-b", "master")
        run_command(repo, "git", "add", "seed.py")
        run_command(repo, "git", "commit", "-m", INITIAL_SUBJECT)
        wt = parent / ".worktrees" / "app" / "app_feat-seed"
        add_worktree(repo, wt, "-b", "feat/app_seed")
        _commit_file(wt, message="later")
        record("fail_nonempty_initial_commit", False, repo)

        repo, wt = _feature(
            root / "fail-basename",
            project="calculator",
            store_project="app",
            branch="feat/app_basename",
            leaf="app_feat-basename",
        )
        _commit_file(wt, message="basename mismatch")
        record("fail_store_not_matching_basename", False, repo)

        repo, wt = _feature(
            root / "pass-named",
            project="calculator",
            branch="feat/calculator_named",
            leaf="calculator_feat-named",
        )
        _commit_file(wt, message="named project")
        merge_branch(repo, "feat/calculator_named")
        record("pass_matching_project_name", True, repo)

        repo, wt = _feature(root / "Projects")
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        record("pass_projects_parent", True, repo)

        repo, wt = _feature(
            root / "pass-multiword",
            branch="fix/app_parse-args",
            leaf="app_fix-parse-args",
        )
        _commit_file(wt, "parser.py", "fix(parser): parse args")
        merge_branch(repo, "fix/app_parse-args")
        record("pass_multiword_feature_slug", True, repo)

        repo, wt = _feature(
            root / "fail-leaf-noproject",
            branch="feat/agent_calc",
            leaf="feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/agent_calc")
        record("fail_leaf_without_project", False, repo)

        repo, wt = _feature(
            root / "fail-leaf-notype",
            branch="feat/agent_calc",
            leaf="agent_calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/agent_calc")
        record("fail_leaf_without_type", False, repo)

        repo, wt = _feature(
            root / "fail-branch-shape",
            branch="agent_feat-calc",
            leaf="agent_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "agent_feat-calc")
        record("fail_branch_without_type_prefix", False, repo)

        repo, wt = _feature(
            root / "fail-type-mismatch",
            branch="feat/agent_calc",
            leaf="agent_fix-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/agent_calc")
        record("fail_type_mismatch", False, repo)

        repo, wt = _feature(
            root / "fail-feature-mismatch",
            branch="feat/agent_parser",
            leaf="agent_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/agent_parser")
        record("fail_feature_mismatch", False, repo)

        repo, wt = _feature(
            root / "fail-project-mismatch",
            branch="feat/agent_calc",
            leaf="other_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/agent_calc")
        record("fail_project_mismatch", False, repo)

        repo, wt = _feature(root / "fail-stray-dir")
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        write_python(
            root / "fail-stray-dir" / ".worktrees" / "app" / "scratch" / "calc.py"
        )
        record("fail_unregistered_dir_in_store", False, repo)

        repo, wt = _feature(root / "fail-stray-file")
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        (root / "fail-stray-file" / ".worktrees" / "app" / "notes.txt").write_text(
            "scratch\n", encoding="utf-8"
        )
        record("fail_unregistered_file_in_store", False, repo)

        repo, wt = _feature(
            root / "fail-nested",
            leaf="nested/agent_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        record("fail_worktree_nested_below_store", False, repo)

        repo, wt = _feature(
            root / "pass-project-prefix",
            branch="feat/app_calc",
            leaf="app_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/app_calc")
        record("pass_project_prefix", True, repo)

        repo, wt = _feature(
            root / "fail-model-prefix",
            branch="feat/someone_calc",
            leaf="someone_feat-calc",
        )
        _commit_file(wt)
        merge_branch(repo, "feat/someone_calc")
        record("fail_model_prefix", False, repo)

    for name, expect_ok, leaf, branch, project in _NAME_CASES:
        problems = check_names(leaf, branch, project)
        ok = (not problems) == expect_ok
        detail = (
            "; ".join(problems) or "conforms"
            if ok
            else f"expected ok={expect_ok} got {problems or 'no problems'}"
        )
        cases.append((name, ok, detail))

    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} worktree check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} worktree check cases passed", flush=True)
    return 0
