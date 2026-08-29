#!/usr/bin/env python3
"""Run one unified Harbor LLM judge."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from llm_judge.grok import DEFAULT_MAX_TURNS, score_with_grok
from llm_judge.log import log
from llm_judge.ratelimit import JUDGE_CLI_FAILURES
from llm_judge.rewardkit import score_with_rewardkit
from llm_judge.scores import write_reward
from llm_judge.self_test import run_self_test
from llm_judge.workspace import DEFAULT_WORKSPACE, list_workspace_python, load_judge_dir


def run_eval_agent(
    *,
    agent: str,
    judge_dir: Path,
    output: Path,
    workspace: Path,
    model: str,
    effort: str,
    timeout: int,
    max_turns: int = DEFAULT_MAX_TURNS,
) -> None:
    """Score one skill with one eval agent and write reward JSON.

    Parameters: agent - grok, cc, or codex; judge_dir - prompt and config directory; output - reward path; workspace - solution checkout; model - backend model; effort - reasoning effort; timeout - wall budget or zero for config; max_turns - Grok tool rounds.

    Returns: None.
    """
    template, criteria, toml_timeout = load_judge_dir(judge_dir)
    budget = timeout or toml_timeout
    files = list_workspace_python(workspace)
    try:
        if agent == "grok":
            raw, rows = score_with_grok(
                template=template,
                criteria=criteria,
                workspace=workspace,
                files=files,
                model=model,
                effort=effort,
                timeout=budget,
                max_turns=max_turns,
            )
        elif agent in {"cc", "codex"}:
            raw, rows = score_with_rewardkit(
                agent=agent,
                judge_dir=judge_dir,
                workspace=workspace,
                files=files,
                model=model,
                effort=effort,
                timeout=budget,
                criteria=criteria,
            )
        else:
            raise ValueError(
                f"unknown eval agent {agent!r} (expected grok, cc, or codex)"
            )
    except JUDGE_CLI_FAILURES as exc:
        err = ""
        if isinstance(exc, subprocess.CalledProcessError):
            err = str(exc.stderr or exc.output or exc)
        else:
            err = str(exc)
        # A crashed or timed-out judge CLI did not score the trial. Treat
        # that as a rate-limit skip, including Codex uvx/rewardkit exit 1
        # and subprocess.TimeoutExpired (not a TimeoutError) from uvx warmup.
        log(
            f"evalAgent {agent} judge CLI failed; recording ratelimit skip "
            f"not a scored no ({type(exc).__name__})"
        )
        write_reward(
            output,
            [],
            err or str(exc),
            agent=agent,
            ratelimit=True,
        )
        return
    write_reward(output, rows, raw, agent=agent)


def main(argv: list[str] | None = None) -> int:
    """Parse options and run a self-test or one eval agent.

    Parameters: argv - optional argument override.

    Returns: process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--agent", choices=("grok", "cc", "codex"), default="grok")
    parser.add_argument("--judge-dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--workspace", type=Path, default=DEFAULT_WORKSPACE)
    parser.add_argument("--model", default="")
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--timeout", type=int, default=0)
    parser.add_argument(
        "--max-turns",
        type=int,
        default=DEFAULT_MAX_TURNS,
        help="Grok agent rounds for reading files before structured output",
    )
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    if args.judge_dir is None or args.output is None:
        parser.error("--judge-dir and --output are required unless --self-test")
    defaults = {
        "grok": "grok-4.6",
        "cc": "claude-opus-5",
        "codex": "gpt-5.6-luna",
    }
    run_eval_agent(
        agent=args.agent,
        judge_dir=args.judge_dir,
        output=args.output,
        workspace=args.workspace,
        model=args.model or defaults[args.agent],
        effort=args.reasoning_effort,
        timeout=args.timeout,
        max_turns=args.max_turns,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
