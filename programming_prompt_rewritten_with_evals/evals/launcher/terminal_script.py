"""Terminal titles and inner-shell script construction."""

from __future__ import annotations

import shlex
from typing import Sequence

WINDOW_TITLE_PREFIX = "harbor-eval:"


def window_title(job_title: str) -> str:
    """Build a unique window-manager title.

    Parameters: job_title - preset job title.

    Returns: a title suitable for xdotool search.
    """
    return f"{WINDOW_TITLE_PREFIX} {job_title}"


def shell_command(args: Sequence[str]) -> str:
    """Quote argv for a shell command.

    Parameters: args - command arguments.

    Returns: a shell-safe command string.
    """
    return " ".join(shlex.quote(part) for part in args)


def terminal_script(title: str, args: Sequence[str]) -> str:
    """Build the inner shell that runs one Harbor job.

    Parameters: title - window title; args - benchmark argv from evals.

    Returns: a bash script that runs the job and stays interactive.
    """
    quoted_title = shlex.quote(title)
    body = shell_command(args)
    quoted_body = shlex.quote(body)
    return (
        f"printf '\\033]0;%s\\007' {quoted_title}; "
        f"echo {quoted_title}; echo; "
        "hist=$(mktemp --tmpdir harbor-eval-hist.XXXXXX); "
        "rc=$(mktemp --tmpdir harbor-eval-rc.XXXXXX); "
        f"printf '%s\\n' {quoted_body} > \"$hist\"; "
        "printf 'export HISTFILE=%s\\nexport HISTSIZE=1000\\nexport HISTFILESIZE=1000\\n' "
        "\"$hist\" > \"$rc\"; "
        "echo '[[ -f ~/.bashrc ]] && . ~/.bashrc' >> \"$rc\"; "
        f"{body}; "
        "status=$?; echo; echo exit=$status; "
        "exec bash --rcfile \"$rc\" -i"
    )
