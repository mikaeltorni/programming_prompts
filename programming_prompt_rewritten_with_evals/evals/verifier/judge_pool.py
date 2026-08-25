#!/usr/bin/env python3
"""Run independent Harbor judge subprocesses concurrently.

Each job is one eval-agent skill score or one programmatic checker. The
pool waits for every job; a non-zero child exit does not abort siblings.

Usage::

    python3 judge_pool.py jobs.json
    python3 judge_pool.py --workers 4 jobs.json
    python3 judge_pool.py --self-test

``jobs.json`` is a JSON list of ``{"label": "srp/codex", "argv": [...]}``
objects. Optional ``cwd`` is the child working directory. Stdout is the
JSON result list; diagnostics go to stderr. ``EVAL_JUDGE_WORKERS`` caps
the pool (default: **1**, so dual eval agents do not stampede rate limits).
``--self-test`` never launches a judge CLI or Harbor.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from llm_judge.log import log


@dataclass(frozen=True)
class JudgeJob:
    """One subprocess the verifier can run in the pool.

    Attributes:
        label: Skill or ``skill/evalAgent`` name for logs.
        argv: Command vector passed to ``subprocess.run``.
        cwd: Optional child working directory.
    """

    label: str
    argv: tuple[str, ...]
    cwd: str | None = None


@dataclass(frozen=True)
class JobResult:
    """Outcome of one pooled judge subprocess.

    Attributes:
        label: Same label as the job.
        returncode: Child exit code (127 when the binary could not start).
        elapsed_sec: Wall time for that child.
    """

    label: str
    returncode: int
    elapsed_sec: float

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable copy of this result."""
        return {
            "label": self.label,
            "returncode": self.returncode,
            "elapsed_sec": round(self.elapsed_sec, 3),
        }


def resolve_workers(job_count: int, requested: int | None = None) -> int:
    """Return the thread-pool size for *job_count* jobs.

    Args:
        job_count: Number of jobs about to run.
        requested: Explicit ``--workers`` value; ``None`` reads
            ``EVAL_JUDGE_WORKERS``. Unset, ``<= 0``, or invalid means **1**.

    Returns:
        At least 1, and never more than *job_count* (or 1 when empty).
    """
    if job_count <= 0:
        return 1
    value = requested
    if value is None:
        raw = os.environ.get("EVAL_JUDGE_WORKERS", "").strip()
        if raw:
            try:
                value = int(raw)
            except ValueError:
                log(f"pool ignoring invalid EVAL_JUDGE_WORKERS={raw!r}")
                value = None
    if value is None or value <= 0:
        chosen = 1
    else:
        chosen = max(1, min(int(value), job_count))
    log(f"pool workers={chosen} jobs={job_count}")
    return chosen


def load_jobs(path: Path) -> list[JudgeJob]:
    """Parse a JSON job list from *path*.

    Args:
        path: File written by ``run_judges.sh``.

    Returns:
        Jobs in file order.

    Raises:
        ValueError: Shape is not a list of label+argv objects.
        OSError: File cannot be read.
        json.JSONDecodeError: File is not JSON.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("jobs file must be a JSON list")
    jobs: list[JudgeJob] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"job {index} is not an object")
        label = str(item.get("label") or "").strip()
        argv_raw = item.get("argv")
        if not label:
            raise ValueError(f"job {index} is missing label")
        if not isinstance(argv_raw, list) or not argv_raw:
            raise ValueError(f"job {index} ({label}) needs a non-empty argv")
        argv = tuple(str(part) for part in argv_raw)
        cwd_raw = item.get("cwd")
        cwd = str(cwd_raw) if cwd_raw else None
        jobs.append(JudgeJob(label=label, argv=argv, cwd=cwd))
    return jobs


def _run_one(job: JudgeJob) -> JobResult:
    """Run *job* and return its result. Does not raise on child failure."""
    started = time.monotonic()
    log(f"pool start label={job.label}")
    try:
        completed = subprocess.run(
            list(job.argv),
            cwd=job.cwd,
            check=False,
        )
        code = int(completed.returncode)
    except OSError as exc:
        log(f"pool spawn-failed label={job.label} error={exc}")
        code = 127
    elapsed = time.monotonic() - started
    log(f"pool done label={job.label} rc={code} elapsed_s={elapsed:.1f}")
    return JobResult(label=job.label, returncode=code, elapsed_sec=elapsed)


def run_jobs(
    jobs: list[JudgeJob],
    workers: int | None = None,
) -> list[JobResult]:
    """Run *jobs* concurrently and return results in the original order.

    Args:
        jobs: Subprocesses to start.
        workers: Optional pool size; see ``resolve_workers``.

    Returns:
        One result per job, same order as *jobs*. Child failures are
        recorded, not raised.
    """
    if not jobs:
        log("pool empty job list")
        return []
    size = resolve_workers(len(jobs), workers)
    indexed: dict[int, JobResult] = {}
    with ThreadPoolExecutor(max_workers=size, thread_name_prefix="judge") as pool:
        futures = {pool.submit(_run_one, job): index for index, job in enumerate(jobs)}
        for future in as_completed(futures):
            index = futures[future]
            indexed[index] = future.result()
    return [indexed[index] for index in range(len(jobs))]


def _self_test() -> int:
    """Fixture jobs only — no Harbor, Codex, Claude Code, or Grok CLI."""
    cases: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))
        print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)

    check("workers_empty", resolve_workers(0) == 1, "empty list still has 1 worker")
    check("workers_default_one", resolve_workers(6, None) == 1, "unset workers = 1")
    check("workers_cap", resolve_workers(6, 100) == 6, "workers cannot exceed jobs")
    check("workers_floor", resolve_workers(6, 2) == 2, "positive cap is kept")
    os.environ["EVAL_JUDGE_WORKERS"] = "3"
    check("workers_env", resolve_workers(8) == 3, "EVAL_JUDGE_WORKERS caps the pool")
    os.environ["EVAL_JUDGE_WORKERS"] = "nope"
    check(
        "workers_bad_env",
        resolve_workers(4) == 1,
        "invalid EVAL_JUDGE_WORKERS falls back to 1",
    )
    os.environ.pop("EVAL_JUDGE_WORKERS", None)
    check("workers_zero_means_one", resolve_workers(5, 0) == 1, "0 workers = 1")

    try:
        load_jobs(Path("/no/such/jobs.json"))
        check("load_missing", False, "missing file should raise")
    except OSError:
        check("load_missing", True, "missing file raises OSError")

    with tempfile.TemporaryDirectory(prefix="judge-pool-") as raw:
        root = Path(raw)
        bad = root / "bad.json"
        bad.write_text('{"no": "list"}\n', encoding="utf-8")
        try:
            load_jobs(bad)
            check("load_not_list", False, "object payload should raise")
        except ValueError as exc:
            check("load_not_list", "JSON list" in str(exc), str(exc))
        empty_argv = root / "empty-argv.json"
        empty_argv.write_text(
            '[{"label": "srp/codex", "argv": []}]\n', encoding="utf-8"
        )
        try:
            load_jobs(empty_argv)
            check("load_empty_argv", False, "empty argv should raise")
        except ValueError:
            check("load_empty_argv", True, "empty argv is rejected")

        marker_a = root / "a.txt"
        marker_b = root / "b.txt"
        marker_c = root / "c.txt"
        fail_marker = root / "fail.txt"

        def sleep_argv(marker: Path, seconds: float, code: int) -> tuple[str, ...]:
            script = (
                "import pathlib, sys, time\n"
                f"pathlib.Path({str(marker)!r}).write_text(str(time.monotonic()))\n"
                f"time.sleep({seconds})\n"
                f"raise SystemExit({code})\n"
            )
            return (sys.executable, "-c", script)

        parallel = [
            JudgeJob("a", sleep_argv(marker_a, 0.3, 0)),
            JudgeJob("b", sleep_argv(marker_b, 0.3, 0)),
            JudgeJob("c", sleep_argv(marker_c, 0.3, 0)),
        ]
        started = time.monotonic()
        parallel_results = run_jobs(parallel, workers=3)
        parallel_elapsed = time.monotonic() - started
        check(
            "parallel_all_ok",
            all(item.returncode == 0 for item in parallel_results)
            and [item.label for item in parallel_results] == ["a", "b", "c"],
            "three overlapping jobs keep file order",
        )
        starts = [float(path.read_text(encoding="utf-8")) for path in (marker_a, marker_b, marker_c)]
        spread = max(starts) - min(starts)
        check(
            "parallel_overlap",
            spread < 0.2 and parallel_elapsed < 0.7,
            f"start spread={spread:.3f}s wall={parallel_elapsed:.3f}s",
        )

        mixed = [
            JudgeJob("ok", sleep_argv(root / "ok.txt", 0.05, 0)),
            JudgeJob("fail", sleep_argv(fail_marker, 0.05, 3)),
        ]
        mixed_results = run_jobs(mixed, workers=2)
        check(
            "failure_isolated",
            mixed_results[0].returncode == 0
            and mixed_results[1].returncode == 3
            and fail_marker.is_file(),
            "a failing child does not skip siblings",
        )

        seq = [
            JudgeJob("s1", sleep_argv(root / "s1.txt", 0.25, 0)),
            JudgeJob("s2", sleep_argv(root / "s2.txt", 0.25, 0)),
        ]
        seq_started = time.monotonic()
        run_jobs(seq, workers=1)
        seq_elapsed = time.monotonic() - seq_started
        check(
            "workers_one_is_serial",
            seq_elapsed >= 0.45,
            f"workers=1 wall={seq_elapsed:.3f}s",
        )

        empty_results = run_jobs([], workers=4)
        check("empty_jobs", empty_results == [], "no jobs returns []")

        good_file = root / "jobs.json"
        good_file.write_text(
            json.dumps(
                [
                    {
                        "label": "worktree",
                        "argv": [sys.executable, "-c", "raise SystemExit(0)"],
                    }
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        loaded = load_jobs(good_file)
        check(
            "load_ok",
            len(loaded) == 1 and loaded[0].label == "worktree",
            "round-trip jobs.json",
        )

        missing_bin = run_jobs(
            [JudgeJob("gone", ("/no/such/judge-binary",))],
            workers=1,
        )
        check(
            "spawn_failed",
            missing_bin[0].returncode == 127,
            "missing binary is rc=127",
        )

    failed = [name for name, ok, _ in cases if not ok]
    if failed:
        print(f"{len(failed)}/{len(cases)} judge-pool self-test(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} judge-pool self-tests passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--self-test`` or run the jobs file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Thread count (default: EVAL_JUDGE_WORKERS or 1)",
    )
    parser.add_argument("jobs_file", nargs="?", type=Path)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.jobs_file is None:
        parser.error("jobs_file is required unless --self-test")
    try:
        jobs = load_jobs(args.jobs_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        log(f"pool cannot load {args.jobs_file}: {exc}")
        print(f"judge_pool: cannot load {args.jobs_file}: {exc}", file=sys.stderr)
        return 2
    results = run_jobs(jobs, workers=args.workers)
    print(json.dumps([item.as_dict() for item in results], indent=2))
    failed = [item.label for item in results if item.returncode != 0]
    if failed:
        log(f"pool finished with failures: {', '.join(failed)}")
    else:
        log(f"pool finished ok jobs={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
