"""Parse judge JSON and write Harbor/rewardkit-shaped reward files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from llm_judge.log import log

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _score_entry_schema() -> dict[str, Any]:
    """JSON Schema for one yes/no criterion object."""
    return {
        "type": "object",
        "properties": {
            "score": {"type": "string", "enum": ["yes", "no"]},
            "reasoning": {"type": "string"},
        },
        "required": ["score", "reasoning"],
        "additionalProperties": False,
    }


def response_schema(criteria: list[dict[str, str]]) -> dict[str, Any]:
    """Return the JSON Schema passed to constrained agent decode.

    Always keyed by criterion name (including a single criterion). Grok's
    constrained decode drops unknown keys; a flat ``{score, reasoning}``
    schema therefore yielded ``structured_output: {}`` when the model used
    the criterion name.

    Args:
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        An object schema whose properties are the criterion names.
    """
    props = {item["name"]: _score_entry_schema() for item in criteria}
    return {
        "type": "object",
        "properties": props,
        "required": list(props.keys()),
        "additionalProperties": False,
    }


def _as_object(value: Any) -> dict[str, Any] | None:
    """Return *value* as a dict, parsing a JSON object string when needed."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        stripped = value.strip()
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            fence = _JSON_FENCE.search(stripped)
            if not fence:
                return None
            try:
                parsed = json.loads(fence.group(1))
            except json.JSONDecodeError:
                return None
        return parsed if isinstance(parsed, dict) else None
    return None


def _looks_like_scores(data: dict[str, Any]) -> bool:
    """Return True when *data* is a yes/no score object or criterion map."""
    if "score" in data and not isinstance(data.get("score"), dict):
        return True
    return any(isinstance(value, dict) and "score" in value for value in data.values())


def _unwrap_agent_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Peel CLI ``--output-format json`` envelopes down to score JSON.

    Grok and Claude Code write
    ``{"type": "result", "structured_output": {...}, "result": "..."}``.
    When constrained decode fails, Grok still puts the scores in ``text``
    (with ``structuredOutputError`` set) — unwrap that string too.

    Args:
        payload: Parsed CLI JSON object.
    """
    for key in ("structured_output", "structuredOutput"):
        inner = _as_object(payload.get(key))
        if inner and _looks_like_scores(inner):
            return inner
    inner = _as_object(payload.get("result"))
    if inner and _looks_like_scores(inner):
        return inner
    inner = _as_object(payload.get("text"))
    if inner and _looks_like_scores(inner):
        log("unwrap scores from envelope text (structured output missing)")
        return inner
    return payload


def _json_objects_from_text(text: str) -> list[dict[str, Any]]:
    """Collect JSON objects from a blob, JSONL stream, or fenced block."""
    stripped = text.strip()
    found: list[dict[str, Any]] = []
    fence = _JSON_FENCE.search(stripped)
    if fence:
        obj = _as_object(fence.group(1))
        if obj is not None:
            found.append(obj)
    try:
        payload = json.loads(stripped)
        if isinstance(payload, dict):
            found.append(payload)
        return found
    except json.JSONDecodeError:
        pass
    for line in stripped.splitlines():
        obj = _as_object(line.strip())
        if obj is not None:
            found.append(obj)
    if found:
        return found
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        obj = _as_object(match.group(0))
        if obj is not None:
            found.append(obj)
    return found


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse score JSON from agent stdout (fence, JSONL, envelope, or raw).

    Args:
        text: Raw CLI stdout.

    Returns:
        Unwrapped score object.

    Raises:
        ValueError: When no JSON object can be found.
    """
    objects = _json_objects_from_text(text)
    if not objects:
        raise ValueError(f"LLM judge returned no JSON: {text.strip()[:200]}")
    chosen = objects[-1]
    for candidate in reversed(objects):
        if candidate.get("structured_output") or candidate.get("type") == "result":
            chosen = candidate
            break
    unwrapped = _unwrap_agent_payload(chosen)
    if unwrapped is chosen and chosen.get("type") == "result":
        log(
            "envelope has no structured_output "
            f"subtype={chosen.get('subtype')!r} is_error={chosen.get('is_error')!r} "
            f"keys={sorted(chosen)}"
        )
    return unwrapped


def _criterion_entry(data: dict[str, Any], name: str) -> dict[str, Any] | None:
    """Return the score object for *name*, including a flat yes/no payload."""
    entry = data.get(name)
    if isinstance(entry, dict) and "score" in entry:
        return entry
    if isinstance(entry, str):
        return {"score": entry, "reasoning": str(data.get("reasoning") or "")}
    if "score" in data and not isinstance(data.get("score"), dict):
        return {
            "score": data["score"],
            "reasoning": str(data.get("reasoning") or ""),
        }
    return None


def parse_scores(
    text: str, criteria: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Turn agent JSON into per-criterion reward rows.

    Accepts a CLI result envelope, a flat ``{score, reasoning}`` object, or
    ``{<criterion>: {score, reasoning}}``.

    Args:
        text: Raw CLI stdout.
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        Dicts with ``name``, ``raw``, ``reward``, ``reasoning``.
    """
    data = extract_json_object(text)
    if (
        len(criteria) == 1
        and "score" in data
        and not isinstance(data["score"], dict)
        and criteria[0]["name"] not in data
    ):
        data = {criteria[0]["name"]: data}
    rows: list[dict[str, Any]] = []
    for item in criteria:
        name = item["name"]
        entry = _criterion_entry(data, name)
        if entry is None:
            log(
                f"parse failed for {name!r}; payload keys={sorted(data)} "
                f"stdout_prefix={text.strip()[:240]!r}"
            )
            raise ValueError(
                f"LLM criterion {name!r} missing score object; "
                f"got {data.get(name)!r} keys={sorted(data)}"
            )
        raw = entry["score"]
        raw_text = str(raw).strip().lower()
        reward = 1.0 if raw_text in {"yes", "true", "1"} else 0.0
        rows.append(
            {
                "name": name,
                "raw": raw,
                "reward": reward,
                "reasoning": str(entry.get("reasoning") or ""),
                "description": item["description"],
            }
        )
    return rows


def _rewardkit_score_object(details: dict[str, Any]) -> dict[str, Any]:
    """Unwrap rewardkit details to the object that holds ``criteria``.

    Rewardkit writes ``{<reward_name>: {score, criteria, ...}}``. Our writer
    uses ``{"reward": {score, criteria, ...}}``.
    """
    inner = details.get("reward")
    if isinstance(inner, dict) and (
        "criteria" in inner or "score" in inner or "judge_output" in inner
    ):
        return inner
    for value in details.values():
        if isinstance(value, dict) and isinstance(value.get("criteria"), list):
            return value
    return details


def rows_from_rewardkit_details(
    details: dict[str, Any], criteria: list[dict[str, str]]
) -> list[dict[str, Any]]:
    """Map a rewardkit details payload onto the shared row shape.

    Args:
        details: Parsed ``reward-*-details.json`` (or its ``reward`` object).
        criteria: Name/description pairs from ``judge.toml``.

    Returns:
        Dicts with ``name``, ``raw``, ``reward``, ``reasoning``.
    """
    payload = _rewardkit_score_object(details)
    listed = payload.get("criteria") if isinstance(payload, dict) else None
    by_name: dict[str, dict[str, Any]] = {}
    if isinstance(listed, list):
        for item in listed:
            if isinstance(item, dict) and item.get("name"):
                by_name[str(item["name"])] = item
    rows: list[dict[str, Any]] = []
    for spec in criteria:
        name = spec["name"]
        entry = by_name.get(name, {})
        raw = entry.get("raw")
        value = entry.get("value")
        if value is None and raw is not None:
            raw_text = str(raw).strip().lower()
            value = 1.0 if raw_text in {"yes", "true", "1"} else 0.0
        try:
            reward = float(value) if value is not None else 0.0
        except (TypeError, ValueError):
            reward = 0.0
        if raw is None:
            raw = "yes" if reward >= 1.0 else "no"
        rows.append(
            {
                "name": name,
                "raw": raw,
                "reward": reward,
                "reasoning": str(entry.get("reasoning") or ""),
                "description": spec["description"],
            }
        )
    return rows


def write_reward(
    output: Path,
    rows: list[dict[str, Any]],
    raw_output: str,
    *,
    agent: str = "grok",
    ratelimit: bool = False,
) -> None:
    """Write ``reward-*.json`` plus sibling details JSON.

    Args:
        output: Path for the numeric reward file.
        rows: Per-criterion scores from :func:`parse_scores`.
        raw_output: Unparsed judge stdout kept for audits.
        agent: Eval-agent id stored in details (``grok``, ``cc``, ``codex``).
        ratelimit: When true, mark the score as a rate-limit skip, not a no.
    """
    overall = 0.0 if ratelimit else (
        1.0 if rows and all(float(row["reward"]) >= 1.0 for row in rows) else 0.0
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {"reward": overall}
    if ratelimit:
        payload["ratelimit"] = True
        payload["error"] = "ratelimit"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    criteria_rows = rows
    if ratelimit and not criteria_rows:
        criteria_rows = [{
            "name": "judge",
            "reward": 0.0,
            "raw": "ratelimit",
            "description": "eval agent rate-limited",
            "reasoning": "failed due to ratelimit",
        }]
    details = {
        "reward": {
            "score": overall,
            "aggregation": "all_pass",
            "kind": "agent",
            "agent": agent,
            "ratelimit": ratelimit,
            "criteria": [
                {
                    "name": row["name"],
                    "value": row["reward"],
                    "raw": "ratelimit" if ratelimit else row["raw"],
                    "weight": 1.0,
                    "description": row["description"],
                    "reasoning": (
                        "failed due to ratelimit" if ratelimit else row["reasoning"]
                    ),
                }
                for row in criteria_rows
            ],
            "judge_output": raw_output[:8000],
        }
    }
    details_path = output.parent / "reward-details.json"
    name = output.name
    if name.startswith("reward-") and name.endswith(".json") and name != "reward.json":
        inner = name[len("reward-") : -len(".json")]
        if inner:
            details_path = output.parent / f"reward-{inner}-details.json"
    payload = json.dumps(details, indent=2) + "\n"
    details_path.write_text(payload, encoding="utf-8")
    sibling = output.parent / "reward-details.json"
    if sibling != details_path:
        sibling.write_text(payload, encoding="utf-8")
    log(f"wrote reward={overall} agent={agent} to {output}")
