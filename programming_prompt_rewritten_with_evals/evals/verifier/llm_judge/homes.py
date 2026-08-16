"""Writable Codex / Claude Code homes for Harbor judge calls.

The trial bind-mounts host credentials read-only. The CLIs also write
sessions and may refresh those files, so each judge run gets a temp copy.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from llm_judge.log import log


def _copy_auth(source: Path, dest: Path) -> None:
    """Copy an auth file with mode 0600. Does not log contents."""
    dest.write_bytes(source.read_bytes())
    dest.chmod(stat.S_IRUSR | stat.S_IWUSR)


def find_codex_auth() -> Path | None:
    """Return the first readable Codex ``auth.json``, if any."""
    home = os.environ.get("CODEX_HOME", "").strip()
    candidates = []
    if home:
        candidates.append(Path(home) / "auth.json")
    candidates.extend(
        [
            Path("/tmp/codex-home/auth.json"),
            Path.home() / ".codex" / "auth.json",
        ]
    )
    for path in candidates:
        if path and path.is_file():
            return path
    return None


def setup_codex_home(effort: str) -> Path:
    """Create a writable ``CODEX_HOME`` with reasoning effort and a copied auth.

    Args:
        effort: ``low``, ``medium``, or ``high``.

    Returns:
        Temporary directory to export as ``CODEX_HOME``.
    """
    judge_home = Path(tempfile.mkdtemp(prefix="codex-judge-"))
    auth = find_codex_auth()
    if auth is not None:
        _copy_auth(auth, judge_home / "auth.json")
        log("codex eval agent: copied auth.json into writable CODEX_HOME")
    (judge_home / "config.toml").write_text(
        f'model_reasoning_effort = "{effort}"\n'
        'sandbox_mode = "danger-full-access"\n',
        encoding="utf-8",
    )
    return judge_home


def _oauth_from_credentials(path: Path) -> str:
    """Return the Claude access token from a credentials JSON file."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    oauth = data.get("claudeAiOauth") if isinstance(data, dict) else None
    token = oauth.get("accessToken") if isinstance(oauth, dict) else None
    if isinstance(token, str) and token.strip():
        return token.strip()
    return ""


def find_claude_credentials() -> Path | None:
    """Return the first readable Claude credentials file, if any."""
    for path in (
        Path.home() / ".claude" / ".credentials.json",
        Path("/root/.claude/.credentials.json"),
    ):
        if path.is_file():
            return path
    return None


def setup_claude_home() -> tuple[Path, str]:
    """Create a writable ``CLAUDE_CONFIG_DIR`` and resolve the OAuth token.

    Args:
        None.

    Returns:
        Temp config dir and token string (empty when unset).

    Raises:
        FileNotFoundError: When neither a token nor credentials exist.
    """
    judge_home = Path(tempfile.mkdtemp(prefix="claude-judge-"))
    (judge_home / "debug").mkdir()
    (judge_home / "projects").mkdir()
    (judge_home / "skills").mkdir()
    cred_src = find_claude_credentials()
    token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN", "").strip()
    if cred_src is not None:
        _copy_auth(cred_src, judge_home / ".credentials.json")
        log("claude eval agent: copied credentials.json into writable CLAUDE_CONFIG_DIR")
        if not token:
            token = _oauth_from_credentials(judge_home / ".credentials.json")
            if token:
                log("claude eval agent: loaded CLAUDE_CODE_OAUTH_TOKEN from credentials.json")
    if token and not (judge_home / ".credentials.json").is_file():
        (judge_home / ".credentials.json").write_text(
            json.dumps({"claudeAiOauth": {"accessToken": token}}) + "\n",
            encoding="utf-8",
        )
        (judge_home / ".credentials.json").chmod(stat.S_IRUSR | stat.S_IWUSR)
        log("claude eval agent: wrote credentials.json from CLAUDE_CODE_OAUTH_TOKEN")
    if not token and not (judge_home / ".credentials.json").is_file():
        shutil.rmtree(judge_home, ignore_errors=True)
        raise FileNotFoundError(
            "Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN or "
            "~/.claude/.credentials.json"
        )
    log(
        f"claude eval agent: CLAUDE_CONFIG_DIR={judge_home} "
        f"token_set={'yes' if token else 'no'} "
        f"credentials={'yes' if (judge_home / '.credentials.json').is_file() else 'no'}"
    )
    return judge_home, token


def claude_wrapper_script(real: str, effort: str) -> str:
    """Return bash for a PATH wrapper that injects effort and bypassPermissions.

    Args:
        real: Absolute path of the real ``claude`` binary.
        effort: ``low``, ``medium``, or ``high``.

    Returns:
        Script text (no secrets).
    """
    # Quote via json.dumps so the wrapper is safe for spaces in paths.
    real_q = json.dumps(real)
    effort_q = json.dumps(effort)
    return (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f"real={real_q}\n"
        f"effort={effort_q}\n"
        'for arg in "$@"; do\n'
        '  if [[ "$arg" == "-p" || "$arg" == "--print" ]]; then\n'
        '    exec "$real" --effort "$effort" --permission-mode bypassPermissions "$@"\n'
        "  fi\n"
        "done\n"
        'exec "$real" "$@"\n'
    )


@contextmanager
def claude_effort_on_path(effort: str) -> Iterator[Path]:
    """Prepend a ``claude`` wrapper that adds ``--effort`` on ``-p`` calls.

    Args:
        effort: ``low``, ``medium``, or ``high``.

    Yields:
        Directory holding the wrapper (prepended to ``PATH``).

    Raises:
        FileNotFoundError: When ``claude`` is not on PATH.
    """
    real = shutil.which("claude")
    if not real:
        raise FileNotFoundError("claude CLI not found on PATH for the Claude Code eval agent")
    wrapper_dir = Path(tempfile.mkdtemp(prefix="claude-wrap-"))
    wrapper = wrapper_dir / "claude"
    wrapper.write_text(claude_wrapper_script(real, effort), encoding="utf-8")
    wrapper.chmod(0o755)
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = f"{wrapper_dir}{os.pathsep}{old_path}"
    log(f"claude eval agent: PATH wrapper effort={effort} bypassPermissions")
    try:
        yield wrapper_dir
    finally:
        os.environ["PATH"] = old_path
        shutil.rmtree(wrapper_dir, ignore_errors=True)
