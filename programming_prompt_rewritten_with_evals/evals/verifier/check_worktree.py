#!/usr/bin/env python3
"""Programmatic worktree-layout checker for Harbor evals.

The live repo (Harbor: /app) must already be a git repository with an empty
initial commit. A valid agent run then:

* adds a worktree under ``<parent>/.worktrees/<project>/<dir>/`` (sibling of
  the repo, never inside it);
* commits finished program parts on a non-default branch in that worktree;
* never adds a remote or pushes.

This file is the judge. ``--self-test`` builds temporary fixtures for every
pass/fail layout the judge must distinguish and checks them here — not pytest.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


DEFAULT_REPO = Path("/app")
INITIAL_SUBJECT = "Initial empty commit"


@dataclass(frozen=True)
class CheckResult:
    """Outcome of one layout inspection.

    Attributes:
        ok: True when every worktree rule passed.
        reasoning: Short human-readable explanation for the verifier.
    """

    ok: bool
    reasoning: str


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command with ``repo`` as the working tree.

    Args:
        repo: Directory to use as git's working tree (``-C``).
        *args: Git subcommand and flags.

    Returns:
        Completed process with text stdout/stderr. Does not raise on
        non-zero exit; callers inspect ``returncode``.
    """
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _git_ok(repo: Path, *args: str) -> str:
    """Run git and return stripped stdout, or empty string on failure.

    Args:
        repo: Git working tree.
        *args: Git subcommand and flags.

    Returns:
        Stripped stdout, or ``""`` if git exited non-zero.
    """
    proc = _run_git(repo, *args)
    if proc.returncode != 0:
        return ""
    return proc.stdout.strip()


def expected_store(repo: Path) -> Path:
    """Return the required sibling worktree store for ``repo``.

    Args:
        repo: Resolved git toplevel (the project checkout).

    Returns:
        ``<parent>/.worktrees/<project-basename>``.
    """
    resolved = repo.resolve()
    return resolved.parent / ".worktrees" / resolved.name


def _parse_worktrees(repo: Path) -> list[dict[str, str]]:
    """Parse ``git worktree list --porcelain`` into dicts.

    Args:
        repo: Git working tree.

    Returns:
        One dict per worktree with keys such as ``worktree``, ``HEAD``,
        ``branch``. The main checkout is included.
    """
    proc = _run_git(repo, "worktree", "list", "--porcelain")
    if proc.returncode != 0:
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw_line in proc.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            if current:
                entries.append(current)
                current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    if current:
        entries.append(current)
    return entries


def _is_default_branch(branch: str) -> bool:
    """Return True if ``branch`` is master/main (with or without refs/heads/).

    Args:
        branch: Branch name from porcelain output.

    Returns:
        Whether this is the live default branch, which must not be the
        worktree's checkout.
    """
    name = branch.removeprefix("refs/heads/")
    return name in {"master", "main"}


def _root_commits(repo: Path) -> list[str]:
    """Return root commit hashes (empty-initial-commit candidates).

    Args:
        repo: Git working tree.

    Returns:
        Hashes from ``git rev-list --max-parents=0 HEAD``.
    """
    text = _git_ok(repo, "rev-list", "--max-parents=0", "HEAD")
    return [line for line in text.splitlines() if line]


def _commit_has_files(repo: Path, commit: str) -> bool:
    """Return True if ``commit`` introduces any file paths.

    Args:
        repo: Git working tree.
        commit: Commit hash.

    Returns:
        True when ``git diff-tree -r`` lists paths.
    """
    text = _git_ok(
        repo,
        "diff-tree",
        "--no-commit-id",
        "--name-only",
        "--root",
        "-r",
        commit,
    )
    return bool(text.strip())


def check_repo(repo: Path) -> CheckResult:
    """Inspect ``repo`` against the worktree eval contract.

    Args:
        repo: Project checkout that should already have been ``git init``'d
            with an empty initial commit (Harbor: ``/app``).

    Returns:
        Pass/fail plus a reasoning string the verifier stores.
    """
    repo = repo.resolve()
    if not (repo / ".git").exists() and _run_git(repo, "rev-parse", "--is-inside-work-tree").returncode != 0:
        return CheckResult(False, f"{repo} is not a git repository")

    if _git_ok(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return CheckResult(False, f"{repo} is not a git working tree")

    remotes = _git_ok(repo, "remote")
    if remotes:
        return CheckResult(
            False,
            f"git remotes are present ({remotes.replace(chr(10), ', ')}); never push in this eval",
        )

    roots = _root_commits(repo)
    if not roots:
        return CheckResult(False, "no root commit; expected git init plus an empty initial commit")
    for root in roots:
        if _commit_has_files(repo, root):
            return CheckResult(
                False,
                f"root commit {root[:12]} is not empty; the test must start from an empty initial commit",
            )

    store = expected_store(repo)
    store_resolved = store.resolve() if store.exists() else store
    extra: list[dict[str, str]] = []
    for entry in _parse_worktrees(repo):
        path_s = entry.get("worktree")
        if not path_s:
            continue
        path = Path(path_s).resolve()
        if path == repo:
            continue
        extra.append(entry)

    if not extra:
        return CheckResult(
            False,
            f"no git worktree besides the live checkout; expected one under {store}",
        )

    valid: list[tuple[Path, dict[str, str]]] = []
    problems: list[str] = []
    for entry in extra:
        path = Path(entry["worktree"]).resolve()
        try:
            path.relative_to(repo)
            inside = True
        except ValueError:
            inside = False
        if inside:
            problems.append(f"{path} is inside the project repo (must be a sibling .worktrees store)")
            continue
        try:
            path.relative_to(store_resolved)
            under_store = True
        except ValueError:
            under_store = False
        if not under_store:
            problems.append(
                f"{path} is not under {store} "
                f"(need <parent>/.worktrees/{repo.name}/<worktree>)"
            )
            continue
        branch = entry.get("branch", "")
        if not branch or _is_default_branch(branch):
            problems.append(
                f"{path} is on {branch or 'detached HEAD'}; worktree must use a feature branch, not master/main"
            )
            continue
        head = entry.get("HEAD") or _git_ok(path, "rev-parse", "HEAD")
        if not head:
            problems.append(f"{path} has no HEAD")
            continue
        count_text = _git_ok(path, "rev-list", "--count", "HEAD")
        try:
            count = int(count_text)
        except ValueError:
            count = 0
        if count < 2:
            problems.append(
                f"{path} has no commit after the empty initial commit; commit each finished part in the worktree"
            )
            continue
        changed = _git_ok(path, "diff-tree", "--no-commit-id", "--name-only", "-r", f"{roots[0]}..HEAD")
        if not changed.strip():
            problems.append(f"{path} commits after init do not add files")
            continue
        valid.append((path, entry))

    if valid:
        names = ", ".join(str(path) for path, _ in valid)
        return CheckResult(
            True,
            f"worktree(s) under {store}: {names}; empty initial commit kept; no remotes/push",
        )
    if problems:
        return CheckResult(False, "; ".join(problems))
    return CheckResult(False, f"no valid worktree under {store}")


def write_reward(result: CheckResult, output: Path) -> None:
    """Write Harbor/rewardkit-shaped reward JSON next to ``output``.

    Args:
        result: Checker outcome.
        output: Path for ``reward-<skill>.json`` (details go beside it).
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    reward = 1.0 if result.ok else 0.0
    raw = "yes" if result.ok else "no"
    output.write_text(json.dumps({"reward": reward}, indent=2) + "\n", encoding="utf-8")
    details = {
        "reward": {
            "score": reward,
            "criteria": [
                {
                    "name": "worktree_layout",
                    "value": reward,
                    "raw": raw,
                    "weight": 1.0,
                    "description": "sibling .worktrees/<project>/ worktree, incremental commits, no push",
                    "reasoning": result.reasoning,
                }
            ],
            "kind": "programmatic",
            "judge_output": json.dumps({"score": raw, "reasoning": result.reasoning}),
        }
    }
    details_path = output.parent / "reward-details.json"
    skill = output.name
    if skill.startswith("reward-") and skill.endswith(".json") and skill != "reward.json":
        inner = skill[len("reward-") : -len(".json")]
        if inner:
            details_path = output.parent / f"reward-{inner}-details.json"
    details_path.write_text(json.dumps(details, indent=2) + "\n", encoding="utf-8")
    # Rewardkit-style sibling name the verifier also looks for.
    sibling = output.parent / "reward-details.json"
    if details_path != sibling:
        sibling.write_text(json.dumps(details, indent=2) + "\n", encoding="utf-8")


def _git_env() -> dict[str, str]:
    """Return env with a local git identity for fixture repos."""
    env = os.environ.copy()
    env.setdefault("GIT_AUTHOR_NAME", "Eval")
    env.setdefault("GIT_AUTHOR_EMAIL", "eval@local")
    env.setdefault("GIT_COMMITTER_NAME", "Eval")
    env.setdefault("GIT_COMMITTER_EMAIL", "eval@local")
    return env


def _cmd(cwd: Path, *args: str) -> None:
    """Run a command in ``cwd`` and raise if it fails.

    Args:
        cwd: Working directory.
        *args: Command argv.
    """
    subprocess.run(list(args), cwd=str(cwd), check=True, env=_git_env(), capture_output=True, text=True)


def _init_empty_repo(repo: Path) -> None:
    """Create ``repo`` as a git repo with one empty initial commit.

    Args:
        repo: Directory to initialize (created if needed).
    """
    repo.mkdir(parents=True, exist_ok=True)
    _cmd(repo, "git", "init", "-b", "master")
    _cmd(repo, "git", "commit", "--allow-empty", "-m", INITIAL_SUBJECT)


def _add_worktree(repo: Path, path: Path, *git_args: str) -> None:
    """Create parent dirs and add a git worktree at ``path``.

    Args:
        repo: Main checkout.
        path: Worktree destination.
        *git_args: Extra args before the path (e.g. ``-b``, ``feat/x``).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    _cmd(repo, "git", "worktree", "add", *git_args, str(path))


def _write_py(path: Path, body: str = "def run():\n    return 1\n") -> None:
    """Write a tiny Python file.

    Args:
        path: Destination file.
        body: File contents.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _self_test() -> int:
    """Build every pass/fail fixture and assert the checker matches.

    Returns:
        0 when all cases match; 1 otherwise.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, expect_ok: bool, repo: Path) -> None:
        got = check_repo(repo)
        ok = got.ok == expect_ok
        cases.append((name, ok, got.reasoning if ok else f"expected ok={expect_ok} got ok={got.ok}: {got.reasoning}"))

    with tempfile.TemporaryDirectory(prefix="worktree-check-") as raw:
        root = Path(raw)

        # Pass: sibling .worktrees/<name>/feat-x with a real commit, no remote.
        parent = root / "pass-sibling"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-calc"
        _add_worktree(repo, wt, "-b", "feat/calc")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "feat(calc): add calculator")
        record("pass_sibling_store", True, repo)

        # Pass: same, then merge --no-ff back to master (worktree still present).
        parent = root / "pass-merge"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-todo"
        _add_worktree(repo, wt, "-b", "feat/todo")
        _write_py(wt / "todo.py")
        _cmd(wt, "git", "add", "todo.py")
        _cmd(wt, "git", "commit", "-m", "feat(todo): add todo")
        _cmd(repo, "git", "merge", "--no-ff", "feat/todo", "-m", "Merge feat/todo")
        record("pass_after_merge", True, repo)

        # Pass: two incremental worktree commits (parse then core).
        parent = root / "pass-incremental"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-counter"
        _add_worktree(repo, wt, "-b", "feat/counter")
        _write_py(wt / "parse.py", "def parse(x):\n    return x\n")
        _cmd(wt, "git", "add", "parse.py")
        _cmd(wt, "git", "commit", "-m", "feat(counter): parse helper")
        _write_py(wt / "counter.py", "def run_counter(c):\n    return c\n")
        _cmd(wt, "git", "add", "counter.py")
        _cmd(wt, "git", "commit", "-m", "feat(counter): entrypoint")
        record("pass_incremental_commits", True, repo)

        # Fail: not a git repo.
        parent = root / "fail-norepo"
        repo = parent / "app"
        repo.mkdir(parents=True)
        (repo / "calculator.py").write_text("x = 1\n", encoding="utf-8")
        record("fail_no_repo", False, repo)

        # Fail: repo with empty init only, files committed on master, no worktree.
        parent = root / "fail-noworktree"
        repo = parent / "app"
        _init_empty_repo(repo)
        _write_py(repo / "calculator.py")
        _cmd(repo, "git", "add", "calculator.py")
        _cmd(repo, "git", "commit", "-m", "add calculator on master")
        record("fail_no_worktree", False, repo)

        # Fail: worktree created inside the repo.
        parent = root / "fail-inside"
        repo = parent / "app"
        _init_empty_repo(repo)
        inside = repo / ".worktrees" / "app" / "feat-x"
        _add_worktree(repo, inside, "-b", "feat/inside")
        _write_py(inside / "calculator.py")
        _cmd(inside, "git", "add", "calculator.py")
        _cmd(inside, "git", "commit", "-m", "inside repo")
        record("fail_worktree_inside_repo", False, repo)

        # Fail: sibling store named worktrees/ (no leading dot).
        parent = root / "fail-nodot"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / "worktrees" / "app" / "feat-x"
        _add_worktree(repo, wt, "-b", "feat/nodot")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "wrong store name")
        record("fail_worktrees_no_dot", False, repo)

        # Fail: .worktrees/<wrong-project-name>/
        parent = root / "fail-wrongname"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "other" / "feat-x"
        _add_worktree(repo, wt, "-b", "feat/wrongname")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "wrong project folder")
        record("fail_wrong_project_name", False, repo)

        # Fail: worktree exists but stays on master.
        parent = root / "fail-master-branch"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "linked-master"
        _add_worktree(repo, wt, "--detach")
        record("fail_worktree_on_master", False, repo)

        # Fail: feature worktree but no commit after empty init.
        parent = root / "fail-empty-wt"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-empty"
        _add_worktree(repo, wt, "-b", "feat/empty")
        record("fail_no_extra_commit", False, repo)

        # Fail: remote configured (push possible).
        parent = root / "fail-remote"
        repo = parent / "app"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-push"
        _add_worktree(repo, wt, "-b", "feat/push")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "feat")
        _cmd(repo, "git", "remote", "add", "origin", "https://example.invalid/repo.git")
        record("fail_has_remote", False, repo)

        # Fail: worktree under $HOME/.worktrees (not sibling of this project).
        parent = root / "fail-home"
        repo = parent / "app"
        _init_empty_repo(repo)
        home_store = root / "fake-home" / ".worktrees" / "app" / "feat-x"
        _add_worktree(repo, home_store, "-b", "feat/home")
        _write_py(home_store / "calculator.py")
        _cmd(home_store, "git", "add", "calculator.py")
        _cmd(home_store, "git", "commit", "-m", "home store")
        record("fail_home_worktrees", False, repo)

        # Fail: root commit is not empty (files in the initial commit).
        parent = root / "fail-nonempty-root"
        repo = parent / "app"
        repo.mkdir(parents=True)
        _write_py(repo / "seed.py")
        _cmd(repo, "git", "init", "-b", "master")
        _cmd(repo, "git", "add", "seed.py")
        _cmd(repo, "git", "commit", "-m", INITIAL_SUBJECT)
        wt = parent / ".worktrees" / "app" / "feat-x"
        _add_worktree(repo, wt, "-b", "feat/seed")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "later")
        record("fail_nonempty_initial_commit", False, repo)

        # Fail: project folder name mismatch using a non-app basename.
        parent = root / "fail-basename"
        repo = parent / "calculator"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-x"
        _add_worktree(repo, wt, "-b", "feat/basename")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "basename mismatch")
        record("fail_store_not_matching_basename", False, repo)

        # Pass: non-app project name with matching store.
        parent = root / "pass-named"
        repo = parent / "calculator"
        _init_empty_repo(repo)
        wt = parent / ".worktrees" / "calculator" / "feat-x"
        _add_worktree(repo, wt, "-b", "feat/named")
        _write_py(wt / "calculator.py")
        _cmd(wt, "git", "add", "calculator.py")
        _cmd(wt, "git", "commit", "-m", "named project")
        record("pass_matching_project_name", True, repo)

    failed = [(name, msg) for name, ok, msg in cases if not ok]
    for name, ok, msg in cases:
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {msg}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} worktree check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} worktree check cases passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI: inspect a repo or run the built-in layout cases.

    Args:
        argv: Optional argv override.

    Returns:
        Process exit code (0 success).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="project checkout (default /app)")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/logs/verifier/reward-worktree.json"),
        help="reward JSON path",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run built-in pass/fail layout fixtures and exit",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = check_repo(args.repo)
    write_reward(result, args.output)
    print(f"worktree check: {'yes' if result.ok else 'no'} — {result.reasoning}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
