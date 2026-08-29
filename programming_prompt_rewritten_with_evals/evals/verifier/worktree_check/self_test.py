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
from .rules import check_repo


def _feature(
    parent: Path,
    *,
    project: str = "app",
    store_project: str | None = None,
    store_name: str = ".worktrees",
    branch: str = "feat/calc",
    leaf: str = "feat-calc",
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


def run_self_test() -> int:
    """Build pass/fail fixtures and check all expected outcomes.

    Parameters: None.

    Returns: zero when every fixture matches its expectation, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, expect_ok: bool, repo: Path) -> None:
        """Record one checker result.

        Parameters: name - case name; expect_ok - expected state; repo - fixture checkout.

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
        merge_branch(repo, "feat/calc")
        record("pass_sibling_store", True, repo)

        repo, wt = _feature(
            root / "fail-unmerged", branch="feat/nomerge", leaf="feat-nomerge"
        )
        _commit_file(wt, message="feat(calc): unmerged")
        record("fail_unmerged", False, repo)

        repo, wt = _feature(
            root / "pass-merge", branch="feat/todo", leaf="feat-todo"
        )
        _commit_file(wt, "todo.py", "feat(todo): add todo")
        run_command(
            repo, "git", "merge", "--no-ff", "feat/todo", "-m", "Merge feat/todo"
        )
        record("pass_after_merge", True, repo)

        repo, wt = _feature(
            root / "pass-incremental",
            branch="feat/counter",
            leaf="feat-counter",
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
        merge_branch(repo, "feat/counter")
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
        wt = repo / ".worktrees" / "app" / "feat-x"
        add_worktree(repo, wt, "-b", "feat/inside")
        _commit_file(wt, message="inside repo")
        record("fail_worktree_inside_repo", False, repo)

        repo, wt = _feature(
            root / "fail-nodot", store_name="worktrees", branch="feat/nodot", leaf="feat-x"
        )
        _commit_file(wt, message="wrong store name")
        record("fail_worktrees_no_dot", False, repo)

        repo, wt = _feature(
            root / "fail-wrongname",
            store_project="other",
            branch="feat/wrongname",
            leaf="feat-x",
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
            root / "fail-empty-wt", branch="feat/empty", leaf="feat-empty"
        )
        record("fail_no_extra_commit", False, repo)

        repo, wt = _feature(
            root / "fail-remote", branch="feat/push", leaf="feat-push"
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
        wt = root / "fake-home" / ".worktrees" / "app" / "feat-x"
        add_worktree(repo, wt, "-b", "feat/home")
        _commit_file(wt, message="home store")
        record("fail_home_worktrees", False, repo)

        parent = root / "fail-nonempty-root"
        repo = parent / "app"
        repo.mkdir(parents=True)
        write_python(repo / "seed.py")
        run_command(repo, "git", "init", "-b", "master")
        run_command(repo, "git", "add", "seed.py")
        run_command(repo, "git", "commit", "-m", INITIAL_SUBJECT)
        wt = parent / ".worktrees" / "app" / "feat-x"
        add_worktree(repo, wt, "-b", "feat/seed")
        _commit_file(wt, message="later")
        record("fail_nonempty_initial_commit", False, repo)

        repo, wt = _feature(
            root / "fail-basename",
            project="calculator",
            store_project="app",
            branch="feat/basename",
            leaf="feat-x",
        )
        _commit_file(wt, message="basename mismatch")
        record("fail_store_not_matching_basename", False, repo)

        repo, wt = _feature(
            root / "pass-named",
            project="calculator",
            branch="feat/named",
            leaf="feat-x",
        )
        _commit_file(wt, message="named project")
        merge_branch(repo, "feat/named")
        record("pass_matching_project_name", True, repo)

        repo, wt = _feature(root / "Projects")
        _commit_file(wt)
        merge_branch(repo, "feat/calc")
        record("pass_projects_parent", True, repo)

    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} worktree check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} worktree check cases passed", flush=True)
    return 0
