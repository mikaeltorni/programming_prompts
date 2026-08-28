"""Exercise feature-commit count outcomes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from worktree_check.fixtures import (
    add_worktree,
    init_empty_repo,
    merge_branch,
    run_command,
    write_python,
)

from .rules import SEED_SUBJECT, check_repo, read_required_features


def _commit_py(repo: Path, filename: str, message: str, body: str = "x = 1\n") -> None:
    """Commit one Python file on the current branch.

    Parameters: repo - git working tree; filename - relative path; message - subject; body - file contents.

    Returns: None.
    """
    write_python(repo / filename, body)
    run_command(repo, "git", "add", filename)
    run_command(repo, "git", "commit", "-m", message)


def run_self_test() -> int:
    """Build pass/fail fixtures and check all expected outcomes.

    Parameters: None.

    Returns: zero when every fixture matches its expectation, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, expect_ok: bool, repo: Path, required: int) -> None:
        """Record one checker result.

        Parameters: name - case name; expect_ok - expected state; repo - fixture checkout; required - Feature count.

        Returns: None.
        """
        got = check_repo(repo, required=required)
        ok = got.ok == expect_ok
        detail = (
            got.reasoning
            if ok
            else f"expected ok={expect_ok} got ok={got.ok}: {got.reasoning}"
        )
        cases.append((name, ok, detail))

    with tempfile.TemporaryDirectory(prefix="commits-check-") as raw:
        root = Path(raw)

        one = root / "one-feature" / "app"
        init_empty_repo(one)
        _commit_py(one, "shop.py", "feat(shop): catalog")
        record("pass_single_feature_one_commit", True, one, 1)

        two_short = root / "two-short" / "app"
        init_empty_repo(two_short)
        _commit_py(two_short, "shop.py", "feat(shop): everything")
        record("fail_two_features_one_commit", False, two_short, 2)

        two_ok = root / "two-ok" / "app"
        init_empty_repo(two_ok)
        _commit_py(two_ok, "catalog.py", "feat(shop): catalog")
        _commit_py(two_ok, "checkout.py", "feat(shop): checkout")
        record("pass_two_features_two_commits", True, two_ok, 2)

        seeded = root / "seeded" / "app"
        init_empty_repo(seeded)
        _commit_py(seeded, "greeter.py", SEED_SUBJECT, "def broken():\n    return 0\n")
        _commit_py(seeded, "catalog.py", "feat(shop): catalog")
        _commit_py(seeded, "checkout.py", "feat(shop): checkout")
        record("pass_skips_seed_commit", True, seeded, 2)

        seed_only = root / "seed-only" / "app"
        init_empty_repo(seed_only)
        _commit_py(seed_only, "greeter.py", SEED_SUBJECT)
        record("fail_seed_is_not_a_feature_commit", False, seed_only, 1)

        parent = root / "via-worktree"
        repo = parent / "app"
        init_empty_repo(repo)
        wt = parent / ".worktrees" / "app" / "feat-shop"
        add_worktree(repo, wt, "-b", "feat/shop")
        _commit_py(wt, "catalog.py", "feat(shop): catalog")
        _commit_py(wt, "checkout.py", "feat(shop): checkout")
        merge_branch(repo, "feat/shop")
        record("pass_after_worktree_merge", True, repo, 2)

        missing = root / "not-git" / "app"
        missing.mkdir(parents=True)
        record("fail_not_a_repo", False, missing, 1)

        count_file = root / "feature_count.txt"
        count_file.write_text("2\n", encoding="utf-8")
        got_n = read_required_features(count_file)
        cases.append(
            (
                "read_feature_count_file",
                got_n == 2,
                f"read {got_n} from feature_count.txt",
            )
        )
        cases.append(
            (
                "missing_feature_count_defaults_to_one",
                read_required_features(root / "no-such.txt") == 1,
                "missing file yields 1",
            )
        )

    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} commits check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} commits check cases passed", flush=True)
    return 0
