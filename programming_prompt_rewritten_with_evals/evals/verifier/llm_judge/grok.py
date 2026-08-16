"""Grok CLI backend for the shared LLM judge."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from llm_judge.log import log
from llm_judge.reliability import retry_prompt, run_until_reliable
from llm_judge.scores import parse_scores, response_schema
from llm_judge.workspace import inspect_prompt, listed_python_keys

DEFAULT_MAX_TURNS = 16


def build_grok_command(
    *,
    prompt: str,
    schema: dict[str, Any],
    workspace: Path,
    model: str,
    effort: str,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> list[str]:
    """Return the Grok CLI argv for a headless judge call.

    Args:
        prompt: Full judge prompt (criteria already substituted).
        schema: JSON Schema for ``--json-schema``.
        workspace: Working directory the CLI may inspect.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        max_turns: Agent tool/model rounds before the CLI must stop.

    Returns:
        Argument list for ``subprocess.run`` (first item is ``grok``).
    """
    return [
        "grok",
        "--single",
        prompt,
        "--json-schema",
        json.dumps(schema),
        "--model",
        model,
        "--reasoning-effort",
        effort,
        "--cwd",
        str(workspace),
        "--max-turns",
        str(max_turns),
        "--always-approve",
        "--permission-mode",
        "bypassPermissions",
        "--disable-web-search",
    ]


def run_grok(
    *,
    prompt: str,
    schema: dict[str, Any],
    workspace: Path,
    model: str,
    effort: str,
    timeout: int,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> str:
    """Invoke the Grok CLI as a headless structured-output judge.

    Args:
        prompt: Full judge prompt (criteria already substituted).
        schema: JSON Schema for ``--json-schema``.
        workspace: Working directory the CLI may inspect.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Subprocess timeout in seconds.
        max_turns: Agent rounds; see :func:`build_grok_command`.

    Returns:
        Decoded stdout.

    Raises:
        FileNotFoundError: When ``grok`` is not on PATH.
        subprocess.CalledProcessError: When the CLI exits non-zero.
        subprocess.TimeoutExpired: When the CLI exceeds *timeout*.
    """
    cmd = build_grok_command(
        prompt=prompt,
        schema=schema,
        workspace=workspace,
        model=model,
        effort=effort,
        max_turns=max_turns,
    )
    log(
        f"starting grok judge model={model} effort={effort} "
        f"max_turns={max_turns} workspace={workspace} timeout={timeout}s"
    )
    proc = subprocess.run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "")[:500]
        log(f"grok judge failed rc={proc.returncode}: {err}")
        raise subprocess.CalledProcessError(
            proc.returncode, cmd, output=proc.stdout, stderr=proc.stderr
        )
    return proc.stdout or ""


def score_with_grok(
    *,
    template: str,
    criteria: list[dict[str, str]],
    workspace: Path,
    files: list[Path],
    model: str,
    effort: str,
    timeout: int,
    max_turns: int = DEFAULT_MAX_TURNS,
    invoke: Any | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Pin workspace Python, run Grok, and retry once if the score is unusable.

    Args:
        template: Judge prompt with ``{criteria}``.
        criteria: Name/description pairs from ``judge.toml``.
        workspace: Coding-agent workspace.
        files: Paths from ``list_workspace_python``.
        model: Grok model id.
        effort: ``low``, ``medium``, or ``high``.
        timeout: Wall budget in seconds for both attempts.
        max_turns: Agent rounds per attempt.
        invoke: Optional runner for ``--self-test`` (same kwargs as
            :func:`run_grok`).

    Returns:
        Raw stdout and parsed rows from the last attempt used.
    """
    prompt = inspect_prompt(template, criteria, workspace, python_files=files)
    schema = response_schema(criteria)
    runner = invoke or run_grok

    def attempt(reason: str | None, timeout_s: int) -> tuple[str, list[dict[str, Any]]]:
        text = prompt if reason is None else retry_prompt(prompt, reason)
        raw = runner(
            prompt=text,
            schema=schema,
            workspace=workspace,
            model=model,
            effort=effort,
            timeout=timeout_s,
            max_turns=max_turns,
        )
        return raw, parse_scores(raw, criteria)

    return run_until_reliable(
        listed_keys=listed_python_keys(files, workspace),
        timeout=timeout,
        attempt=attempt,
    )
