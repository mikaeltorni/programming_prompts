"""Exercise archive layout and results-index behavior."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .harbor_copy import archive_jobs_root, write_meta
from .results_index import (
    format_runtime,
    looks_like_results_table,
    parse_results_table,
    prepend_results_line,
    rebuild_results_index,
    run_elapsed_seconds,
)


def _git(cwd: Path, *args: str) -> None:
    """Run git with a local identity for archive fixtures.

    Parameters: cwd - fixture repository; args - git arguments.

    Returns: nothing.
    """
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Eval Agent"
    env["GIT_AUTHOR_EMAIL"] = "eval@local"
    env["GIT_COMMITTER_NAME"] = "Eval Agent"
    env["GIT_COMMITTER_EMAIL"] = "eval@local"
    subprocess.run(
        [
            "git", "-C", str(cwd),
            "-c", "user.email=eval@local",
            "-c", "user.name=Eval Agent",
            *args,
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def _write_results_fixture(
    runs_root: Path,
    stamp: str,
    *,
    mode: str,
    harness: str,
    eval_agent: str,
    overall: float,
    skill_ok: float,
    started_at: str,
    archived_at: str,
) -> Path:
    """Create one archived run for results-index checks.

    Parameters: runs_root - temporary runs root; stamp - run timestamp; mode - benchmark mode; harness - harness name; eval_agent - judge name; overall - overall reward; skill_ok - SRP reward; started_at - ISO start; archived_at - ISO end.

    Returns: fixture run directory.
    """
    run_dir = runs_root / f"{stamp}__harness-{harness}__mode-{mode}"
    trial = run_dir / "jobs" / f"{harness}-skills" / "trials" / "calculator__abc"
    trial.mkdir(parents=True)
    (trial / "01-reward.json").write_text(
        json.dumps({"reward": overall}) + "\n", encoding="utf-8"
    )
    (trial / "03-reward-srp.json").write_text(
        json.dumps({"reward": skill_ok}) + "\n", encoding="utf-8"
    )
    (trial / "03-reward-srp-codex.json").write_text(
        json.dumps({"reward": skill_ok}) + "\n", encoding="utf-8"
    )
    write_meta(
        run_dir,
        {
            "timestamp": stamp,
            "harnesses": [harness],
            "eval_agents": [eval_agent],
            "mode": mode,
            "skills": ["srp"],
            "tasks": ["calculator"],
            "attempts_per_task": 5,
            "concurrent": 5,
            "run_separately": False,
            "started_at": started_at,
            "archived_at": archived_at,
        },
    )
    return run_dir


def _check_projects(record) -> None:
    """Run Projects archive fixture checks.

    Parameters: record - case-recording callback.

    Returns: nothing.
    """
    with tempfile.TemporaryDirectory(prefix="archive-projects-") as raw:
        root = Path(raw)
        job = root / "harbor" / "cc-skills"
        trial = job / "calculator__abc123"
        artifacts = trial / "artifacts" / "Projects"
        app = artifacts / "app"
        wt = artifacts / ".worktrees" / "app" / "feat-calculator"
        trial.mkdir(parents=True)
        (trial / "result.json").write_text("{}\n", encoding="utf-8")
        (trial / "verifier").mkdir()
        (trial / "verifier" / "reward.json").write_text(
            '{"reward": 1.0}\n', encoding="utf-8"
        )
        app.mkdir(parents=True)
        _git(app, "init", "-b", "master")
        _git(app, "commit", "--allow-empty", "-m", "Initial empty commit")
        wt.parent.mkdir(parents=True)
        _git(app, "worktree", "add", "-b", "feat/calculator", str(wt))
        (wt / "calculator.py").write_text(
            "def run_calculator(c):\n    return c\n", encoding="utf-8"
        )
        _git(wt, "add", "calculator.py")
        _git(wt, "commit", "-m", "feat(calculator): add calculator")
        _git(app, "merge", "--no-ff", "feat/calculator", "-m", "Merge feat/calculator")
        record(
            "fixture_merged_clone",
            (app / "calculator.py").is_file(),
            "clone has merged file before archive"
            if (app / "calculator.py").is_file()
            else "expected calculator.py in clone after merge",
        )
        run_dir = root / "run"
        archive_jobs_root(root / "harbor", run_dir)
        dest_app = run_dir / "Projects" / trial.name / "app"
        dest_wt = (
            run_dir / "Projects" / trial.name / ".worktrees" / "app" / "feat-calculator"
        )
        dest_code = (
            run_dir / "jobs" / "cc-skills" / "trials" / trial.name / "code"
            / "calculator.py"
        )
        record("projects_clone_exists", dest_app.is_dir(), str(dest_app))
        record(
            "clone_reset_empty",
            dest_app.is_dir() and not (dest_app / "calculator.py").exists(),
            "cloned app must be the empty initial commit, not the merge",
        )
        record(
            "worktree_has_code",
            (dest_wt / "calculator.py").is_file(),
            str(dest_wt / "calculator.py"),
        )
        record("jobs_code_copy", dest_code.is_file(), str(dest_code))


def _check_results(record) -> None:
    """Run results-index fixture checks.

    Parameters: record - case-recording callback.

    Returns: nothing.
    """
    record("runtime_format_zero", format_runtime(0) == "0h 00m 00s", format_runtime(0))
    record("runtime_format_hms", format_runtime(3723) == "1h 02m 03s", format_runtime(3723))
    record(
        "runtime_format_long",
        format_runtime(2 * 3600 + 15 * 60 + 3) == "2h 15m 03s",
        format_runtime(2 * 3600 + 15 * 60 + 3),
    )
    record("runtime_format_missing", format_runtime(None) == "-", format_runtime(None))
    local_tz = datetime.now().astimezone().tzinfo
    stamp_start = datetime(2026, 8, 16, 10, 0, 0, tzinfo=local_tz)
    stamp_end = stamp_start + timedelta(hours=0, minutes=9, seconds=3)
    stamp_elapsed = run_elapsed_seconds(
        {
            "timestamp": "2026-08-16_100000_99",
            "archived_at": stamp_end.astimezone(timezone.utc).isoformat(),
        }
    )
    record(
        "runtime_from_stamp",
        format_runtime(stamp_elapsed) == "0h 09m 03s",
        format_runtime(stamp_elapsed),
    )
    in_progress = run_elapsed_seconds(
        {"started_at": "2026-08-16T10:00:00+00:00"},
        now=datetime(2026, 8, 16, 11, 2, 3, tzinfo=timezone.utc),
    )
    record(
        "runtime_in_progress_uses_now",
        format_runtime(in_progress) == "1h 02m 03s",
        format_runtime(in_progress),
    )
    with tempfile.TemporaryDirectory(prefix="archive-mtime-") as raw_mtime:
        mtime_root = Path(raw_mtime)
        stale = _write_results_fixture(
            mtime_root, "2026-08-16_100000_mtime", mode="positive",
            harness="codex", eval_agent="codex", overall=1.0, skill_ok=1.0,
            started_at="2026-08-16T10:00:00+00:00",
            archived_at="2026-08-16T10:00:01+00:00",
        )
        summary = stale / "01-SUMMARY.txt"
        summary.write_text("summary\n", encoding="utf-8")
        start_ts = datetime(2026, 8, 16, 10, 0, 0, tzinfo=timezone.utc).timestamp()
        os.utime(summary, (start_ts + 14 * 60, start_ts + 14 * 60))
        mtime_index = rebuild_results_index(mtime_root)
        mtime_rows = parse_results_table(mtime_index.read_text(encoding="utf-8"))
        record(
            "runtime_from_summary_mtime",
            bool(mtime_rows) and mtime_rows[0]["Runtime"] == "0h 14m 00s",
            mtime_rows[0].get("Runtime", "") if mtime_rows else "missing",
        )
    with tempfile.TemporaryDirectory(prefix="archive-results-") as raw:
        runs_root = Path(raw)
        _write_results_fixture(
            runs_root, "2026-08-16_100000_1", mode="baseline",
            harness="codex", eval_agent="cc", overall=0.0, skill_ok=0.0,
            started_at="2026-08-16T10:00:00+00:00",
            archived_at="2026-08-16T10:09:03+00:00",
        )
        _write_results_fixture(
            runs_root, "2026-08-16_110000_2", mode="positive",
            harness="grok", eval_agent="grok", overall=1.0, skill_ok=1.0,
            started_at="2026-08-16T11:00:00+00:00",
            archived_at="2026-08-16T12:02:03+00:00",
        )
        index = rebuild_results_index(runs_root)
        text = index.read_text(encoding="utf-8")
        rows = parse_results_table(text)
        record(
            "results_newest_first",
            len(rows) == 2 and rows[0]["Run"] == "2026-08-16_110000_2",
            f"rows={len(rows)} first={rows[0]['Run'] if rows else ''}",
        )
        record(
            "results_has_header",
            looks_like_results_table(text) and text.splitlines()[0].startswith("Run"),
            text.splitlines()[0] if text else "missing",
        )
        headers = [cell.strip() for cell in text.splitlines()[0].split(" | ")]
        record(
            "results_runtime_between_run_and_mode",
            headers[:3] == ["Run", "Runtime", "Mode"],
            str(headers[:5]),
        )
        record(
            "results_runtime_hms",
            bool(rows)
            and rows[0]["Runtime"] == "1h 02m 03s"
            and rows[1]["Runtime"] == "0h 09m 03s",
            f"{rows[0].get('Runtime') if rows else ''} {rows[1].get('Runtime') if len(rows) > 1 else ''}",
        )
        record(
            "results_table_pass",
            rows[0]["Pass"] == "1/1"
            and rows[0]["srp"] == "1/1"
            and rows[0]["calculator"] == "1/1"
            and rows[0]["Mode"] == "positive"
            and rows[0]["Harness"] == "grok"
            and rows[0]["Judge"] == "grok",
            str(rows[0]) if rows else "missing",
        )
        record(
            "results_skips_agent_skill_file",
            "srp-codex" not in text.splitlines()[0],
            "per-agent 03-reward-srp-codex.json is not a column",
        )
        record(
            "results_baseline_fail",
            rows[1]["Pass"] == "0/1" and rows[1]["Mode"] == "baseline",
            str(rows[1]) if len(rows) > 1 else "missing",
        )
        extra = _write_results_fixture(
            runs_root, "2026-08-16_120000_3", mode="positive",
            harness="codex", eval_agent="codex", overall=1.0, skill_ok=1.0,
            started_at="2026-08-16T12:00:00+00:00",
            archived_at="2026-08-16T14:15:03+00:00",
        )
        prepend_results_line(runs_root, extra)
        prepend_results_line(runs_root, extra)
        rows = parse_results_table(index.read_text(encoding="utf-8"))
        record(
            "results_prepend_dedupes",
            len(rows) == 3 and rows[0]["Run"] == "2026-08-16_120000_3",
            f"rows={len(rows)} first={rows[0]['Run'] if rows else ''}",
        )
        record(
            "results_prepend_runtime",
            bool(rows) and rows[0]["Runtime"] == "2h 15m 03s",
            rows[0].get("Runtime", "") if rows else "missing",
        )
        record(
            "results_body_below_header",
            index.read_text(encoding="utf-8").splitlines()[2].startswith(
                "2026-08-16_120000_3"
            ),
            "newest data row sits under the header",
        )
        index.write_text(
            "2026-08-11_old mode=positive harness=codex pass=1/1\n",
            encoding="utf-8",
        )
        prepend_results_line(runs_root, extra)
        replaced = index.read_text(encoding="utf-8")
        record(
            "results_replaces_legacy",
            looks_like_results_table(replaced)
            and "mode=positive" not in replaced.splitlines()[0]
            and len(parse_results_table(replaced)) == 1
            and parse_results_table(replaced)[0]["Run"] == "2026-08-16_120000_3",
            "legacy one-liners are wiped",
        )


def _self_test() -> int:
    """Run all archive fixture checks.

    Parameters: none.

    Returns: zero when all existing cases pass, otherwise one.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

    _check_projects(record)
    _check_results(record)
    failed = [(name, msg) for name, ok, msg in cases if not ok]
    for name, ok, msg in cases:
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {msg}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} archive layout case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} archive layout cases passed", flush=True)
    return 0
