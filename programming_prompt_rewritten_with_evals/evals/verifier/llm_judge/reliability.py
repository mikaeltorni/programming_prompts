"""Detect unsupported or self-contradictory scores and retry once.

Shared by every eval agent so Codex, Claude Code, and Grok apply the same
reliability gate. The retry token never includes secrets or file contents.
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from llm_judge.evidence import git
from llm_judge.log import log
from llm_judge.testing_evidence import MAX_SOURCE_BYTES, equality_expectations

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
    r"|(?:^|[.!?;]\s+)no (?:criterion )?violation (?:is|was) evidenced[.!?]?\s*$"
    r"|\bscore yes\b"
    r"|\ball\b[^.!?\n]{0,100}\bfeatures?\b[^.!?\n]{0,100}"
    r"\b(?:satisfy|pass)\b[^.!?\n]{0,40}\bcriterion\b"
    r"|\b(?:a|the) no (?:is|was) not supported\b"
    r"|\bno verdict (?:is|was) unsupported\b",
    re.IGNORECASE,
)
_PERIOD_AFTER_CLAIM = re.compile(
    r'(?:^|[.!?]\s+)(?:the )?(?:source|(?:original )?request) '
    r'has a period after\s+[“"](?P<fragment>[^”"\n]{1,200})[”"]',
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
_EXPECTED_LITERAL_CLAIM = re.compile(
    r"\bexpects?\s+"
    r"(?:`(?P<backtick>[^`\n]{1,160})`|[\"“](?P<quoted>[^\"”\n]{1,160})[\"”])",
    re.IGNORECASE,
)
_TESTING_CITATION = re.compile(
    r"\bCitation:\s*(?:(?P<commit>[0-9a-f]{7,40}):)?"
    r"(?P<path>[^\s|:]+\.py):(?P<line>\d+)\s*\|\s*(?P<source>[^\n]+?)"
    r"(?=[ \t]+(?:Citation:\s*(?:[0-9a-f]{7,40}:)?[^\s|:]+\.py:\d+\s*\|"
    r"|TraceCitation:\s*[a-zA-Z0-9_-]+\.txt:\d+)|\n|$)"
)


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


def _contradicted_request_boundary(reasoning: str, request_text: str) -> bool:
    """Check a literal punctuation claim without deriving Features or counts.

    A fragment present in the request must actually be followed by the claimed
    period. Unmatched fragments remain the semantic judge's responsibility.
    """
    source = re.sub(r"\s+", " ", re.sub(r"[*`]", "", request_text))
    for match in _PERIOD_AFTER_CLAIM.finditer(reasoning):
        fragment = re.sub(r"\s+", " ", match.group("fragment")).strip()
        if fragment in source and not re.search(re.escape(fragment) + r"\s*\.", source):
            return True
    return False


def _contradicted_testing_literal(reasoning: str, python_files: list[Path]) -> bool:
    """Detect a quoted current expectation absent from cited literal assertions.

    Dynamic expected expressions and historical/corrective claims are left to
    the semantic judge. This only requests reinspection; it never awards yes.
    """
    cited = {Path(item).name for item in mentioned_python_paths(reasoning)}
    literals: set[str] = set()
    found = False
    for path in python_files:
        if path.name not in cited:
            continue
        try:
            with path.open("rb") as handle:
                data = handle.read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                return False
            values, dynamic = equality_expectations(ast.parse(data.decode("utf-8")))
        except (OSError, UnicodeError, SyntaxError):
            return False
        if dynamic:
            return False
        literals.update(values)
        found = found or bool(values)
    if not found:
        return False
    for match in _EXPECTED_LITERAL_CLAIM.finditer(reasoning):
        prefix = reasoning[max(0, match.start() - 180):match.start()]
        if not re.search(r"\.py\b|\blines?\s+\d", prefix, re.I):
            continue
        if re.search(r"historical|earlier commit|at commit|\b[0-9a-f]{7,40}\b"
                     r"|\b(?:no|not|never|missing|absent|omitted)\b"
                     r"|should\s*$|must\s*$|ought to\s*$", prefix, re.I):
            continue
        value = match.group("backtick") or match.group("quoted")
        if value not in literals:
            return True
    return False


def _trace_citation_issue(reasoning: str, logs_root: Path) -> str | None:
    """Validate transcript positions and optional exact quotes without judging order.

    Parameters: reasoning - semantic judge finding; logs_root - allowed transcript directory.
    Returns: missing/unavailable/mismatch/excess issue, or None for valid references.
    """
    print(f"reasoning={reasoning} logs_root={logs_root}")
    citations = list(re.finditer(
        r'\b(?:TraceCitation:\s*)?(?P<path>[a-zA-Z0-9_-]+\.txt):(?P<line>[0-9]+)'
        r'(?:[ \t]*\|[ \t]*(?P<excerpt>[^\n]+))?', reasoning))
    if not citations:
        print("missing")
        return "missing"
    if len(citations) > 16:
        print("excess")
        return "excess"
    for match in citations:
        if match.group("path") not in {"codex.txt", "claude-code.txt", "grok-build.txt", "grok.txt"}:
            print("unavailable")
            return "unavailable"
        token = match.group("line")
        if len(token) > 10:
            print("mismatch")
            return "mismatch"
        number = int(token)
        excerpt = match.group("excerpt")
        excerpt = excerpt.strip() if excerpt is not None else None
        found = False
        try:
            with (logs_root / match.group("path")).open("rb") as handle:
                for position, line in enumerate(handle, 1):
                    if position == number:
                        # A locator proves availability, not the semantic allegation.
                        # Supplied quotations still have to match the actual raw line.
                        found = excerpt is None or (bool(excerpt) and excerpt in line.decode("utf-8", errors="replace"))
                        break
        except OSError:
            print("unavailable")
            return "unavailable"
        if not found:
            print("mismatch")
            return "mismatch"
    print(None)
    return None


def _assertion_syntax_present(python_files: list[Path]) -> bool:
    """Detect literal assertion syntax conservatively without scoring verification.

    Parameters: python_files - current submitted Python files.
    Returns: True for observed assertion syntax or incomplete/unreadable evidence.
    """
    print(f"python_files={python_files}")
    if len(python_files) >= 40:
        print(True)
        return True
    for path in python_files:
        try:
            with path.open("rb") as handle:
                data = handle.read(MAX_SOURCE_BYTES + 1)
            if len(data) > MAX_SOURCE_BYTES:
                print(True)
                return True
            tree = ast.parse(data.decode("utf-8"))
        except (OSError, UnicodeError, SyntaxError, ValueError):
            print(True)
            return True
        for node in ast.walk(tree):
            name = node.func.attr if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) else ""
            if isinstance(node, ast.Assert) or name.startswith("assert") or name == "raises":
                print(True)
                return True
    print(False)
    return False


def _testing_citation_issue(
    reasoning: str, python_files: list[Path], *, logs_root: Path = Path("/logs/agent")
) -> str | None:
    """Validate Python quotes or available transcript references for a testing finding.

    Parameters: reasoning - judge finding; python_files - submitted Python paths;
        logs_root - allowed chronological transcript root.
    Returns: a quotation issue, or None when the cited evidence is authentic.
    """
    print(f"reasoning={reasoning} python_files={python_files} logs_root={logs_root}")
    citations = list(_TESTING_CITATION.finditer(reasoning))
    if not citations:
        trace_reference = re.search(r"\bTraceCitation:|\b[a-zA-Z0-9_-]+\.txt:\d+", reasoning)
        if not trace_reference and not _assertion_syntax_present(python_files):
            mentioned = mentioned_python_paths(reasoning)
            result = "path" if any(
                not any(path.as_posix() == name or path.as_posix().endswith("/" + name) for path in python_files)
                for name in mentioned
            ) else None
            print(result)
            return result
        result = _trace_citation_issue(reasoning, logs_root)
        print(result)
        return result
    if len(citations) > 16:
        result = "excess"
        print(result)
        return result
    root = None
    for match in citations:
        name = match.group("path").strip("`")
        commit = match.group("commit")
        if commit:
            try:
                if root is None:
                    root = Path(git(python_files[0].parent, "rev-parse", "--show-toplevel").strip())
                if Path(name).is_absolute() or ".." in Path(name).parts:
                    result = "path"
                    print(result)
                    return result
                text = git(root, "show", f"{commit}:{name}")
                if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
                    result = "unavailable"
                    print(result)
                    return result
                lines = text.splitlines()
            except (OSError, ValueError, UnicodeError, subprocess.TimeoutExpired):
                result = "unavailable"
                print(result)
                return result
        else:
            paths = [path for path in python_files if path.as_posix() == name
                     or path.as_posix().endswith("/" + name)]
            if len(paths) != 1:
                result = "path"
                print(result)
                return result
            try:
                with paths[0].open("rb") as handle:
                    data = handle.read(MAX_SOURCE_BYTES + 1)
                if len(data) > MAX_SOURCE_BYTES:
                    result = "unavailable"
                    print(result)
                    return result
                lines = data.decode("utf-8").splitlines()
            except (OSError, UnicodeError):
                result = "unavailable"
                print(result)
                return result
        line_number = match.group("line")
        if len(line_number) > 10:
            result = "mismatch"
            print(result)
            return result
        number = int(line_number)
        quoted = match.group("source").strip().strip("`")
        if number < 1 or number > len(lines) or lines[number - 1].strip() != quoted:
            result = "mismatch"
            print(result)
            return result
    result = _trace_citation_issue(reasoning, logs_root) if re.search(
        r"\b(?:TraceCitation:\s*)?(?:codex|claude-code|grok-build|grok)\.txt:\d+", reasoning) else None
    print(result)
    return result


def unreliable_score_reason(
    rows: list[dict[str, Any]], listed_keys: set[str],
    *, judge_name: str = "", python_files: list[Path] | None = None,
    workflow_issues: list[str] | None = None,
    request_text: str = "",
) -> str | None:
    """Return why a score contradicts supplied evidence, or None.

    Triggers on skip-inspect wording, a no verdict whose reasoning explicitly
    says the score should be yes, or ``.py`` citations outside a nonempty
    workspace listing. A workflow yes also retries when it contradicts concrete
    plan structure or internal-consistency issues. This gate never assigns a
    semantic replacement score.

    Args:
        rows: Parsed criterion scores.
        listed_keys: Lowercased names from ``listed_python_keys``.
        judge_name: Skill name; logging and testing receive syntax contradiction checks.
        python_files: Solution source paths for that bounded check.
        request_text: Original task context for literal punctuation claims.
        workflow_issues: Concrete issues within the saved plan, not expected
            Feature counts derived from a task catalog.

    Returns:
        ``not_inspected:<criterion>``, ``contradictory_no:<criterion>``,
        ``source_conflict:<criterion>:<function>``, ``plan_conflict:<criterion>``,
        ``request_boundary_conflict:<criterion>``, or ``wrong_path:<criterion>:<file>``.
        Testing may return ``testing_literal_conflict:<criterion>`` for a quoted
        current expectation absent from the cited file's literal assertions, or
        ``testing_citation_<issue>:<criterion>`` for missing/mismatched source quotes.
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
        if request_text and _contradicted_request_boundary(reasoning, request_text):
            return f"request_boundary_conflict:{name}"
        if _NOT_INSPECTED.search(reasoning):
            return f"not_inspected:{name}"
        if _CONTRADICTORY_NO.search(reasoning):
            return f"contradictory_no:{name}"
        if judge_name == "testing" and python_files and _contradicted_testing_literal(
            str(row.get("reasoning") or ""), python_files
        ):
            return f"testing_literal_conflict:{name}"
        if judge_name == "testing" and python_files:
            issue = _testing_citation_issue(str(row.get("reasoning") or ""), python_files)
            if issue:
                return f"testing_citation_{issue}:{name}"
        if judge_name == "logging" and python_files:
            function = _contradicted_fallthrough(str(row.get("reasoning") or ""), python_files)
            if function:
                return f"source_conflict:{name}:{function}"
            function = _contradicted_exit_trace(str(row.get("reasoning") or ""), python_files)
            if function:
                return f"exit_trace_conflict:{name}:{function}"
        mentioned = mentioned_python_paths(reasoning)
        # An empty source listing supports a missing-submission no verdict.
        # Naming the requested file then is not a contradictory source citation
        # and must not turn a submission failure into judge infrastructure error.
        if not mentioned or not listed_keys:
            continue
        if any(_path_is_listed(item, listed_keys) for item in mentioned):
            continue
        return f"wrong_path:{name}:{Path(mentioned[0]).name}"
    return None


def retry_prompt(prompt: str, reason: str) -> str:
    """Request reinspection after a score contradicts evidence or omits a quote.

    Parameters: prompt - original evidence-enriched judge instructions; reason - validation issue.
    Returns: the same prompt with one focused correction request appended.
    """
    print(f"prompt={prompt} reason={reason}")
    if reason.startswith(("contradictory_no:", "contradictory_yes:")):
        result = (prompt
            + "\n\nRETRY: the previous JSON score was unusable because its "
            + "verdict contradicted its own reasoning. Re-evaluate the supplied "
            + "evidence and make the score agree with the concrete reason. "
            + "Do not change a genuine no merely to match prior wording.\n"
        )
        print(result)
        return result
    if reason.startswith("testing_literal_conflict:"):
        result = (prompt
            + "\n\nRETRY: the previous no cited a quoted expected value absent "
            + "from the current literal equality assertions in its cited files. "
            + "Re-read the current assertion and its preceding fixture calls; "
            + "quote its actual expected expression. Distinguish historical "
            + "commit source from the current runner's imported source. Identify "
            + "a supported material failure or score yes; absence of a literal "
            + "alone is not a semantic failure or an automatic pass.\n"
        )
        print(result)
        return result
    if reason.startswith("testing_citation_"):
        criterion = reason.split(":", 1)[-1]
        result = (prompt
            + f"\n\nRETRY unresolved criterion: {criterion}. Include a verified reference inside each no criterion's own reasoning; another criterion's citation does not cover it. "
            + "\n\nRETRY: the previous testing no omitted or misstated its exact "
            + "source or chronological trace citation. For a chronology failure use "
            + "TraceCitation: codex.txt:LINE with the actual line number, without "
            + "copying or re-escaping the JSON record "
            + "(or the actual claude-code.txt/grok-build.txt/grok.txt). Raw trace "
            + "positions establish availability only; inspect those actual records "
            + "and explain the file-write/run order. "
            + "For absence of saved checks or a runner, cite the actual available file-listing, file-write or execution TraceCitation; do not quote a nonexistent test. "
            + "Alternatively cite an exact Python source/check line with Citation "
            + "and identify the decisive raw transcript positions in reasoning. "
            + "For source failures reinspect the decisive claim and include "
            + "a separate reasoning line: Citation: relative/path.py:LINE | "
            + "the exact source line, without a line-number prefix. Quote the "
            + "line without wrapping backticks or trailing prose. For a Git "
            + "historical claim use Citation: HASH:relative/path.py:LINE | "
            + "the exact line from that commit. Supply one to three citations. "
            + "Quote the assertion for a wrong-expectation claim, or the actual validation "
            + "owner and closest retained check for a missing-coverage claim. "
            + "Use the snapshot actually loaded by the runner. A quote confirms "
            + "source text only, not failure: reassess shared owners, fixtures "
            + "and later successful executions. Keep a supported failure, or "
            + "score yes when no material testing failure remains.\n"
        )
        print(result)
        return result
    if reason.startswith("plan_conflict:"):
        result = (prompt
            + "\n\nRETRY: the previous yes contradicted concrete issues in the supplied "
            + "plan table structure/internal consistency evidence. Reconcile those "
            + "issues with the workflow rules before scoring. Do not infer the "
            + "source request's sentence boundaries from a plan's claims.\n"
        )
        print(result)
        return result
    if reason.startswith("exit_trace_conflict:"):
        result = (prompt
            + "\n\nRETRY: the previous no denied a final exit trace, but the cited "
            + "function ends with print(value) immediately followed by return value "
            + "in the actual source. Reinspect all actual returns and entry prints. "
            + "Identify a different concrete uncovered path or score yes.\n"
        )
        print(result)
        return result
    if reason.startswith("request_boundary_conflict:"):
        result = (prompt
            + "\n\nRETRY: the previous no claimed a period after a quoted request "
            + "fragment, but that period is absent from the supplied original text. "
            + "Copy the exact source characters around the alleged boundary. "
            + "Re-enumerate complete sentences without inserting punctuation, "
            + "then judge the actual ledger and history.\n"
        )
        print(result)
        return result
    if reason.startswith("source_conflict:"):
        result = (prompt
            + "\n\nRETRY: the previous no verdict claimed an implicit fallthrough "
            + "for a function whose final top-level statement is an explicit "
            + "return in the supplied source. Reinspect its function boundary "
            + "and every actual exit path. Score the source, not the prior claim.\n"
        )
        print(result)
        return result
    result = (prompt
        + "\n\nRETRY: the previous JSON score was unusable "
        + f"({reason}). Score ONLY the Python files listed above. "
        + "Do not invent app.py. Do not answer no because you have not "
        + "inspected — the source is in this prompt.\n"
    )
    print(result)
    return result


def run_until_reliable(
    *,
    listed_keys: set[str],
    timeout: int,
    attempt: AttemptFn,
    judge_name: str = "",
    python_files: list[Path] | None = None,
    workflow_issues: list[str] | None = None,
    request_text: str = "",
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
        request_text: Original task context for literal punctuation claims.

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
        workflow_issues=workflow_issues, request_text=request_text
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
        workflow_issues=workflow_issues, request_text=request_text
    )
    if second:
        log(f"retry still unreliable reason={second}")
        raise UnreliableJudgeScore(second, [raw, raw_retry])
    log("retry produced a usable score")
    return json.dumps({"retry_reason": reason, "attempts": [raw, raw_retry]}), rows_retry
