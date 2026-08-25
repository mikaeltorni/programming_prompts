"""Copy Harbor jobs and trials into inspectable archives."""

from __future__ import annotations

import fcntl
from datetime import datetime, timezone
from pathlib import Path

from .fsutil import copy_file, load_json_lenient, write_json
from .projects import archive_projects_layout

SKIP_JOB_DIR_NAMES = {"task-trees", "Projects", "harbor", "jobs"}


def _flatten_code_rel(rel: Path) -> Path:
    """Map an artifact path to its compact code path.

    Parameters: rel - path relative to the artifacts directory.

    Returns: destination path under ``code``.
    """
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


def _copy_named_trial_files(trial_dir: Path, dest_trial: Path, files: list[str]) -> None:
    """Copy fixed-name trial files.

    Parameters: trial_dir - Harbor trial directory; dest_trial - archive trial directory; files - mutable archived file list.

    Returns: nothing.
    """
    mapping = [
        ("result.json", "00-trial-result.json"),
        ("exception.txt", "20-exception.txt"),
        ("trial.log", "21-trial.log"),
        ("config.json", "00-trial-config.json"),
    ]
    for src_name, dest_name in mapping:
        src = trial_dir / src_name
        if src.is_file():
            copy_file(src, dest_trial / dest_name)
            files.append(dest_name)


def _copy_verifier(verifier: Path, dest_trial: Path, info: dict[str, object]) -> None:
    """Copy verifier rewards and test output.

    Parameters: verifier - Harbor verifier directory; dest_trial - archive trial directory; info - mutable trial index.

    Returns: nothing.
    """
    if not verifier.is_dir():
        return
    files = info["files"]
    assert isinstance(files, list)
    reward = verifier / "reward.json"
    if reward.is_file():
        copy_file(reward, dest_trial / "01-reward.json")
        files.append("01-reward.json")
        payload = load_json_lenient(reward)
        if payload and "reward" in payload:
            info["reward"] = payload["reward"]
    details = verifier / "reward-details.json"
    if details.is_file():
        copy_file(details, dest_trial / "02-reward-details.json")
        files.append("02-reward-details.json")
    for path in sorted(verifier.glob("reward-*.json")):
        if path.name in {"reward.json", "reward-details.json"}:
            continue
        if path.name.endswith("-details.json"):
            skill = path.name[len("reward-") : -len("-details.json")]
            dest_name = f"03-reward-{skill}-details.json"
        else:
            skill = path.name[len("reward-") : -len(".json")]
            dest_name = f"03-reward-{skill}.json"
        copy_file(path, dest_trial / dest_name)
        files.append(dest_name)
    stdout = verifier / "test-stdout.txt"
    if stdout.is_file():
        copy_file(stdout, dest_trial / "10-test-stdout.txt")
        files.append("10-test-stdout.txt")


def _copy_code(trial_dir: Path, dest_trial: Path, files: list[str]) -> int:
    """Copy Python artifacts into the trial code directory.

    Parameters: trial_dir - Harbor trial directory; dest_trial - archive trial directory; files - mutable archived file list.

    Returns: number of copied Python files.
    """
    artifacts = trial_dir / "artifacts"
    if not artifacts.is_dir():
        return 0
    count = 0
    for path in sorted(artifacts.rglob("*.py")):
        if not path.is_file():
            continue
        out_rel = _flatten_code_rel(path.relative_to(artifacts))
        copy_file(path, dest_trial / "code" / out_rel)
        count += 1
        files.append(f"code/{out_rel.as_posix()}")
    return count


def _copy_agent_logs(trial_dir: Path, dest_trial: Path, files: list[str]) -> None:
    """Copy compact agent logs while excluding bulky sessions.

    Parameters: trial_dir - Harbor trial directory; dest_trial - archive trial directory; files - mutable archived file list.

    Returns: nothing.
    """
    agent = trial_dir / "agent"
    if not agent.is_dir():
        return
    for path in sorted(agent.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(agent)
        if "sessions" in rel.parts and rel.suffix not in {".json", ".txt", ".md"}:
            continue
        if len(rel.parts) > 2 and rel.parts[0] == "sessions":
            continue
        copy_file(path, dest_trial / "agent" / rel)
        files.append(f"agent/{rel.as_posix()}")


def archive_trial(
    trial_dir: Path,
    dest_trial: Path,
    *,
    projects_root: Path | None = None,
) -> dict:
    """Copy one Harbor trial into a sorted folder.

    Parameters: trial_dir - Harbor trial directory; dest_trial - archive trial directory; projects_root - optional Projects archive root.

    Returns: trial index data.
    """
    dest_trial.mkdir(parents=True, exist_ok=True)
    info: dict[str, object] = {"trial": trial_dir.name, "files": []}
    files = info["files"]
    assert isinstance(files, list)
    _copy_named_trial_files(trial_dir, dest_trial, files)
    _copy_verifier(trial_dir / "verifier", dest_trial, info)
    info["code_files"] = _copy_code(trial_dir, dest_trial, files)
    if projects_root is not None:
        dest_projects = projects_root / trial_dir.name
        if archive_projects_layout(trial_dir, dest_projects):
            info["projects"] = dest_projects.as_posix()
    _copy_agent_logs(trial_dir, dest_trial, files)
    write_json(dest_trial / "00-trial-index.json", info)
    return info


def _is_trial_dir(path: Path) -> bool:
    """Check whether a directory contains Harbor trial output.

    Parameters: path - candidate directory.

    Returns: whether the directory is a trial.
    """
    return path.is_dir() and (
        (path / "verifier").is_dir() or (path / "result.json").is_file()
    )


def archive_job(
    job_dir: Path,
    dest_job: Path,
    *,
    jobs_root: Path | None = None,
    projects_root: Path | None = None,
) -> dict:
    """Archive one Harbor job directory.

    Parameters: job_dir - Harbor job directory; dest_job - archive job directory; jobs_root - source jobs root; projects_root - archive Projects root.

    Returns: job index data.
    """
    dest_job.mkdir(parents=True, exist_ok=True)
    index: dict[str, object] = {"job": job_dir.name, "source": str(job_dir), "trials": []}
    result = job_dir / "result.json"
    if result.is_file():
        copy_file(result, dest_job / "00-job-result.json")
    if jobs_root is not None:
        config = jobs_root / f"harbor.{job_dir.name}.yaml"
        if config.is_file():
            copy_file(config, dest_job / "00-harbor-config.yaml")
    trials = index["trials"]
    assert isinstance(trials, list)
    for trial_dir in sorted(job_dir.iterdir()):
        if trial_dir.name == "task-trees" or not _is_trial_dir(trial_dir):
            continue
        trials.append(
            archive_trial(
                trial_dir,
                dest_job / "trials" / trial_dir.name,
                projects_root=projects_root,
            )
        )
    write_json(dest_job / "00-job-index.json", index)
    return index


def _is_job_dir(path: Path) -> bool:
    """Check whether a directory contains Harbor job output.

    Parameters: path - candidate directory.

    Returns: whether the directory is a job.
    """
    return path.is_dir() and (
        (path / "result.json").is_file()
        or any(_is_trial_dir(child) for child in path.iterdir())
    )


def archive_jobs_root(
    jobs_root: Path,
    run_dir: Path,
    *,
    only_job: str | None = None,
) -> list[dict]:
    """Archive selected Harbor jobs into a run directory.

    Parameters: jobs_root - Harbor output root; run_dir - archive run directory; only_job - optional job-name filter.

    Returns: archived job indexes.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    archived: list[dict] = []
    for job_dir in sorted(jobs_root.iterdir()):
        if job_dir.name in SKIP_JOB_DIR_NAMES:
            continue
        if only_job is not None and job_dir.name != only_job:
            continue
        if not _is_job_dir(job_dir):
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
    """Write archive metadata with defaults.

    Parameters: run_dir - archive run directory; meta - metadata fields.

    Returns: nothing. Sets ``started_at`` when the payload omits it.
    Finalize overwrites ``archived_at``, ``elapsed_sec``, and ``runtime``.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = dict(meta)
    payload.setdefault("started_at", datetime.now(timezone.utc).isoformat())
    payload["run_dir"] = str(run_dir)
    write_json(run_dir / "00-meta.json", payload)


def append_summary(run_dir: Path, text: str, *, name: str = "01-SUMMARY.txt") -> None:
    """Append text to an archive summary.

    Parameters: run_dir - archive run directory; text - summary text; name - summary filename.

    Returns: nothing.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / name
    with path.open("a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            handle.write(text)
            if not text.endswith("\n"):
                handle.write("\n")
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
