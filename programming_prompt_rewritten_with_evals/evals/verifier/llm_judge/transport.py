"""Deliver Codex judge evidence without placing its contents in argv."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

PROMPT_FILE_PREFIX = "acc-judge-prompt-file:"


def install_codex_prompt_transport() -> None:
    """Adapt the pinned rewardkit backend within its isolated child process.

    Parameters: none.
    Returns: None.
    """
    from rewardkit.agents import CodexCLI

    directory = os.environ["ACC_JUDGE_PROMPT_DIR"]
    original = CodexCLI.build_command

    def build_command(self: Any, prompt: str, schema: dict[str, Any],
                      allowed_tools: tuple[str, ...] = ()) -> list[str]:
        """Store complete evidence and pass only its path to the Codex shim.

        Parameters: self - rewardkit backend; prompt - full judge input;
            schema - response schema; allowed_tools - permitted judge tools.
        Returns: the original command with a file reference as its prompt.
        """
        descriptor, filename = tempfile.mkstemp(dir=directory, suffix=".md")
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(prompt)
        return original(self, PROMPT_FILE_PREFIX + filename, schema, allowed_tools)

    CodexCLI.build_command = build_command


def codex_prompt_stdin(arguments: list[str]) -> list[str]:
    """Connect file-backed judge evidence to Codex stdin before exec.

    Parameters: arguments - CLI arguments excluding the executable.
    Returns: copied arguments with the file reference replaced by stdin '-'.
    """
    forwarded = list(arguments)
    if len(forwarded) < 2 or forwarded[0] != "exec":
        return forwarded
    if not forwarded[1].startswith(PROMPT_FILE_PREFIX):
        return forwarded
    path = Path(forwarded[1][len(PROMPT_FILE_PREFIX):])
    with path.open("rb") as handle:
        os.dup2(handle.fileno(), 0)
    forwarded[1] = "-"
    return forwarded
