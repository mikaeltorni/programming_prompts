"""Write worktree-check rewards in Harbor formats."""

from __future__ import annotations

import json
from pathlib import Path

from .rules import CheckResult


def write_reward(result: CheckResult, output: Path) -> None:
    """Write reward and detail JSON files.

    Parameters: result - checker outcome; output - reward JSON destination.

    Returns: None.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    reward = 1.0 if result.ok else 0.0
    raw = "yes" if result.ok else "no"
    output.write_text(
        json.dumps({"reward": reward}, indent=2) + "\n", encoding="utf-8"
    )
    details = {
        "reward": {
            "score": reward,
            "criteria": [
                {
                    "name": "worktree_layout",
                    "value": reward,
                    "raw": raw,
                    "weight": 1.0,
                    "description": "sibling .worktrees/<project>/ worktree, merge back, no push",
                    "reasoning": result.reasoning,
                }
            ],
            "kind": "programmatic",
            "judge_output": json.dumps(
                {"score": raw, "reasoning": result.reasoning}
            ),
        }
    }
    details_path = output.parent / "reward-details.json"
    skill = output.name
    if (
        skill.startswith("reward-")
        and skill.endswith(".json")
        and skill != "reward.json"
    ):
        inner = skill[len("reward-") : -len(".json")]
        if inner:
            details_path = output.parent / f"reward-{inner}-details.json"
    details_path.write_text(
        json.dumps(details, indent=2) + "\n", encoding="utf-8"
    )
    sibling = output.parent / "reward-details.json"
    if details_path != sibling:
        sibling.write_text(
            json.dumps(details, indent=2) + "\n", encoding="utf-8"
        )
