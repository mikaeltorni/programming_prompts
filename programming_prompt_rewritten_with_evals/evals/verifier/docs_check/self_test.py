"""Exercise docs-after-code outcomes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from worktree_check.fixtures import write_python

from .rules import check_repo, public_entrypoints


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

    with tempfile.TemporaryDirectory(prefix="docs-check-") as raw:
        root = Path(raw)

        missing = root / "no-readme"
        missing.mkdir()
        write_python(
            missing / "shop.py",
            "def run_shop(command: str) -> str:\n    return command\n",
        )
        record("fail_missing_readme", False, missing)

        empty = root / "empty-readme"
        empty.mkdir()
        write_python(
            empty / "shop.py",
            "def run_shop(command: str) -> str:\n    return command\n",
        )
        (empty / "README.md").write_text("\n", encoding="utf-8")
        record("fail_empty_readme", False, empty)

        no_entry = root / "no-entrypoint"
        no_entry.mkdir()
        write_python(
            no_entry / "shop.py",
            "def run_shop(command: str) -> str:\n    return command\n",
        )
        (no_entry / "README.md").write_text("# Shop\nA tiny catalog.\n", encoding="utf-8")
        record("fail_readme_omits_entrypoint", False, no_entry)

        ok = root / "ok"
        ok.mkdir()
        write_python(
            ok / "shop.py",
            "def parse_command(command: str):\n    return command\n"
            "def run_shop(command: str) -> str:\n    return command\n",
        )
        (ok / "README.md").write_text(
            "# Shop\n\nPublic entrypoint: run_shop.\nCommands: add <name> <price>, total.\n",
            encoding="utf-8",
        )
        record("pass_readme_names_entrypoint", True, ok)

        names = public_entrypoints(ok)
        cases.append(
            (
                "collects_run_entrypoint_only",
                names == ["run_shop"],
                f"entrypoints {names!r}",
            )
        )

        no_run = root / "no-run-def"
        no_run.mkdir()
        write_python(no_run / "util.py", "def helper():\n    return 1\n")
        (no_run / "README.md").write_text("Documents util.py usage.\n", encoding="utf-8")
        record("pass_readme_names_module_without_run", True, no_run)

        no_run_miss = root / "no-run-miss"
        no_run_miss.mkdir()
        write_python(no_run_miss / "util.py", "def helper():\n    return 1\n")
        (no_run_miss / "README.md").write_text("A helper module.\n", encoding="utf-8")
        record("fail_readme_omits_module_name", False, no_run_miss)

    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} docs check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} docs check cases passed", flush=True)
    return 0
