"""Codex / Claude Code judges via pinned harbor-rewardkit 0.1.7.

Rewardkit still owns the CLI call. This module copies the skill prompt,
appends the real workspace ``*.py`` listing, then retries once when the
score admits non-inspection or cites a path that is not in the workspace.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.homes import (
    claude_effort_on_path,
    claude_judge_env,
    overlay_environ,
    setup_claude_home,
    setup_codex_home,
)
from llm_judge.log import log
from llm_judge.reliability import retry_prompt, run_until_reliable
from llm_judge.scores import rows_from_rewardkit_details
from llm_judge.workspace import (
    listed_python_keys,
    load_judge_dir,
    pin_workspace_python,
)

REWARDKIT_FROM = "harbor-rewardkit@0.1.7"
UVX_WARMUP_TIMEOUT_S = 180
_UVX_LOCK = Path("/tmp/harbor-rewardkit-uvx.lock")
_UVX_READY = Path("/tmp/harbor-rewardkit-ready-0.1.7")


def rewardkit_command() -> list[str]:
    """Return the argv prefix for the rewardkit CLI.

    Parameters: none.

    Returns: ``[path-to-rewardkit]`` when the task image preinstalled the
        binary, otherwise pinned ``uvx --from harbor-rewardkit@0.1.7``.
    """
    binary = shutil.which("rewardkit")
    if binary:
        return [binary]
    return ["uvx", "--from", REWARDKIT_FROM, "rewardkit"]


def _rewardkit_error_excerpt(text: str) -> str:
    """Keep the useful tail of rewardkit stderr.

    Parameters: text - combined stderr/stdout from a failed ``uvx`` run.

    Returns: excerpt without leading download-progress lines.
    """
    lines = [
        line
        for line in text.splitlines()
        if not line.strip().startswith("Downloading ")
        and " Downloaded " not in line
        and not line.startswith("Installed ")
    ]
    excerpt = "\n".join(lines).strip() or text.strip()
    return excerpt[-3000:]


def ensure_rewardkit_cli(env: dict[str, str] | None = None) -> None:
    """Install harbor-rewardkit once so parallel judges do not race ``uvx``.

    Skips warmup when ``rewardkit`` is already on PATH (task image
    ``uv tool install``). 100 concurrent ``uvx --from`` warmups otherwise
    stall the disk and hit :data:`UVX_WARMUP_TIMEOUT_S`.

    Parameters: env - optional environment for the warmup process.

    Returns: none.
    """
    if shutil.which("rewardkit"):
        log("preinstalled rewardkit on PATH; skip uvx warmup")
        return
    if _UVX_READY.is_file():
        return
    _UVX_LOCK.parent.mkdir(parents=True, exist_ok=True)
    with _UVX_LOCK.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        if shutil.which("rewardkit") or _UVX_READY.is_file():
            return
        log(f"warming uvx {REWARDKIT_FROM} (serial; parallel judges wait)")
        merged = os.environ.copy()
        if env:
            merged.update(env)
        proc = subprocess.run(
            ["uvx", "--from", REWARDKIT_FROM, "rewardkit", "--help"],
            check=False,
            capture_output=True,
            text=True,
            timeout=UVX_WARMUP_TIMEOUT_S,
            env=merged,
        )
        if proc.returncode != 0:
            err = _rewardkit_error_excerpt(proc.stderr or proc.stdout or "")
            log(f"rewardkit warmup failed rc={proc.returncode}: {err}")
            raise subprocess.CalledProcessError(
                proc.returncode,
                ["uvx", "--from", REWARDKIT_FROM, "rewardkit", "--help"],
                output=proc.stdout,
                stderr=proc.stderr,
            )
        _UVX_READY.write_text("ok\n", encoding="utf-8")
        log("rewardkit uvx tool is ready")


def rewardkit_backend(agent: str) -> str:
    """Return the rewardkit ``--judge`` name for an eval-agent id.

    Args:
        agent: ``cc``, ``codex``, or another id.

    Returns:
        ``claude-code`` or ``codex``.
    """
    if agent == "cc":
        return "claude-code"
    return "codex"


def write_pinned_judge_dir(
    judge_dir: Path,
    workspace: Path,
    files: list[Path],
    retry_reason: str | None = None,
) -> Path:
    """Copy a skill judge dir and append the workspace Python listing.

    Leaves ``{criteria}`` in ``prompt.md`` so rewardkit can substitute it.

    Args:
        judge_dir: Canonical ``evals/judges/<skill>`` (or the Harbor copy).
        workspace: Coding-agent workspace.
        files: Paths from :func:`list_workspace_python`.
        retry_reason: Optional token from ``unreliable_score_reason``.

    Returns:
        Temporary directory with ``prompt.md`` and ``judge.toml``.
    """
    template, _, _ = load_judge_dir(judge_dir)
    pinned = pin_workspace_python(template, workspace, files)
    if retry_reason:
        pinned = retry_prompt(pinned, retry_reason)
    work = Path(tempfile.mkdtemp(prefix="llm-judge-rk-"))
    (work / "prompt.md").write_text(pinned + "\n", encoding="utf-8")
    shutil.copy(judge_dir / "judge.toml", work / "judge.toml")
    log(
        f"pinned rewardkit prompt files={len(files)} "
        f"retry={'yes' if retry_reason else 'no'} dir={work}"
    )
    return work


def load_rewardkit_details(output: Path) -> dict[str, Any]:
    """Read rewardkit's sibling ``reward-details.json`` next to *output*.

    Args:
        output: Path passed as ``rewardkit --output``.

    Returns:
        Parsed details object, or ``{}`` when missing/invalid.
    """
    details_path = output.with_name("reward-details.json")
    if not details_path.is_file():
        log(f"rewardkit details missing: {details_path}")
        return {}
    try:
        payload = json.loads(details_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log(f"rewardkit details unreadable: {exc}")
        return {}
    return payload if isinstance(payload, dict) else {}


def run_rewardkit(
    *,
    work: Path,
    output: Path,
    backend: str,
    model: str,
    workspace: Path,
    timeout: int,
    env: dict[str, str] | None = None,
) -> None:
    """Shell out to preinstalled ``rewardkit`` or pinned ``uvx``.

    Args:
        work: Temp judge directory with pinned ``prompt.md``.
        output: Reward JSON path (details written beside it).
        backend: ``codex`` or ``claude-code``.
        model: Model id for ``--model``.
        workspace: Coding-agent workspace.
        timeout: Subprocess timeout in seconds.
        env: Optional environment overlay (homes, tokens). Values are not logged.

    Raises:
        FileNotFoundError: When neither ``rewardkit`` nor ``uvx`` is on PATH.
        subprocess.CalledProcessError: When rewardkit exits non-zero.
        subprocess.TimeoutExpired: When the CLI exceeds *timeout*.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    ensure_rewardkit_cli(env)
    cmd = [
        *rewardkit_command(),
        str(work),
        "--workspace",
        str(workspace),
        "--output",
        str(output),
        "--judge",
        backend,
        "--model",
        model,
    ]
    merged = os.environ.copy()
    if env:
        merged.update(env)
        log(f"rewardkit env overlay keys={','.join(sorted(env))}")
    log(
        f"starting rewardkit judge argv0={cmd[0]} backend={backend} model={model} "
        f"workspace={workspace} timeout={timeout}s"
    )
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=merged,
    )
    if proc.returncode != 0:
        err = _rewardkit_error_excerpt(proc.stderr or proc.stdout or "")
        log(f"rewardkit judge failed rc={proc.returncode}: {err}")
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )


def score_with_rewardkit(
    *,
    agent: str,
    judge_dir: Path,
    workspace: Path,
    files: list[Path],
    model: str,
    effort: str,
    timeout: int,
    criteria: list[dict[str, str]],
    invoke: Callable[..., None] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Pin workspace Python, run rewardkit, and retry once if unusable.

    Args:
        agent: ``cc`` or ``codex``.
        judge_dir: Skill judge directory with ``prompt.md`` / ``judge.toml``.
        workspace: Coding-agent workspace.
        files: Paths from :func:`list_workspace_python`.
        model: Model id.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Wall budget in seconds for both attempts.
        criteria: Name/description pairs from ``judge.toml``.
        invoke: Optional ``run_rewardkit`` replacement for ``--self-test``.

    Returns:
        Details JSON text and parsed rows from the last attempt used.
    """
    backend = rewardkit_backend(agent)
    runner = invoke or run_rewardkit
    listed_keys = listed_python_keys(files, workspace)
    overlay: dict[str, str] = {}

    def attempt(reason: str | None, timeout_s: int) -> tuple[str, list[dict[str, Any]]]:
        work = write_pinned_judge_dir(judge_dir, workspace, files, reason)
        tmp_out = work / "reward.json"
        try:
            runner(
                work=work,
                output=tmp_out,
                backend=backend,
                model=model,
                workspace=workspace,
                timeout=timeout_s,
                env=overlay or None,
            )
            details = load_rewardkit_details(tmp_out)
            rows = rows_from_rewardkit_details(details, criteria)
            raw = json.dumps(details)[:8000]
            return raw, rows
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def with_homes() -> tuple[str, list[dict[str, Any]]]:
        if agent == "cc":
            home, token = setup_claude_home()
            overlay.update(claude_judge_env(home, token))
            try:
                with overlay_environ(overlay), claude_effort_on_path(effort):
                    return run_until_reliable(
                        listed_keys=listed_keys, timeout=timeout, attempt=attempt
                    )
            finally:
                shutil.rmtree(home, ignore_errors=True)
        home = setup_codex_home(effort)
        overlay["CODEX_HOME"] = str(home)
        try:
            with overlay_environ(overlay):
                return run_until_reliable(
                    listed_keys=listed_keys, timeout=timeout, attempt=attempt
                )
        finally:
            shutil.rmtree(home, ignore_errors=True)

    if invoke is not None:
        return run_until_reliable(
            listed_keys=listed_keys, timeout=timeout, attempt=attempt
        )
    return with_homes()
