"""Define the archive benchmark command-line interface."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .fsutil import load_json_lenient
from .harbor_copy import append_summary, archive_jobs_root, write_meta
from .paths import build_run_dirname
from .results_index import prepend_results_line, rebuild_results_index
from .self_test import _self_test

DESCRIPTION = "Archive a Harbor benchmark job tree into an inspectable runs/ folder."


def _build_parser() -> argparse.ArgumentParser:
    """Build the archive command parser.

    Parameters: none.

    Returns: configured argument parser.
    """
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    sub = parser.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="Create run directory + meta.json")
    init.add_argument("--runs-root", type=Path, required=True)
    init.add_argument("--timestamp", required=True)
    init.add_argument("--harness", action="append", default=[])
    init.add_argument("--mode", required=True)
    init.add_argument("--skill", action="append", default=[])
    init.add_argument("--separately", action="store_true")
    init.add_argument("--task", action="append", default=[])
    init.add_argument("--attempts", type=int, default=5)
    init.add_argument("--concurrent", type=int, default=5)
    init.add_argument("--eval-agent", action="append", default=[])
    init.add_argument("--jobs-temp", default="")
    init.add_argument("--command", default="")
    init.add_argument("--extra-json", default="")
    sync = sub.add_parser("sync-job", help="Archive one Harbor job into an existing run dir")
    sync.add_argument("--run-dir", type=Path, required=True)
    sync.add_argument("--jobs-root", type=Path, required=True)
    sync.add_argument("--job-name", required=True)
    sync.add_argument("--summary-file", type=Path, default=None)
    finalize = sub.add_parser("finalize", help="Archive all jobs + write combined summary")
    finalize.add_argument("--run-dir", type=Path, required=True)
    finalize.add_argument("--jobs-root", type=Path, required=True)
    finalize.add_argument("--summary-file", type=Path, default=None)
    sub.add_parser("self-test", help="Check Projects/ archive layout fixtures")
    index = sub.add_parser(
        "results-index",
        help="Rewrite runs/RESULTS.txt as an aligned table of every archived run (newest first)",
    )
    index.add_argument("--runs-root", type=Path, required=True)
    return parser


def _init_run(args: argparse.Namespace) -> int:
    """Create a run directory and metadata.

    Parameters: args - parsed init arguments.

    Returns: process exit code.
    """
    tasks = args.task or ["all"]
    dirname = build_run_dirname(
        timestamp=args.timestamp,
        harnesses=args.harness,
        mode=args.mode,
        skills=args.skill,
        separately=args.separately,
        tasks=tasks,
        attempts=args.attempts,
        concurrent=args.concurrent,
        eval_agents=args.eval_agent,
    )
    run_dir = args.runs_root / dirname
    meta = {
        "timestamp": args.timestamp,
        "harnesses": args.harness,
        "eval_agents": args.eval_agent,
        "eval_agent_inherit": not bool(args.eval_agent),
        "mode": args.mode,
        "skills": args.skill,
        "run_separately": bool(args.separately),
        "tasks": tasks,
        "attempts_per_task": args.attempts,
        "concurrent": args.concurrent,
        "jobs_dir": args.jobs_temp,
        "jobs_temp": args.jobs_temp,
        "command": args.command,
        "dirname": dirname,
    }
    if args.extra_json:
        try:
            meta["extra"] = json.loads(args.extra_json)
        except json.JSONDecodeError:
            meta["extra_raw"] = args.extra_json
    write_meta(run_dir, meta)
    if args.command:
        (run_dir / "02-command.txt").write_text(
            args.command.rstrip() + "\n", encoding="utf-8"
        )
    print(run_dir)
    return 0


def _copy_summary(source: Path | None, destinations: list[tuple[Path, bool]]) -> None:
    """Copy a summary to append or overwrite destinations.

    Parameters: source - optional summary file; destinations - destination and append-mode pairs.

    Returns: nothing.
    """
    if source is None or not source.is_file():
        return
    text = source.read_text(encoding="utf-8")
    for path, append in destinations:
        if append:
            append_summary(path.parent, text, name=path.name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")


def _sync_job(args: argparse.Namespace) -> int:
    """Archive one job into an existing run.

    Parameters: args - parsed sync-job arguments.

    Returns: process exit code.
    """
    archive_jobs_root(args.jobs_root, args.run_dir, only_job=args.job_name)
    _copy_summary(
        args.summary_file,
        [
            (args.run_dir / "01-SUMMARY.txt", True),
            (args.run_dir / "jobs" / args.job_name / "01-SUMMARY.txt", False),
        ],
    )
    print(args.run_dir)
    return 0


def _finalize(args: argparse.Namespace) -> int:
    """Finalize a run and update RESULTS.

    Parameters: args - parsed finalize arguments.

    Returns: process exit code.
    """
    archive_jobs_root(args.jobs_root, args.run_dir)
    if args.summary_file and args.summary_file.is_file():
        text = args.summary_file.read_text(encoding="utf-8")
        append_summary(args.run_dir, "\n" + text)
        (args.run_dir / "03-COMBINED-SUMMARY.txt").write_text(text, encoding="utf-8")
    meta = load_json_lenient(args.run_dir / "00-meta.json") or {}
    meta["archived_at"] = datetime.now(timezone.utc).isoformat()
    meta["jobs_dir"] = str(args.jobs_root)
    meta["jobs_temp"] = str(args.jobs_root)
    write_meta(args.run_dir, meta)
    prepend_results_line(args.run_dir.parent, args.run_dir)
    print(args.run_dir)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run the requested archive command.

    Parameters: argv - optional command arguments.

    Returns: process exit code.
    """
    args = _build_parser().parse_args(argv)
    if args.cmd == "init":
        return _init_run(args)
    if args.cmd == "sync-job":
        return _sync_job(args)
    if args.cmd == "finalize":
        return _finalize(args)
    if args.cmd == "self-test":
        return _self_test()
    if args.cmd == "results-index":
        print(rebuild_results_index(args.runs_root))
        return 0
    return 1
