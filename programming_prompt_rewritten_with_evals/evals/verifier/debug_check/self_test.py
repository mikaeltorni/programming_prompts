"""Exercise read-logs-first outcomes."""

from __future__ import annotations

import tempfile
from pathlib import Path

from worktree_check.fixtures import write_python

from .rules import check_repo, required_tokens


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

    with tempfile.TemporaryDirectory(prefix="debug-check-") as raw:
        root = Path(raw)

        none = root / "no-logs"
        none.mkdir()
        write_python(none / "greeter.py", "def run_greeter(c):\n    return c\n")
        record("pass_when_no_log_dir", True, none)

        empty = root / "empty-logs"
        empty.mkdir()
        (empty / ".log").mkdir()
        write_python(empty / "greeter.py", "def run_greeter(c):\n    return c\n")
        record("pass_when_log_dir_empty", True, empty)

        ok = root / "matched"
        ok.mkdir()
        log_dir = ok / ".log"
        log_dir.mkdir()
        (log_dir / "greeter.log").write_text(
            "ERROR hour=3 greeting=Good night\n"
            "expected hi=Good twilight\n"
            "require: twilight\n"
            "require: hi=\n",
            encoding="utf-8",
        )
        write_python(
            ok / "greeter.py",
            'def run_greeter(c):\n    return f"hi=Good twilight, Ada"\n',
        )
        record("pass_when_code_matches_log", True, ok)

        miss = root / "missing-token"
        miss.mkdir()
        miss_log = miss / ".log"
        miss_log.mkdir()
        (miss_log / "greeter.log").write_text("require: twilight\n", encoding="utf-8")
        write_python(
            miss / "greeter.py",
            'def run_greeter(c):\n    return "greeting=Good night"\n',
        )
        record("fail_when_code_ignores_log", False, miss)

        unmarked = root / "no-require"
        unmarked.mkdir()
        unmarked_log = unmarked / ".log"
        unmarked_log.mkdir()
        (unmarked_log / "app.log").write_text("ERROR something broke\n", encoding="utf-8")
        write_python(unmarked / "app.py", "x = 1\n")
        record("fail_logs_without_require_tokens", False, unmarked)

        tokens = required_tokens(ok / ".log")
        cases.append(
            (
                "parse_require_tokens",
                tokens == ["twilight", "hi="],
                f"parsed {tokens!r}",
            )
        )

    for name, ok, detail in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)
    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} debug check case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} debug check cases passed", flush=True)
    return 0
