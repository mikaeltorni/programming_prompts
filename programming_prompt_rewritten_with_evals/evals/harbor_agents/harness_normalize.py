"""Normalization and eval-override helpers for Harbor harness arguments."""

from __future__ import annotations

import sys

from harbor_agents.harness_registry import (
    GROUPS,
    HARNESSES,
    REASONING_EFFORTS,
    choices_help,
    require_harness,
)


def _parse_csv_tokens(raw: str) -> tuple[str, ...]:
    """Split a comma-separated value and drop empty tokens.

    Parameters: raw - user input such as ``cc,codex`` or ``low``.

    Returns: Lowercased, whitespace-free tokens in order.
    """
    tokens: list[str] = []
    for part in raw.split(","):
        token = "".join(part.lower().split())
        if token:
            tokens.append(token)
    return tuple(tokens)


def _normalize_one_harness(token: str, *, raw: str) -> tuple[str, ...]:
    """Map one token to canonical harness ids.

    Parameters: token - normalized token; raw - original input for errors.

    Returns: Canonical harness ids, including expanded groups.
    """
    if token in GROUPS:
        return GROUPS[token]
    for spec in HARNESSES.values():
        if token in spec.aliases:
            return (spec.id,)
    raise ValueError(f"Unknown harness '{raw}' (use {choices_help()})")


def normalize_harness(raw: str) -> tuple[str, ...]:
    """Normalize a coding-harness CLI argument.

    Parameters: raw - harness aliases, groups, or comma-separated input.

    Returns: Deduplicated canonical harness ids in run order.
    """
    key = "".join(raw.lower().split())
    if key in GROUPS:
        return GROUPS[key]
    tokens = _parse_csv_tokens(raw)
    if not tokens:
        return GROUPS[""]
    ids: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        for harness_id in _normalize_one_harness(token, raw=raw):
            if harness_id not in seen:
                ids.append(harness_id)
                seen.add(harness_id)
    return tuple(ids)


def normalize_eval_agents(raw: str) -> tuple[str, ...]:
    """Normalize an ``evalAgent=`` argument.

    Parameters: raw - eval-agent aliases, groups, or comma-separated input.

    Returns: Canonical eval-agent ids, or empty to inherit the coding harness.
    """
    tokens = _parse_csv_tokens(raw)
    if not tokens:
        print("evalAgent omitted: inherit coding harness", file=sys.stderr)
        return ()
    ids: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if token in GROUPS and token != "":
            mapped = GROUPS[token]
        else:
            mapped = _normalize_one_harness(token, raw=raw)
        for harness_id in mapped:
            if harness_id not in seen:
                ids.append(harness_id)
                seen.add(harness_id)
    print(f"evalAgent resolved to: {', '.join(ids)}", file=sys.stderr)
    return tuple(ids)


def zip_eval_overrides(
    agents: tuple[str, ...],
    raw: str,
    *,
    kind: str,
    defaults: tuple[str, ...],
    allowed: tuple[str, ...] | None = None,
) -> tuple[str, ...]:
    """Align comma-separated overrides with eval agents.

    Parameters: agents - eval agents; raw - overrides; kind - error label; defaults - per-agent defaults; allowed - optional allowed values.

    Returns: One resolved override per eval agent.
    """
    if len(defaults) != len(agents):
        raise ValueError(f"{kind}: internal defaults length mismatch")
    tokens = [part.strip() for part in raw.split(",")] if raw.strip() else []
    tokens = [part for part in tokens if part]
    if allowed is not None:
        tokens = [part.lower() for part in tokens]
    if not tokens:
        values = defaults
    elif len(tokens) == 1:
        values = tuple(tokens[0] for _ in agents)
    elif len(tokens) == len(agents):
        values = tuple(tokens)
    else:
        raise ValueError(
            f"{kind} has {len(tokens)} value(s) but evalAgent has "
            f"{len(agents)} agent(s); use one value or one per agent"
        )
    if allowed is not None:
        for value in values:
            if value not in allowed:
                raise ValueError(
                    f"{kind}={value!r} is not one of {', '.join(allowed)}"
                )
    return values


def resolve_eval_models(agents: tuple[str, ...], raw: str) -> tuple[str, ...]:
    """Resolve the judge model for each eval agent.

    Parameters: agents - canonical eval-agent ids; raw - model overrides.

    Returns: One model id per eval agent.
    """
    defaults = tuple(require_harness(name).eval_model_name for name in agents)
    return zip_eval_overrides(
        agents, raw, kind="evalAgentModel", defaults=defaults
    )


def resolve_eval_efforts(agents: tuple[str, ...], raw: str) -> tuple[str, ...]:
    """Resolve the judge reasoning effort for each eval agent.

    Parameters: agents - canonical eval-agent ids; raw - effort overrides.

    Returns: One reasoning effort per eval agent.
    """
    defaults = tuple("low" for _ in agents)
    return zip_eval_overrides(
        agents,
        raw,
        kind="evalAgentReasoningEffort",
        defaults=defaults,
        allowed=REASONING_EFFORTS,
    )
