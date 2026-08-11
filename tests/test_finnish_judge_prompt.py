"""Guard the calculator-comments LLM judge prompt against soft language checks."""

from __future__ import annotations

from pathlib import Path

TESTS = (
    Path(__file__).resolve().parents[1]
    / "programming_prompt_rewritten_with_evals"
    / "evals"
    / "tasks"
    / "calculator-comments"
    / "tests"
)


def test_judge_prompt_rejects_swedish_and_keeps_criteria_placeholder():
    prompt = (TESTS / "judge-prompt.md").read_text(encoding="utf-8")
    assert "{criteria}" in prompt
    lowered = prompt.lower()
    assert "swedish" in lowered or "svenska" in lowered
    assert "finnish" in lowered or "suomi" in lowered
    assert "if unsure" in lowered or "when unsure" in lowered


def test_criterion_toml_points_at_prompt_and_rejects_swedish():
    toml_text = (TESTS / "finnish-comments.toml").read_text(encoding="utf-8")
    assert 'prompt_template = "judge-prompt.md"' in toml_text
    assert "Swedish" in toml_text or "swedish" in toml_text
    assert "Addera" in toml_text
    assert "Finnish" in toml_text or "finnish" in toml_text


def test_verifier_uses_medium_reasoning_for_language_check():
    script = (TESTS / "test.sh").read_text(encoding="utf-8")
    assert 'model_reasoning_effort = "medium"' in script
