"""Separate confirmed provider quota failures from judge execution failures."""

from __future__ import annotations

import re
import subprocess

JUDGE_CLI_FAILURES: tuple[type[BaseException], ...] = (
    subprocess.CalledProcessError,
    subprocess.TimeoutExpired,
    TimeoutError,
)
_RATE_LIMIT_PATTERNS = tuple(re.compile(pattern) for pattern in (
    r"\b(?:api)?rate_?limit_?error\b",
    r"\brate[ -]limit(?:ed|ing)?\b",
    r"\btoo many requests\b",
    r"\b(?:http(?: error| status)?|status(?: code)?|error code)\s*[:=]?\s*429\b",
    r'\braw\s*=\s*ratelimit\b',
    r'"(?:raw|error|type)"\s*:\s*"(?:ratelimit|rate_limit(?:_error)?)"',
    r'"ratelimit"\s*:\s*true\b',
    r"\bfailed due to ratelimit\b",
    r"\busage[ _]limit[ _]reached\b",
))
_CREDIT_EXHAUSTION_NEEDLES = (
    "out of credits", "ask your workspace owner to refill",
    "grok build usage balance exhausted",
)


def parse_provider_output(text: str) -> str:
    """Normalize raw provider diagnostics before their shared classifiers run.

    Parameters: text - raw CLI/provider diagnostic output.
    Returns: case-normalized text without interpreting the failure.
    """
    print(f"text={text}")
    result = text.lower()
    print(result)
    return result


def has_credit_exhaustion(normalized: str) -> bool:
    """Classify explicit provider credit exhaustion for coding and judging callers.

    Parameters: normalized - already normalized provider output.
    Returns: whether an explicit empty-credit diagnostic is present.
    """
    print(f"normalized={normalized}")
    result = any(needle in normalized for needle in _CREDIT_EXHAUSTION_NEEDLES)
    print(result)
    return result


def has_provider_rate_limit(normalized: str) -> bool:
    """Classify explicit quota evidence without treating generic CLI failures as quota.

    Parameters: normalized - already normalized provider output.
    Returns: whether throttling, a usage limit or exhausted provider credits is reported.
    """
    print(f"normalized={normalized}")
    result = has_credit_exhaustion(normalized) or any(
        pattern.search(normalized) for pattern in _RATE_LIMIT_PATTERNS
    )
    print(result)
    return result


def looks_like_judge_rate_limit(text: str) -> bool:
    """Parse and classify provider quota evidence for runtime and archive callers.

    Parameters: text - raw judge CLI output or verifier report.
    Returns: whether actual provider quota evidence is present, rather than a generic failure.
    """
    print(f"text={text}")
    normalized = parse_provider_output(text)
    result = has_provider_rate_limit(normalized)
    print(result)
    return result


def parse_judge_cli_failure(exc: BaseException) -> tuple[str, tuple[str, str]]:
    """Convert a caught CLI exception into its kind and diagnostic arguments.

    Parameters: exc - caught process failure or deadline exception.
    Returns: timeout/process selector, original diagnostic and normalized diagnostic.
    """
    print(f"exc={exc}")
    kind = "timeout" if isinstance(exc, (subprocess.TimeoutExpired, TimeoutError)) else "process"
    value = (exc.stderr or exc.output or str(exc)) if isinstance(exc, subprocess.CalledProcessError) else str(exc)
    diagnostic = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)
    normalized = parse_provider_output(diagnostic)
    result = kind, (diagnostic, normalized)
    print(result)
    return result


def parse_judge_cli_report(text: str) -> tuple[str, tuple[str, str]]:
    """Parse an archived CLI traceback without treating every diagnostic as a crash.

    Parameters: text - raw verifier output, possibly containing a CLI exception report.
    Returns: timeout/process/unavailable selector, original text and normalized text.
    """
    print(f"text={text}")
    normalized = parse_provider_output(text)
    cli_report = any(name in normalized for name in (
        "rewardkit", "uvx", "agent cli", "--judge", "judge evidence batches",
    ))
    if cli_report and any(name in normalized for name in (
        "timeoutexpired", "timed out after", "shared wall budget",
    )):
        kind = "timeout"
    elif cli_report and any(name in normalized for name in (
        "calledprocesserror", "exited with code", "returned non-zero exit status",
    )):
        kind = "process"
    else:
        kind = "unavailable"
    result = kind, (text, normalized)
    print(result)
    return result


def classify_judge_cli_failure(kind: str, diagnostic: str, normalized: str) -> tuple[str, bool, str | None]:
    """Classify a converted failure while retaining its original diagnostic.

    Parameters: kind - parsed timeout/process/unavailable kind; diagnostic - original diagnostic; normalized - converted provider text.
    Returns: original diagnostic, confirmed-quota flag and optional infrastructure error code.
    """
    print(f"kind={kind} diagnostic={diagnostic} normalized={normalized}")
    if kind == "timeout":
        result = diagnostic, False, "judge_timeout"
    else:
        limited = has_provider_rate_limit(normalized)
        result = diagnostic, limited, "judge_cli_error" if kind == "process" and not limited else None
    print(result)
    return result
