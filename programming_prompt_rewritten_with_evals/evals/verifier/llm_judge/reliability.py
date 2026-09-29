"""Detect unsupported or self-contradictory scores and retry once.

Shared by every eval agent so Codex, Claude Code, and Grok apply the same
reliability gate. The retry token never includes secrets or file contents.
"""

from __future__ import annotations

import ast
import json
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.log import log

MIN_RETRY_SECONDS = 40
_NOT_INSPECTED = re.compile(
    r"not inspected|withheld until|have not yet(?:\s+\w+){0,8}\s+inspect"
    r"|have not inspected|until the workspace python is inspected"
    r"|scoring is withheld|have not yet verified"
    r"|without (?:an? )?actual file"
    r"|(?:helper|boundary check)[^.!?\n]{0,60}(?:not (?:run|used)|was not executed)",
    re.IGNORECASE,
)
_PY_MENTION = re.compile(
    r"(?:(?:\.{0,2}/)?[\w.-]+(?:/[\w.-]+)*)\.py",
    re.IGNORECASE,
)
_CONTRADICTORY_NO = re.compile(
    r"\b(?:the )?(?:score|verdict|criterion|check|result)\s*"
    r"(?:should\s+be|is|:)\s*yes\b"
    r"|\b(?:so |the )?(?:criterion|check) passes[.!;,]?\s*$"
    r"|\b(?:all|every) functions? pass(?:[.!]|,?\s+so\b)"
    r"|\bevidence supports (?:a pass|yes)\b"
    r"|\bno (?:feature-boundary|workflow|logging) violation (?:was )?found\b"
    r"|\bfound no\b[^.!?\n]{0,120}\bviolation\b"
    r"|\bno violation found\b"
    r"|(?:^|[.!?]\s+)(?:I|we) (?:find|found) no (?:criterion )?violation\b"
    r"[^.!?\n]*[.!?]?\s*$"
    r"|(?:^|[.!?]\s+)(?:Thus[,\s]+)?(?:this|that) is not a violation\b"
    r"[^.!?\n]*[.!?]?\s*$"
    r"|\bscore yes\b"
    r"|\ball\b[^.!?\n]{0,100}\bfeatures?\b[^.!?\n]{0,100}"
    r"\b(?:satisfy|pass)\b[^.!?\n]{0,40}\bcriterion\b"
    r"|\b(?:a|the) no (?:is|was) not supported\b"
    r"|\bno verdict (?:is|was) unsupported\b",
    re.IGNORECASE,
)
_CONTRADICTORY_YES = re.compile(
    r"(?:^|[.!?]\s+)(?:the )?(?:criterion|requirement|check)"
    r"[^.!?\n]{0,120}\b(?:fails|is unmet|is not met)\b"
    r"[^.!?]*[.!?]?\s*$"
    r"|(?:^|[.!?]\s+)(?:the )?(?:first(?: concrete)?|(?:a )?concrete) "
    r"(?:feature|ledger|workflow) violation is\b"
    r"[^.!?]*[.!?]?\s*$",
    re.IGNORECASE,
)
_FALLTHROUGH_CLAIM = re.compile(
    r"`(?P<name>[A-Za-z_]\w*)`[^!?\n]{0,200}"
    r"\b(?:fall[ -]?through|implicit(?:ly)?\s+(?:returns?\s+)?None|"
    r"no\s+(?:explicit\s+)?return)\b",
    re.IGNORECASE,
)

AttemptFn = Callable[[str | None, int], tuple[str, list[dict[str, Any]]]]


class UnreliableJudgeScore(RuntimeError):
    """The judge did not produce a defensible score within the retry budget."""

    def __init__(self, reason: str, attempts: list[str] | None = None):
        """Retain attempted answers for the archived infrastructure diagnosis."""
        super().__init__(reason)
        self.raw = json.dumps({"retry_reason": reason, "attempts": attempts or []})


def mentioned_python_paths(reasoning: str) -> list[str]:
    """Return ``.py`` paths cited in judge reasoning.

    Args:
        reasoning: Free-text ``reasoning`` field from an eval agent.

    Returns:
        Path-like strings in mention order (trailing punctuation stripped).
    """
    found: list[str] = []
    for match in _PY_MENTION.findall(reasoning):
        cleaned = match.rstrip(")'\".,;:")
        if cleaned:
            found.append(cleaned)
    return found


def _path_is_listed(mentioned: str, keys: set[str]) -> bool:
    """Return True when *mentioned* matches a listed workspace Python file."""
    text = mentioned.strip().lower()
    if text in keys:
        return True
    return Path(text).name.lower() in keys


def _contradicted_fallthrough(
    reasoning: str, python_files: list[Path]
) -> str | None:
    """Name a claimed implicit exit blocked by a function's final return.

    A final top-level ``return`` prevents normal fallthrough for that function.
    This is a bounded syntax check, not a semantic logging score.

    Args:
        reasoning: Failing logging judge explanation.
        python_files: Exhaustive solution Python files.

    Returns:
        Function name when the claim contradicts source, otherwise None.
    """
    names = {match.group("name") for match in _FALLTHROUGH_CLAIM.finditer(reasoning)}
    if not names:
        return None
    endings: dict[str, list[bool]] = {}
    for path in python_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name in names:
                    endings.setdefault(node.name, []).append(isinstance(node.body[-1], ast.Return))
    for name, explicit_returns in endings.items():
        if all(explicit_returns):
            return name
    return None


def _contradicted_exit_trace(reasoning: str, python_files: list[Path]) -> str | None:
    """Identify a denied final print/return pair that is present in source.

    This bounded check triggers a reinspection, never a logging pass. Earlier
    returns and entry tracing still require the semantic judge's assessment.
    """
    if not re.search(r"no immediately preceding print|no exit trace|without.*exit print", reasoning, re.I):
        return None
    cited = set(re.findall(r"`([A-Za-z_]\w*)`", reasoning))
    for path in python_files:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name not in cited:
                continue
            if len(node.body) < 2:
                continue
            previous, final = node.body[-2:]
            if not isinstance(final, ast.Return) or not isinstance(previous, ast.Expr):
                continue
            call = previous.value
            if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                    and call.func.id == "print" and len(call.args) == 1):
                continue
            if final.value is not None and ast.dump(final.value) == ast.dump(call.args[0]):
                return node.name
    return None


def unreliable_score_reason(
    rows: list[dict[str, Any]], listed_keys: set[str],
    *, judge_name: str = "", python_files: list[Path] | None = None,
    workflow_issues: list[str] | None = None,
) -> str | None:
    """Return why a score contradicts supplied evidence, or None.

    Triggers on skip-inspect wording, a no verdict whose reasoning explicitly
    says the score should be yes, or ``.py`` citations outside the workspace
    listing. A workflow yes also retries when it contradicts concrete plan
    structure or internal-consistency issues. This gate never assigns a
    semantic replacement score.

    Args:
        rows: Parsed criterion scores.
        listed_keys: Lowercased names from ``listed_python_keys``.
        judge_name: Skill name; logging receives a syntax contradiction check.
        python_files: Solution source paths for that bounded check.
        workflow_issues: Concrete issues within the saved plan, not expected
            Feature counts derived from a task catalog.

    Returns:
        ``not_inspected:<criterion>``, ``contradictory_no:<criterion>``,
        ``source_conflict:<criterion>:<function>``, ``plan_conflict:<criterion>``, or
        ``wrong_path:<criterion>:<file>``.
    """
    for row in rows:
        reasoning = re.sub(r"[*`]", "", str(row.get("reasoning") or ""))
        if float(row["reward"]) >= 1.0:
            if _CONTRADICTORY_YES.search(reasoning):
                return f"contradictory_yes:{row['name']}"
            if judge_name == "workflow" and workflow_issues:
                return f"plan_conflict:{row['name']}"
            continue
        name = str(row["name"])
        if _NOT_INSPECTED.search(reasoning):
            return f"not_inspected:{name}"
        if _CONTRADICTORY_NO.search(reasoning):
            return f"contradictory_no:{name}"
        if judge_name == "logging" and python_files:
            function = _contradicted_fallthrough(str(row.get("reasoning") or ""), python_files)
            if function:
                return f"source_conflict:{name}:{function}"
            function = _contradicted_exit_trace(str(row.get("reasoning") or ""), python_files)
            if function:
                return f"exit_trace_conflict:{name}:{function}"
        mentioned = mentioned_python_paths(reasoning)
        if not mentioned:
            continue
        if any(_path_is_listed(item, listed_keys) for item in mentioned):
            continue
        return f"wrong_path:{name}:{Path(mentioned[0]).name}"
    return None


def retry_prompt(prompt: str, reason: str) -> str:
    """Append a one-shot correction after an unusable first score.

    Args:
        prompt: Original judge prompt (files already listed).
        reason: Short token from :func:`unreliable_score_reason` (no secrets).

    Returns:
        Prompt text for the retry attempt.
    """
    if reason.startswith(("contradictory_no:", "contradictory_yes:")):
        return (
            prompt
            + "\n\nRETRY: the previous JSON score was unusable because its "
            + "verdict contradicted its own reasoning. Re-evaluate the supplied "
            + "evidence and make the score agree with the concrete reason. "
            + "Do not change a genuine no merely to match prior wording.\n"
        )
    if reason.startswith("plan_conflict:"):
        return (
            prompt
            + "\n\nRETRY: the previous yes contradicted concrete issues in the supplied "
            + "plan table structure/internal consistency evidence. Reconcile those "
            + "issues with the workflow rules before scoring. Do not infer the "
            + "source request's sentence boundaries from a plan's claims.\n"
        )
    if reason.startswith("exit_trace_conflict:"):
        return (
            prompt
            + "\n\nRETRY: the previous no denied a final exit trace, but the cited "
            + "function ends with print(value) immediately followed by return value "
            + "in the actual source. Reinspect all actual returns and entry prints. "
            + "Identify a different concrete uncovered path or score yes.\n"
        )
    if reason.startswith("source_conflict:"):
        return (
            prompt
            + "\n\nRETRY: the previous no verdict claimed an implicit fallthrough "
            + "for a function whose final top-level statement is an explicit "
            + "return in the supplied source. Reinspect its function boundary "
            + "and every actual exit path. Score the source, not the prior claim.\n"
        )
    return (
        prompt
        + "\n\nRETRY: the previous JSON score was unusable "
        + f"({reason}). Score ONLY the Python files listed above. "
        + "Do not invent app.py. Do not answer no because you have not "
        + "inspected — the source is in this prompt.\n"
    )


def run_until_reliable(
    *,
    listed_keys: set[str],
    timeout: int,
    attempt: AttemptFn,
    judge_name: str = "",
    python_files: list[Path] | None = None,
    workflow_issues: list[str] | None = None,
) -> tuple[str, list[dict[str, Any]]]:
    """Run one judge attempt, then retry once on unreliable evidence.

    Args:
        listed_keys: Allowed ``.py`` citations from ``listed_python_keys``.
        timeout: Wall budget in seconds for both attempts combined.
        attempt: ``attempt(retry_reason_or_None, timeout_s) -> (raw, rows)``.
            First call uses ``reason=None`` and the full *timeout*. The retry
            call receives the reason token and remaining seconds.
        judge_name: Skill name for bounded source-conflict detection.
        python_files: Solution files for that detection.
        workflow_issues: Plan structure/consistency evidence for a workflow yes.

    Returns:
        Raw stdout and parsed rows from a reliable attempt. On retry, raw is a
        JSON envelope preserving both answers and the retry reason for auditing.

    Raises:
        UnreliableJudgeScore: No trustworthy score was produced.
    """
    started = time.monotonic()
    raw, rows = attempt(None, timeout)
    reason = unreliable_score_reason(
        rows, listed_keys, judge_name=judge_name, python_files=python_files,
        workflow_issues=workflow_issues
    )
    if reason is None:
        return raw, rows
    remaining = timeout - (time.monotonic() - started) - 5
    if remaining < MIN_RETRY_SECONDS:
        log(
            f"skip retry reason={reason} remaining_s={remaining:.0f} "
            f"min_s={MIN_RETRY_SECONDS}"
        )
        raise UnreliableJudgeScore(reason, [raw])
    log(f"retrying judge once reason={reason} remaining_s={remaining:.0f}")
    raw_retry, rows_retry = attempt(reason, int(remaining))
    second = unreliable_score_reason(
        rows_retry, listed_keys, judge_name=judge_name, python_files=python_files,
        workflow_issues=workflow_issues
    )
    if second:
        log(f"retry still unreliable reason={second}")
        raise UnreliableJudgeScore(second, [raw, raw_retry])
    log("retry produced a usable score")
    return json.dumps({"retry_reason": reason, "attempts": [raw, raw_retry]}), rows_retry
