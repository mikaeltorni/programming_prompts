#!/usr/bin/env python3
"""Archive a Harbor benchmark job tree into an inspectable runs/ folder.

Layout (explorer-friendly, timestamp-first directory name):

  evals/runs/
    YYYY-MM-DD_HHMMSS__harness-…__mode-…__skills-…__separately-…__kN-nN/
      00-meta.json
      01-SUMMARY.txt
      02-command.txt
      Projects/<trial-name>/
        app/                    # cloned repo reset to the empty initial commit
        .worktrees/<project>/<dir>/   # worktree files (the actual work)
      harbor/                   # raw Harbor -o output (not /tmp)
      jobs/<job-name>/
        00-job-result.json
        00-harbor-config.yaml   # when present next to the job
        01-SUMMARY.txt
        trials/<trial-name>/
          00-trial-result.json
          01-reward.json
          02-reward-details.json
          03-reward-<skill>.json
          03-reward-<skill>-details.json
          10-test-stdout.txt
          20-exception.txt
          code/*.py
          agent/<log files>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _safe_slug(value: str, *, max_len: int = 80) -> str:
    text = value.strip().lower()
    text = re.sub(r"[^a-z0-9._+-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    if not text:
        return "na"
    return text[:max_len]


def build_run_dirname(
    *,
    timestamp: str,
    harnesses: list[str],
    mode: str,
    skills: list[str],
    separately: bool,
    tasks: list[str],
    attempts: int,
    concurrent: int,
    extra: str = "",
) -> str:
    """Build a lexicographically timestamp-sorted run directory name."""
    harness_part = "+".join(_safe_slug(h) for h in harnesses) or "na"
    skills_part = "+".join(_safe_slug(s) for s in skills) or "all"
    if not tasks or tasks == ["all"]:
        tasks_part = "all"
    else:
        tasks_part = "+".join(_safe_slug(t) for t in tasks)
        if len(tasks_part) > 60:
            tasks_part = f"{len(tasks)}-tasks"
    parts = [
        timestamp,
        f"harness-{harness_part}",
        f"mode-{_safe_slug(mode)}",
        f"skills-{skills_part}",
        f"separately-{'yes' if separately else 'no'}",
        f"tasks-{tasks_part}",
        f"k{attempts}-n{concurrent}",
    ]
    if extra:
        parts.append(_safe_slug(extra))
    return "__".join(parts)


def _load_json_lenient(path: Path) -> dict | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    if "[REDACTED]" in text:
        text = re.sub(
            r'("reward"\s*:\s*)\[REDACTED\](\.0\b)?',
            lambda m: f"{m.group(1)}1{m.group(2) or ''}",
            text,
        )
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


SKIP_JOB_DIR_NAMES = {
    "task-trees",
    "generated-negative-skill",
    "generated-negative-tasks",
    "Projects",
    "harbor",
    "jobs",
}


def _copy_tree(src: Path, dest: Path) -> None:
    """Copy a directory tree, replacing *dest* if it already exists."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(src, dest, symlinks=True, ignore_dangling_symlinks=True)


def _projects_source(artifacts: Path) -> Path | None:
    """Return the directory that holds ``app/`` and/or ``.worktrees/``.

    Harbor stores ``--artifact /Projects`` as ``artifacts/Projects/``. Older
    jobs stored ``--artifact /app`` as ``artifacts/app/``.
    """
    if not artifacts.is_dir():
        return None
    nested = artifacts / "Projects"
    if nested.is_dir() and ((nested / "app").exists() or (nested / ".worktrees").exists()):
        return nested
    if (artifacts / "app").exists() or (artifacts / ".worktrees").exists():
        return artifacts
    return None


def _reset_clone_to_initial(repo: Path) -> None:
    """Reset a copied git checkout to its empty initial commit.

    The archived ``Projects/<trial>/app`` folder is the cloned initial state.
    Work lives next to it under ``.worktrees/``.
    """
    if not (repo / ".git").exists():
        return
    proc = subprocess.run(
        ["git", "-C", str(repo), "rev-list", "--max-parents=0", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    roots = [line.strip() for line in (proc.stdout or "").splitlines() if line.strip()]
    if proc.returncode != 0 or not roots:
        return
    subprocess.run(
        ["git", "-C", str(repo), "reset", "--hard", roots[0]],
        check=False,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "clean", "-fd"],
        check=False,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "prune"],
        check=False,
        capture_output=True,
        text=True,
    )
    extra = repo / ".git" / "worktrees"
    if extra.is_dir():
        shutil.rmtree(extra, ignore_errors=True)


def archive_projects_layout(trial_dir: Path, dest_projects: Path) -> bool:
    """Copy one trial's simulated ``Projects/`` tree (clone + worktrees).

    Args:
        trial_dir: Harbor trial directory that contains ``artifacts/``.
        dest_projects: Destination ``<run>/Projects/<trial>/`` folder.

    Returns:
        True when a Projects tree was written.
    """
    source = _projects_source(trial_dir / "artifacts")
    if source is None:
        return False
    dest_projects.mkdir(parents=True, exist_ok=True)
    src_app = source / "app"
    src_wt = source / ".worktrees"
    if src_app.exists():
        _copy_tree(src_app, dest_projects / "app")
        _reset_clone_to_initial(dest_projects / "app")
    if src_wt.exists():
        _copy_tree(src_wt, dest_projects / ".worktrees")
    return (dest_projects / "app").exists() or (dest_projects / ".worktrees").exists()


def _flatten_code_rel(rel: Path) -> Path:
    """Map an artifacts-relative path to a flat ``code/`` path."""
    parts = rel.parts
    if not parts:
        return rel
    if parts[0] == "Projects":
        parts = parts[1:]
    if parts and parts[0] == "app":
        return Path(*parts[1:]) if len(parts) > 1 else Path(rel.name)
    if ".worktrees" in parts:
        return Path(rel.name)
    return Path(*parts)


def archive_trial(
    trial_dir: Path,
    dest_trial: Path,
    *,
    projects_root: Path | None = None,
) -> dict:
    """Copy one Harbor trial into a sorted, inspectable folder."""
    dest_trial.mkdir(parents=True, exist_ok=True)
    info: dict[str, object] = {"trial": trial_dir.name, "files": []}

    mapping = [
        ("result.json", "00-trial-result.json"),
        ("exception.txt", "20-exception.txt"),
        ("trial.log", "21-trial.log"),
        ("config.json", "00-trial-config.json"),
    ]
    for src_name, dest_name in mapping:
        src = trial_dir / src_name
        if src.is_file():
            _copy_file(src, dest_trial / dest_name)
            info["files"].append(dest_name)

    verifier = trial_dir / "verifier"
    if verifier.is_dir():
        reward = verifier / "reward.json"
        if reward.is_file():
            _copy_file(reward, dest_trial / "01-reward.json")
            info["files"].append("01-reward.json")
            payload = _load_json_lenient(reward)
            if payload and "reward" in payload:
                info["reward"] = payload["reward"]
        details = verifier / "reward-details.json"
        if details.is_file():
            _copy_file(details, dest_trial / "02-reward-details.json")
            info["files"].append("02-reward-details.json")
        for path in sorted(verifier.glob("reward-*.json")):
            name = path.name
            if name in {"reward.json", "reward-details.json"}:
                continue
            if name.endswith("-details.json"):
                skill = name[len("reward-") : -len("-details.json")]
                dest_name = f"03-reward-{skill}-details.json"
            else:
                skill = name[len("reward-") : -len(".json")]
                dest_name = f"03-reward-{skill}.json"
            _copy_file(path, dest_trial / dest_name)
            info["files"].append(dest_name)
        stdout = verifier / "test-stdout.txt"
        if stdout.is_file():
            _copy_file(stdout, dest_trial / "10-test-stdout.txt")
            info["files"].append("10-test-stdout.txt")

    code_dest = dest_trial / "code"
    artifacts = trial_dir / "artifacts"
    copied_code = 0
    if artifacts.is_dir():
        for path in sorted(artifacts.rglob("*.py")):
            if not path.is_file():
                continue
            rel = path.relative_to(artifacts)
            out_rel = _flatten_code_rel(rel)
            _copy_file(path, code_dest / out_rel)
            copied_code += 1
            info["files"].append(f"code/{out_rel.as_posix()}")
    info["code_files"] = copied_code

    if projects_root is not None:
        dest_projects = projects_root / trial_dir.name
        if archive_projects_layout(trial_dir, dest_projects):
            info["projects"] = dest_projects.as_posix()

    agent = trial_dir / "agent"
    agent_dest = dest_trial / "agent"
    if agent.is_dir():
        for path in sorted(agent.rglob("*")):
            if not path.is_file():
                continue
            # Skip bulky session trees; keep top-level agent logs + trajectory.
            rel = path.relative_to(agent)
            if "sessions" in rel.parts and rel.suffix not in {".json", ".txt", ".md"}:
                continue
            if len(rel.parts) > 2 and rel.parts[0] == "sessions":
                continue
            _copy_file(path, agent_dest / rel)
            info["files"].append(f"agent/{rel.as_posix()}")

    _write_json(dest_trial / "00-trial-index.json", info)
    return info


def archive_job(
    job_dir: Path,
    dest_job: Path,
    *,
    jobs_root: Path | None = None,
    projects_root: Path | None = None,
) -> dict:
    """Archive one Harbor job directory (e.g. codex-skills)."""
    dest_job.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {
        "job": job_dir.name,
        "source": str(job_dir),
        "trials": [],
    }

    result = job_dir / "result.json"
    if result.is_file():
        _copy_file(result, dest_job / "00-job-result.json")

    # Harbor config written beside the job output root.
    if jobs_root is not None:
        config = jobs_root / f"harbor.{job_dir.name}.yaml"
        if config.is_file():
            _copy_file(config, dest_job / "00-harbor-config.yaml")

    for trial_dir in sorted(job_dir.iterdir()):
        if not trial_dir.is_dir():
            continue
        if trial_dir.name in {"task-trees"}:
            continue
        if not (trial_dir / "verifier").is_dir() and not (trial_dir / "result.json").is_file():
            continue
        trial_info = archive_trial(
            trial_dir,
            dest_job / "trials" / trial_dir.name,
            projects_root=projects_root,
        )
        index["trials"].append(trial_info)

    _write_json(dest_job / "00-job-index.json", index)
    return index


def archive_jobs_root(
    jobs_root: Path,
    run_dir: Path,
    *,
    only_job: str | None = None,
) -> list[dict]:
    """Archive one or all Harbor jobs under *jobs_root* into *run_dir*/jobs/."""
    run_dir.mkdir(parents=True, exist_ok=True)
    archived: list[dict] = []
    for job_dir in sorted(jobs_root.iterdir()):
        if not job_dir.is_dir():
            continue
        if job_dir.name in SKIP_JOB_DIR_NAMES:
            continue
        if job_dir.name.startswith("generated-negative-"):
            continue
        if only_job is not None and job_dir.name != only_job:
            continue
        # Skip empty / non-job dirs (no result.json and no trial children).
        has_result = (job_dir / "result.json").is_file()
        has_trials = any(
            (child / "verifier").is_dir() or (child / "result.json").is_file()
            for child in job_dir.iterdir()
            if child.is_dir()
        )
        if not has_result and not has_trials:
            continue
        archived.append(
            archive_job(
                job_dir,
                run_dir / "jobs" / job_dir.name,
                jobs_root=jobs_root,
                projects_root=run_dir / "Projects",
            )
        )
    return archived


def write_meta(run_dir: Path, meta: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = dict(meta)
    meta.setdefault("archived_at", datetime.now(timezone.utc).isoformat())
    meta["run_dir"] = str(run_dir)
    _write_json(run_dir / "00-meta.json", meta)


def append_summary(run_dir: Path, text: str, *, name: str = "01-SUMMARY.txt") -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / name
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text)
        if not text.endswith("\n"):
            handle.write("\n")


def _git(cwd: Path, *args: str) -> None:
    """Run a git command with a local identity for archive fixtures."""
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "Eval Agent"
    env["GIT_AUTHOR_EMAIL"] = "eval@local"
    env["GIT_COMMITTER_NAME"] = "Eval Agent"
    env["GIT_COMMITTER_EMAIL"] = "eval@local"
    subprocess.run(
        [
            "git",
            "-C",
            str(cwd),
            "-c",
            "user.email=eval@local",
            "-c",
            "user.name=Eval Agent",
            *args,
        ],
        check=True,
        env=env,
        capture_output=True,
        text=True,
    )


def _self_test() -> int:
    """Build a fake Harbor trial and check the Projects/ archive layout.

    Returns:
        0 when the clone is reset to the empty initial commit and the
        worktree files are copied beside it.
    """
    cases: list[tuple[str, bool, str]] = []

    def record(name: str, ok: bool, detail: str) -> None:
        cases.append((name, ok, detail))

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
        (wt / "calculator.py").write_text("def run_calculator(c):\n    return c\n", encoding="utf-8")
        _git(wt, "add", "calculator.py")
        _git(wt, "commit", "-m", "feat(calculator): add calculator")
        _git(app, "merge", "--no-ff", "feat/calculator", "-m", "Merge feat/calculator")
        if not (app / "calculator.py").is_file():
            record("fixture_merged_clone", False, "expected calculator.py in clone after merge")
        else:
            record("fixture_merged_clone", True, "clone has merged file before archive")

        run_dir = root / "run"
        archive_jobs_root(root / "harbor", run_dir)
        dest_app = run_dir / "Projects" / trial.name / "app"
        dest_wt = run_dir / "Projects" / trial.name / ".worktrees" / "app" / "feat-calculator"
        dest_code = run_dir / "jobs" / "cc-skills" / "trials" / trial.name / "code" / "calculator.py"

        record(
            "projects_clone_exists",
            dest_app.is_dir(),
            str(dest_app),
        )
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
        record(
            "jobs_code_copy",
            dest_code.is_file(),
            str(dest_code),
        )

    failed = [(name, msg) for name, ok, msg in cases if not ok]
    for name, ok, msg in cases:
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {name}: {msg}", flush=True)
    if failed:
        print(f"{len(failed)}/{len(cases)} archive layout case(s) failed", flush=True)
        return 1
    print(f"{len(cases)}/{len(cases)} archive layout cases passed", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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

    args = parser.parse_args(argv)

    if args.cmd == "init":
        dirname = build_run_dirname(
            timestamp=args.timestamp,
            harnesses=args.harness,
            mode=args.mode,
            skills=args.skill,
            separately=args.separately,
            tasks=args.task or ["all"],
            attempts=args.attempts,
            concurrent=args.concurrent,
        )
        run_dir = args.runs_root / dirname
        meta = {
            "timestamp": args.timestamp,
            "harnesses": args.harness,
            "mode": args.mode,
            "skills": args.skill,
            "run_separately": bool(args.separately),
            "tasks": args.task or ["all"],
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
            (run_dir / "02-command.txt").write_text(args.command.rstrip() + "\n", encoding="utf-8")
        print(run_dir)
        return 0

    if args.cmd == "sync-job":
        archive_jobs_root(args.jobs_root, args.run_dir, only_job=args.job_name)
        if args.summary_file and args.summary_file.is_file():
            text = args.summary_file.read_text(encoding="utf-8")
            append_summary(args.run_dir, text)
            job_summary = args.run_dir / "jobs" / args.job_name / "01-SUMMARY.txt"
            job_summary.parent.mkdir(parents=True, exist_ok=True)
            job_summary.write_text(text, encoding="utf-8")
        print(args.run_dir)
        return 0

    if args.cmd == "finalize":
        archive_jobs_root(args.jobs_root, args.run_dir)
        if args.summary_file and args.summary_file.is_file():
            text = args.summary_file.read_text(encoding="utf-8")
            append_summary(args.run_dir, "\n" + text, name="01-SUMMARY.txt")
            (args.run_dir / "03-COMBINED-SUMMARY.txt").write_text(text, encoding="utf-8")
        # Refresh meta archived_at
        meta_path = args.run_dir / "00-meta.json"
        meta = _load_json_lenient(meta_path) or {}
        meta["archived_at"] = datetime.now(timezone.utc).isoformat()
        meta["jobs_dir"] = str(args.jobs_root)
        meta["jobs_temp"] = str(args.jobs_root)
        write_meta(args.run_dir, meta)
        print(args.run_dir)
        return 0

    if args.cmd == "self-test":
        return _self_test()

    return 1


if __name__ == "__main__":
    sys.exit(main())
