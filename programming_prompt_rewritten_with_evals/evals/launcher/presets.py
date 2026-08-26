"""Preset models, JSON persistence, matrix catalog, and listing helpers."""

from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .log import log

EVALS_DIR = Path(__file__).resolve().parent.parent
PRESETS_DIR = EVALS_DIR / "presets"
RUN_SCRIPT = "run_benchmark.sh"
DEFAULT_SKILLS = "srp,commenting,logging,worktree"
HARNESS_ORDER: tuple[str, ...] = ("codex", "cc", "grok")


@dataclass(frozen=True)
class Job:
    """One terminal to launch."""

    title: str
    args: tuple[str, ...]


@dataclass(frozen=True)
class Preset:
    """A named list of Harbor jobs."""

    name: str
    description: str
    jobs: tuple[Job, ...]
    path: Path | None = None


def slugify(name: str) -> str:
    """Turn a preset name into a filename stem.

    Parameters: name - human-readable preset title.

    Returns: a safe non-empty filename stem.
    """
    text = name.strip().lower()
    text = re.sub(r"[^a-z0-9._+-]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-._")
    return text or "preset"


def matrix_jobs(harnesses: Sequence[str], *, baseline: bool) -> tuple[Job, ...]:
    """Build one coding job per included harness.

    Parameters: harnesses - coders and judges for the slice; baseline - whether to pass ``--baseline``.

    Returns: matrix jobs sharing the included harnesses as judges.
    """
    if not harnesses:
        raise ValueError("need at least one harness")
    judges = ",".join(harnesses)
    jobs: list[Job] = []
    for harness in harnesses:
        args = [
            f"./{RUN_SCRIPT}",
            f"harness={harness}",
            f"evalAgent={judges}",
        ]
        if baseline:
            args.append("--baseline")
        args.extend(["--skills", DEFAULT_SKILLS, "-k", "5"])
        jobs.append(Job(title=f"{harness} x {judges}", args=tuple(args)))
    return tuple(jobs)


def matrix_preset_name(harnesses: Sequence[str], *, baseline: bool) -> str:
    """Build a matrix preset filename stem.

    Parameters: harnesses - included harness IDs; baseline - baseline or positive mode.

    Returns: the matrix preset stem.
    """
    mode = "baseline" if baseline else "positive"
    if tuple(harnesses) == HARNESS_ORDER:
        return f"{mode}-all-harnesses-all-judges"
    return f"{mode}-{'-'.join(harnesses)}"


def matrix_description(harnesses: Sequence[str], *, baseline: bool) -> str:
    """Build one-line matrix menu text.

    Parameters: harnesses - included harness IDs; baseline - baseline or positive mode.

    Returns: a matrix description including exclusions.
    """
    judges = ",".join(harnesses)
    mode = "baseline" if baseline else "positive"
    excluded = [item for item in HARNESS_ORDER if item not in harnesses]
    drop = f"; no {','.join(excluded)}" if excluded else ""
    return f"{mode}; judges={judges} on each coding run{drop}; k=5"


def shipped_matrix_groups() -> list[tuple[str, ...]]:
    """List the shipped three-way, two-way, and one-way groups.

    Parameters: none.

    Returns: harness groups in shipped catalog order.
    """
    groups: list[tuple[str, ...]] = [HARNESS_ORDER]
    for excluded in reversed(HARNESS_ORDER):
        groups.append(tuple(harness for harness in HARNESS_ORDER if harness != excluded))
    groups.extend((only,) for only in HARNESS_ORDER)
    return groups


def shipped_presets() -> list[Preset]:
    """Build the shipped positive and baseline matrix catalog.

    Parameters: none.

    Returns: built-in presets in menu order.
    """
    return [
        Preset(
            name=matrix_preset_name(harnesses, baseline=baseline),
            description=matrix_description(harnesses, baseline=baseline),
            jobs=matrix_jobs(harnesses, baseline=baseline),
        )
        for harnesses in shipped_matrix_groups()
        for baseline in (False, True)
    ]


def parse_job(raw: dict[str, Any], *, index: int) -> Job:
    """Build a job from one preset JSON object.

    Parameters: raw - job object; index - one-based index for errors.

    Returns: a validated job.
    """
    title = str(raw.get("title") or f"job-{index}").strip()
    args_raw = raw.get("args")
    if not isinstance(args_raw, list) or not args_raw:
        raise ValueError(f"job {index} needs a non-empty args array")
    args = tuple(str(item) for item in args_raw)
    if Path(args[0]).name != RUN_SCRIPT:
        raise ValueError(f"job {index} must run {RUN_SCRIPT}, got {args[0]!r}")
    if not title:
        raise ValueError(f"job {index} has an empty title")
    return Job(title=title, args=args)


def parse_preset(payload: dict[str, Any], *, path: Path | None = None) -> Preset:
    """Build a preset from a JSON root object.

    Parameters: payload - root object; path - source file when loaded from disk.

    Returns: a validated preset.
    """
    name = str(payload.get("name") or (path.stem if path else "preset")).strip()
    description = str(payload.get("description") or "").strip()
    jobs_raw = payload.get("jobs")
    if not isinstance(jobs_raw, list) or not jobs_raw:
        raise ValueError("preset needs a non-empty jobs array")
    jobs = tuple(parse_job(item, index=i) for i, item in enumerate(jobs_raw, start=1))
    titles = [job.title for job in jobs]
    if len(titles) != len(set(titles)):
        raise ValueError("preset job titles must be unique (window names)")
    return Preset(name=slugify(name), description=description, jobs=jobs, path=path)


def preset_to_json(preset: Preset) -> dict[str, Any]:
    """Serialize a preset for disk.

    Parameters: preset - in-memory preset.

    Returns: a JSON-compatible root object.
    """
    return {
        "name": preset.name,
        "description": preset.description,
        "jobs": [{"title": job.title, "args": list(job.args)} for job in preset.jobs],
    }


def load_preset_file(path: Path) -> Preset:
    """Read and validate one preset JSON file.

    Parameters: path - preset JSON path.

    Returns: the validated preset.
    """
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must be a JSON object")
    return parse_preset(payload, path=path)


def list_preset_files(directory: Path = PRESETS_DIR) -> list[Path]:
    """List preset JSON paths in menu order.

    Parameters: directory - presets folder.

    Returns: shipped catalog files first, then extra stems.
    """
    if not directory.is_dir():
        return []
    order = {preset.name: index for index, preset in enumerate(shipped_presets())}

    def sort_key(path: Path) -> tuple[int, int | str]:
        """Build one preset path's ordering key.

        Parameters: path - preset JSON path.

        Returns: shipped-order or extra-name key.
        """
        stem = path.stem
        return (0, order[stem]) if stem in order else (1, stem)

    return sorted(directory.glob("*.json"), key=sort_key)


def resolve_preset(name: str, directory: Path = PRESETS_DIR) -> Path:
    """Resolve a preset stem, filename, or path.

    Parameters: name - preset identifier; directory - presets folder.

    Returns: an existing preset path.
    """
    candidate = Path(name)
    if candidate.is_file():
        return candidate
    direct = directory / name
    if direct.is_file():
        return direct
    if not name.endswith(".json"):
        with_ext = directory / f"{name}.json"
        if with_ext.is_file():
            return with_ext
    raise FileNotFoundError(f"preset not found: {name} (looked in {directory})")


def save_preset(preset: Preset, directory: Path = PRESETS_DIR) -> Path:
    """Write a preset as JSON.

    Parameters: preset - preset to store; directory - presets folder.

    Returns: the written path.
    """
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{preset.name}.json"
    path.write_text(json.dumps(preset_to_json(preset), indent=2) + "\n", encoding="utf-8")
    log(f"saved preset {path}")
    return path


def write_shipped_presets(directory: Path = PRESETS_DIR) -> list[Path]:
    """Rewrite shipped matrix JSON files.

    Parameters: directory - presets folder.

    Returns: paths written.
    """
    written = [save_preset(preset, directory) for preset in shipped_presets()]
    log(f"wrote {len(written)} shipped preset(s) under {directory}")
    return written


def jobs_from_command_lines(lines: Sequence[str]) -> tuple[Job, ...]:
    """Parse pasted benchmark commands into jobs.

    Parameters: lines - one command per line with blanks and comments ignored.

    Returns: jobs with unique window titles.
    """
    jobs: list[Job] = []
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        args = tuple(shlex.split(stripped))
        if (Path(args[0]).name if args else "") != RUN_SCRIPT:
            raise ValueError(f"line {index} must start with {RUN_SCRIPT}")
        jobs.append(
            Job(
                title=_title_from_args(args, fallback=f"job-{len(jobs) + 1}"),
                args=args,
            )
        )
    if not jobs:
        raise ValueError("no commands to save")
    seen: dict[str, int] = {}
    unique: list[Job] = []
    for job in jobs:
        count = seen.get(job.title, 0) + 1
        seen[job.title] = count
        title = job.title if count == 1 else f"{job.title} {count}"
        unique.append(Job(title=title, args=job.args))
    return tuple(unique)


def _title_from_args(args: Sequence[str], *, fallback: str) -> str:
    """Derive a window title from command arguments.

    Parameters: args - benchmark argv; fallback - title without harness metadata.

    Returns: the derived or fallback title.
    """
    harness = "harness"
    agent = "inherit"
    for item in args:
        if item.startswith("harness="):
            harness = item.split("=", 1)[1] or harness
        if item.startswith(("evalAgent=", "eval-agent=")):
            agent = item.split("=", 1)[1] or agent
    if harness == "harness" and agent == "inherit":
        return fallback
    return f"{harness} x {agent}"


def _job_eval_agents(job: Job) -> set[str]:
    """Read evaluator IDs from a job.

    Parameters: job - one launcher job.

    Returns: evaluator IDs from the comma list.
    """
    for item in job.args:
        if item.startswith(("evalAgent=", "eval-agent=")):
            return {token for token in item.split("=", 1)[1].split(",") if token}
    return set()


def _job_harness(job: Job) -> str:
    """Read the coding harness from a job.

    Parameters: job - one launcher job.

    Returns: the harness ID or an empty string.
    """
    for item in job.args:
        if item.startswith("harness="):
            return item.split("=", 1)[1]
    return ""


def _eval_agent_csv(job: Job) -> str:
    """Order evaluator IDs for display.

    Parameters: job - one launcher job.

    Returns: evaluator IDs in harness order followed by extras.
    """
    agents = _job_eval_agents(job)
    ordered = [item for item in HARNESS_ORDER if item in agents]
    ordered.extend(sorted(agents - set(HARNESS_ORDER)))
    return ",".join(ordered)


def format_preset_listing(preset: Preset) -> str:
    """Format a preset summary for menus and lists.

    Parameters: preset - preset to summarize.

    Returns: coding count, shared judges, and description.
    """
    count = len(preset.jobs)
    coding = "1 coding" if count == 1 else f"{count} coding"
    judges = _eval_agent_csv(preset.jobs[0]) if preset.jobs else "-"
    return f"[{coding} × judges={judges}]  {preset.description}"
