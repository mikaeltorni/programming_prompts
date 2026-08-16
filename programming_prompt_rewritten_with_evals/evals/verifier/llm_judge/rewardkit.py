"""Codex / Claude Code judges via pinned harbor-rewardkit 0.1.7.

Rewardkit still owns the CLI call. This module copies the skill prompt,
appends the real workspace ``*.py`` listing, then retries once when the
score admits non-inspection or cites a path that is not in the workspace.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.homes import claude_effort_on_path, setup_claude_home, setup_codex_home
from llm_judge.log import log
from llm_judge.reliability import retry_prompt, run_until_reliable
from llm_judge.scores import rows_from_rewardkit_details
from llm_judge.workspace import (
    listed_python_keys,
    load_judge_dir,
    pin_workspace_python,
)

REWARDKIT_FROM = "harbor-rewardkit@0.1.7"


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
    """Shell out to pinned ``uvx harbor-rewardkit``.

    Args:
        work: Temp judge directory with pinned ``prompt.md``.
        output: Reward JSON path (details written beside it).
        backend: ``codex`` or ``claude-code``.
        model: Model id for ``--model``.
        workspace: Coding-agent workspace.
        timeout: Subprocess timeout in seconds.
        env: Optional environment overlay (homes, tokens). Values are not logged.

    Raises:
        FileNotFoundError: When ``uvx`` is missing.
        subprocess.CalledProcessError: When rewardkit exits non-zero.
        subprocess.TimeoutExpired: When the CLI exceeds *timeout*.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "uvx",
        "--from",
        REWARDKIT_FROM,
        "rewardkit",
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
    log(
        f"starting rewardkit judge backend={backend} model={model} "
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
        err = (proc.stderr or proc.stdout or "")[:500]
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
            env = {
                "CLAUDE_FORCE_OAUTH": "true",
                "REWARDKIT_FORCE_OAUTH": "true",
                "CLAUDE_CONFIG_DIR": str(home),
                "IS_SANDBOX": "1",
                "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
            }
            if token:
                env["CLAUDE_CODE_OAUTH_TOKEN"] = token
            try:
                with claude_effort_on_path(effort):
                    return run_until_reliable(
                        listed_keys=listed_keys, timeout=timeout, attempt=attempt
                    )
            finally:
                shutil.rmtree(home, ignore_errors=True)
        home = setup_codex_home(effort)
        try:
            old = os.environ.get("CODEX_HOME")
            os.environ["CODEX_HOME"] = str(home)
            try:
                return run_until_reliable(
                    listed_keys=listed_keys, timeout=timeout, attempt=attempt
                )
            finally:
                if old is None:
                    os.environ.pop("CODEX_HOME", None)
                else:
                    os.environ["CODEX_HOME"] = old
        finally:
            shutil.rmtree(home, ignore_errors=True)

    if invoke is not None:
        return run_until_reliable(
            listed_keys=listed_keys, timeout=timeout, attempt=attempt
        )
    return with_homes()
