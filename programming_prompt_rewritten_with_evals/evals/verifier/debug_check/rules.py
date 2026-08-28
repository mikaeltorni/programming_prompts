"""Apply the Harbor read-logs-first rules."""

from __future__ import annotations

import re
from pathlib import Path

from worktree_check.rules import CheckResult

REQUIRE_RE = re.compile(r"^(?:#\s*)?require:\s*(.+)$", re.IGNORECASE)


def _log_files(log_dir: Path) -> list[Path]:
    """List files under the repository log directory.

    Parameters: log_dir - repo `.log/` path.

    Returns: sorted files (not directories).
    """
    if not log_dir.is_dir():
        return []
    return sorted(path for path in log_dir.rglob("*") if path.is_file())


def required_tokens(log_dir: Path) -> list[str]:
    """Read `require:` tokens from planted log files.

    Parameters: log_dir - repo `.log/` path.

    Returns: non-empty token strings in file order.
    """
    tokens: list[str] = []
    for path in _log_files(log_dir):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in text.splitlines():
            match = REQUIRE_RE.match(line.strip())
            if match:
                token = match.group(1).strip()
                if token:
                    tokens.append(token)
    return tokens


def _workspace_python(repo: Path) -> str:
    """Concatenate workspace Python sources.

    Parameters: repo - project checkout.

    Returns: joined file contents for substring search.
    """
    chunks: list[str] = []
    for path in sorted(repo.rglob("*.py")):
        if any(part in {".git", "__pycache__", ".worktrees"} for part in path.parts):
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return "\n".join(chunks)


def check_repo(repo: Path) -> CheckResult:
    """Inspect whether workspace Python matches planted log diagnosis tokens.

    Parameters: repo - project checkout. Missing or empty `.log/` is a pass.

    Returns: pass/fail state and reasoning.
    """
    repo = repo.resolve()
    log_dir = repo / ".log"
    files = _log_files(log_dir)
    if not files:
        return CheckResult(True, f"no logs under {log_dir}; debug skill does not apply")
    tokens = required_tokens(log_dir)
    if not tokens:
        return CheckResult(
            False,
            f"logs exist under {log_dir} but have no require: tokens",
        )
    source = _workspace_python(repo)
    missing = [token for token in tokens if token not in source]
    if missing:
        return CheckResult(
            False,
            "workspace Python does not match the log diagnosis; "
            f"missing {missing!r}",
        )
    return CheckResult(
        True,
        f"workspace Python matches log diagnosis tokens {tokens!r}",
    )
