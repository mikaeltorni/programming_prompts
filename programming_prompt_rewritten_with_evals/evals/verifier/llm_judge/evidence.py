"""Read-only Git evidence for semantic judges; no task-specific scoring.

Run this file with --repo PATH and optionally --commit REV [--path FILE].
The default JSON report lists history, parents, changed paths and worktrees.
Commit mode returns the actual diff or a source blob, without checking out refs.
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from llm_judge.log import log


def git(repo: Path, *args: str) -> str:
    """Run a bounded Git read and expose failures instead of empty evidence."""
    proc = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if proc.returncode:
        raise ValueError(proc.stderr.strip() or "Git evidence command failed")
    return proc.stdout


def history(repo: Path) -> dict:
    """Collect reachable commits in parent order, including merge topology."""
    commits = []
    for line in git(repo, "rev-list", "--reverse", "--topo-order", "--parents", "HEAD").splitlines():
        commit, *parents = line.split()
        commits.append({
            "commit": commit, "parents": parents,
            "subject": git(repo, "show", "-s", "--format=%s", commit).strip(),
            "changed_paths": git(repo, "diff-tree", "--root", "--no-commit-id",
                                 "--name-status", "-r", commit).splitlines(),
        })
    log(f"collected Git evidence commits={len(commits)}")
    return {
        "repository": str(repo.resolve()), "commits": commits,
        "worktrees": git(repo, "worktree", "list", "--porcelain"),
        "note": "Subjects and counts are not proof; inspect diffs and source at each feature boundary.",
    }


def commit_source_context(repo: Path, max_bytes: int = 200_000) -> str:
    """Pin real parent topology and complete Python trees for semantic judging.

    Args:
        repo: Live solution checkout.
        max_bytes: Maximum source/diff bytes to inline; omitted evidence is named.

    Returns:
        Git graph and source snapshots, with explicit missing evidence on error.
        No task markers, expected Feature counts, or semantic scores are inferred.
    """
    report = history(repo)
    parts = ["\nRead-only reachable Git graph (direct parents are ancestors):\n",
             json.dumps(report, indent=2)]
    used = 0
    for item in report["commits"]:
        if len(item["parents"]) > 1:
            continue
        sha = item["commit"]
        diff = git(repo, "show", "--format=fuller", "--no-ext-diff", "--no-textconv", sha)
        sources = []
        for name in git(repo, "ls-tree", "-r", "--name-only", sha).splitlines():
            if name.endswith(".py"):
                sources.append(f"\nSource at {sha}:{name}\n```python\n"
                               + git(repo, "show", f"{sha}:{name}") + "\n```\n")
        block = f"\nCommit {sha} actual diff:\n{diff}" + "".join(sources)
        size = len(block.encode("utf-8"))
        if used + size > max_bytes:
            parts.append(f"\nSource/diff for {sha} omitted at inline budget; inspect with the Git helper.")
        else:
            parts.append(block)
            used += size
    log(f"pinned commit evidence commits={len(report['commits'])} source_bytes={used}")
    return "\n".join(parts)


def python_boundaries(path: Path) -> dict:
    """Describe actual function boundaries without assigning a semantic score.

    Args:
        path: Complete Python source file to parse.

    Returns:
        Function spans, first executable statements and final statements.
        Docstrings are omitted from the entry boundary. Parsing/read errors
        propagate to the evidence caller instead of inventing source.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = node.body
        if (isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            body = body[1:]
        first = body[0] if body else node.body[0]
        last = body[-1] if body else node.body[-1]
        functions.append({
            "name": node.name, "line": node.lineno, "end_line": node.end_lineno,
            "docstring_lines": (ast.get_docstring(node, clean=False) or "").splitlines(),
            "first_statement_source": ast.get_source_segment(source, first),
            "last_statements_source": [ast.get_source_segment(source, item) for item in body[-2:]],
            "last_statement": type(last).__name__,
            "last_statement_source": ast.get_source_segment(source, last),
        })
    return {"file": str(path), "functions": functions,
            "note": "Syntax evidence only; inspect reachable control flow and prints."}


def main() -> int:
    """Print evidence to stdout; errors are explicit and never a failing score."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--commit")
    parser.add_argument("--path", help="source path at --commit; omit for its diff")
    parser.add_argument("--python-path", help="inspect function boundaries in a current Python file")
    args = parser.parse_args()
    if args.python_path and (args.commit or args.path):
        parser.error("--python-path cannot be combined with --commit or --path")
    if args.path and not args.commit:
        parser.error("--path requires --commit")
    try:
        if args.python_path:
            path = (args.repo / args.python_path).resolve()
            path.relative_to(args.repo.resolve())
            report = python_boundaries(path)
            log(f"collected Python boundaries functions={len(report['functions'])}")
            print(json.dumps(report, indent=2))
        elif args.commit:
            commit = git(args.repo, "rev-parse", "--verify", "--end-of-options",
                         args.commit + "^{commit}").strip()
            log(f"reading commit evidence commit={commit}")
            if args.path:
                print(git(args.repo, "show", f"{commit}:{args.path}"), end="")
            else:
                print(git(args.repo, "show", "--format=fuller", "--no-ext-diff",
                          "--no-textconv", commit, "--"), end="")
        else:
            print(json.dumps(history(args.repo), indent=2))
    except (ValueError, SyntaxError, OSError, subprocess.TimeoutExpired) as exc:
        log(f"evidence unavailable: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
