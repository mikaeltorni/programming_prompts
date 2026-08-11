"""Clean Claude Code agent for rewritten-prompt Harbor benchmarks.

Wipes host/user Claude skill trees inside the trial, then installs only the
skills Harbor injected for the job. CLI version defaults to the pin in
``evals/claude-version.txt`` unless ``--ak version=...`` overrides it.
"""

from __future__ import annotations

from typing import override

from harbor.agents.installed.claude_code import ClaudeCode
from harbor.models.agent.name import AgentName

from harbor_agents.clean_skills import (
    build_clean_claude_skills_register_command,
    load_claude_version,
)


class BenchmarkClaudeCode(ClaudeCode):
    """Claude Code agent that pins a CLI version and keeps skills job-local."""

    def __init__(
        self,
        *args,
        version: str | None = None,
        **kwargs,
    ) -> None:
        """Create the agent, defaulting ``version`` to the evals pin file.

        Args:
            *args: Forwarded to Harbor's Claude Code agent.
            version: Claude Code CLI version to install/verify inside the trial
                environment. When omitted, reads ``evals/claude-version.txt``.
            **kwargs: Forwarded to the Harbor Claude Code agent (model flags,
                skills directory, reasoning effort, and so on).
        """
        pinned = version if version is not None else load_claude_version()
        super().__init__(*args, version=pinned, **kwargs)
        self.logger.info(
            "BenchmarkClaudeCode initialized version=%s skills_dir=%s",
            self._version,
            self.skills_dir,
        )

    @staticmethod
    @override
    def name() -> str:
        """Return Harbor's Claude Code agent name for job labels."""
        return AgentName.CLAUDE_CODE.value

    @override
    def _build_register_skills_command(self) -> str | None:
        """Always wipe Claude skill roots; install Harbor-injected skills when present."""
        command = build_clean_claude_skills_register_command(self.skills_dir)
        self.logger.info(
            "Resetting Claude skill discovery paths; installing skills_dir=%s",
            self.skills_dir,
        )
        return command
