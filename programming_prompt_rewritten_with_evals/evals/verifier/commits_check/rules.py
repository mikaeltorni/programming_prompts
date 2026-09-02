"""Apply the Harbor feature-commit count and per-commit marker rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from worktree_check.git_io import git_ok, root_commits
from worktree_check.rules import CheckResult

# Keep in sync with sync_tasks.sh SEED_SUBJECT (skipped in Feature-commit counts).
SEED_SUBJECT = "Seed task files"
DEFAULT_FEATURE_COUNT_FILE = Path("/tests/feature_count.txt")


@dataclass(frozen=True)
class FeatureMarker:
    """Tokens the Nth Feature commit's Python tree must contain or omit.

    Parameters: index - 1-based Feature commit; has - substrings that must
        appear; lacks - substrings that must not appear.

    Returns: n/a (data).
    """

    index: int
    has: list[str] = field(default_factory=list)
    lacks: list[str] = field(default_factory=list)


def parse_feature_spec(path: Path | None = None) -> tuple[int, list[FeatureMarker]]:
    """Read Feature count and optional per-commit markers.

    Parameters: path - ``feature_count.txt`` (first line integer, later lines
        ``N has:token lacks:token``); defaults to /tests/feature_count.txt.

    Returns: required count (>= 1) and marker list. Missing files yield (1, []).
    """
    target = path if path is not None else DEFAULT_FEATURE_COUNT_FILE
    try:
        text = target.read_text(encoding="utf-8")
    except OSError:
        return 1, []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 1, []
    try:
        need = int(lines[0])
    except ValueError:
        return 1, []
    if need < 1:
        need = 1
    markers: list[FeatureMarker] = []
    for line in lines[1:]:
        if line.startswith("#"):
            continue
        marker = _parse_marker_line(line)
        if marker is not None:
            markers.append(marker)
    return need, markers


def _parse_marker_line(line: str) -> FeatureMarker | None:
    """Parse one ``N has:token lacks:token`` line.

    Parameters: line - stripped marker line.

    Returns: FeatureMarker, or None when the line has no index.
    """
    parts = line.split()
    if not parts:
        return None
    try:
        index = int(parts[0])
    except ValueError:
        return None
    if index < 1:
        return None
    has: list[str] = []
    lacks: list[str] = []
    for token in parts[1:]:
        if token.startswith("has:") and len(token) > 4:
            has.append(token[4:])
        elif token.startswith("lacks:") and len(token) > 6:
            lacks.append(token[6:])
    return FeatureMarker(index=index, has=has, lacks=lacks)


def read_required_features(path: Path | None = None) -> int:
    """Read how many Features the coding prompt declared.

    Parameters: path - file with count on the first line; defaults to
        /tests/feature_count.txt.

    Returns: required Feature count, at least 1. Missing or unreadable files yield 1.
    """
    need, _markers = parse_feature_spec(path)
    return need


def _feature_py_commits(repo: Path) -> list[tuple[str, str]]:
    """List non-merge Python-changing commits after the empty root.

    Parameters: repo - project checkout.

    Returns: (hash, subject) oldest first. Seed commits are skipped.
    """
    roots = root_commits(repo)
    if not roots:
        return []
    log_text = git_ok(
        repo,
        "log",
        "--reverse",
        "--no-merges",
        "--format=%H%x09%s",
        f"{roots[0]}..HEAD",
    )
    counted: list[tuple[str, str]] = []
    for line in log_text.splitlines():
        if not line.strip():
            continue
        commit, _, subject = line.partition("\t")
        if subject.strip() == SEED_SUBJECT:
            continue
        names = git_ok(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            commit,
        )
        if any(name.endswith(".py") for name in names.splitlines() if name.strip()):
            counted.append((commit, subject.strip() or commit[:12]))
    return counted


def _python_at_commit(repo: Path, commit: str) -> str:
    """Concatenate Python blobs at one commit.

    Parameters: repo - project checkout; commit - hash to inspect.

    Returns: joined file contents for substring search.
    """
    names = git_ok(repo, "ls-tree", "-r", "--name-only", commit)
    chunks: list[str] = []
    for name in names.splitlines():
        if not name.endswith(".py"):
            continue
        if any(part in {".git", "__pycache__", ".worktrees"} for part in Path(name).parts):
            continue
        blob = git_ok(repo, "show", f"{commit}:{name}")
        if blob:
            chunks.append(blob)
    return "\n".join(chunks)


def _check_markers(
    repo: Path,
    commits: list[tuple[str, str]],
    markers: list[FeatureMarker],
) -> CheckResult | None:
    """Fail when Feature capabilities do not land one per commit, in order.

    Each marker is matched to the earliest commit (at or after the commit that
    matched the previous marker plus one) whose Python tree contains all of its
    has-tokens. Matching by search rather than by position tolerates extra
    non-Feature commits (fixups, docs, README) between Feature commits while
    still requiring every Feature to land in its own, later commit and to keep
    later-Feature tokens out of the earlier one.

    Parameters: repo - project checkout; commits - Python-changing commits
        oldest first; markers - per-Feature has/lacks tokens.

    Returns: failure result, or None when every marker matches.
    """
    cursor = 0
    sources: dict[str, str] = {}

    def tree_of(commit: str) -> str:
        """Return the concatenated Python sources at one commit, memoized.

        Parameters: commit - hash to inspect.

        Returns: joined file contents for substring search.
        """
        if commit not in sources:
            sources[commit] = _python_at_commit(repo, commit)
        return sources[commit]

    for marker in markers:
        matched: int | None = None
        for position in range(cursor, len(commits)):
            commit, _subject = commits[position]
            if all(token in tree_of(commit) for token in marker.has):
                matched = position
                break
        if matched is None:
            missing_all = sorted(
                {
                    token
                    for token in marker.has
                    if not any(
                        token in tree_of(commit) for commit, _s in commits[cursor:]
                    )
                }
            ) or list(marker.has)
            return CheckResult(
                False,
                f"Feature {marker.index} never lands in its own commit after "
                f"Feature {marker.index - 1}: missing {missing_all!r} "
                f"({len(commits)} Python commit(s) total)",
            )
        commit, subject = commits[matched]
        leaked = [token for token in marker.lacks if token in tree_of(commit)]
        if leaked:
            return CheckResult(
                False,
                f"Feature {marker.index} commit {subject!r} "
                f"still contains later-Feature {leaked!r}",
            )
        cursor = matched + 1
    return None


def check_repo(
    repo: Path,
    required: int | None = None,
    markers: list[FeatureMarker] | None = None,
    spec_path: Path | None = None,
) -> CheckResult:
    """Inspect git history for one Python commit per declared Feature.

    Parameters: repo - project checkout; required - Feature count override;
        markers - optional per-commit has/lacks tokens; spec_path - file to
        parse when required/markers are omitted.

    Returns: pass/fail state and reasoning.
    """
    repo = repo.resolve()
    if git_ok(repo, "rev-parse", "--is-inside-work-tree") != "true":
        return CheckResult(False, f"{repo} is not a git working tree")
    if required is None and markers is None:
        need, parsed = parse_feature_spec(spec_path)
    else:
        need = required if required is not None else 1
        parsed = markers if markers is not None else []
    commits = _feature_py_commits(repo)
    count = len(commits)
    subjects = ", ".join(subject for _hash, subject in commits) if commits else "none"
    if count < need:
        return CheckResult(
            False,
            f"need at least {need} Python Feature commit(s) after init "
            f"(excluding seed); found {count} ({subjects})",
        )
    marker_fail = _check_markers(repo, commits, parsed)
    if marker_fail is not None:
        return marker_fail
    extra = ""
    if parsed:
        extra = "; sequential Feature markers matched"
    return CheckResult(
        True,
        f"{count} Python Feature commit(s) after init (required {need}): "
        f"{subjects}{extra}",
    )
