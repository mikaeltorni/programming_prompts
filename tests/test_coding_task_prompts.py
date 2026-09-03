"""Validate the Harbor coding-task prompts, their markers, and their oracles.

Each ``programming_prompt_rewritten_with_evals/evals/coding-prompts/<name>.md``
declares a Feature count that ``sync_tasks.sh`` writes to
``tests/feature_count.txt`` and that ``verifier/check_commits.py`` scores. The
sibling ``<name>.markers`` file pins one ``has:``/``lacks:`` token set per
Feature commit, so a drifted marker (wrong index, token the reference solution
never prints) would silently make the multi-step commits check unscoreable.
These tests keep prompt, markers, and oracle in sync, and smoke-test the
harder multi-step oracles end to end.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "programming_prompt_rewritten_with_evals" / "evals"
PROMPTS_DIR = EVALS / "coding-prompts"
ORACLES_DIR = EVALS / "oracles"


def prompt_paths() -> list[Path]:
    """List every coding-prompt markdown file.

    Parameters: none.

    Returns: sorted prompt paths, excluding the directory README.
    """
    return sorted(
        path
        for path in PROMPTS_DIR.glob("*.md")
        if path.name.lower() != "readme.md"
    )


def parse_frontmatter(path: Path) -> dict[str, str]:
    """Read the ``key: value`` frontmatter block of one prompt.

    Parameters: path - coding-prompt markdown file.

    Returns: mapping of frontmatter keys to raw string values.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path.name}: missing frontmatter"
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def parse_markers(path: Path) -> list[tuple[int, list[str], list[str]]]:
    """Parse one ``<name>.markers`` file into per-Feature token sets.

    Parameters: path - markers file (``N has:token lacks:token`` per line).

    Returns: list of ``(index, has_tokens, lacks_tokens)`` in file order.
    """
    parsed: list[tuple[int, list[str], list[str]]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        index = int(parts[0])
        has = [token[4:] for token in parts[1:] if token.startswith("has:")]
        lacks = [token[6:] for token in parts[1:] if token.startswith("lacks:")]
        parsed.append((index, has, lacks))
    return parsed


def load_oracle(name: str) -> ModuleType:
    """Import one oracle reference solution by task name.

    Parameters: name - task stem, e.g. ``bank``.

    Returns: the freshly imported oracle module (module-level state is reset).
    """
    path = ORACLES_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"oracle_{name}", path)
    assert spec is not None and spec.loader is not None, f"cannot import {path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("prompt", prompt_paths(), ids=lambda path: path.stem)
def test_prompt_declares_artifact_features_and_oracle(prompt: Path) -> None:
    """Every prompt names an artifact, a Feature count, and has an oracle."""
    fields = parse_frontmatter(prompt)
    assert fields.get("artifact", "").startswith("/app/"), prompt.name
    assert fields.get("description"), f"{prompt.name}: missing description"
    features = int(fields.get("features", "1"))
    assert features >= 1, prompt.name
    oracle = ORACLES_DIR / f"{prompt.stem}.py"
    assert oracle.is_file(), f"{prompt.name}: missing oracle {oracle}"


@pytest.mark.parametrize("prompt", prompt_paths(), ids=lambda path: path.stem)
def test_markers_cover_every_feature_and_match_the_oracle(prompt: Path) -> None:
    """Markers index Features 1..N and only pin tokens the oracle really prints."""
    features = int(parse_frontmatter(prompt).get("features", "1"))
    markers_path = prompt.with_suffix(".markers")
    if features < 2:
        return
    assert markers_path.is_file(), f"{prompt.name}: multi-Feature prompt needs markers"
    markers = parse_markers(markers_path)
    assert [index for index, _has, _lacks in markers] == list(range(1, features + 1)), (
        f"{markers_path.name}: markers must index Features 1..{features} in order"
    )
    oracle_source = (ORACLES_DIR / f"{prompt.stem}.py").read_text(encoding="utf-8")
    later_has = {
        token
        for index, has, _lacks in markers
        for token in has
    }
    for index, has, lacks in markers:
        assert has, f"{markers_path.name}: Feature {index} pins no has: token"
        for token in has:
            assert token in oracle_source, (
                f"{markers_path.name}: Feature {index} has:{token} never appears "
                f"in oracles/{prompt.stem}.py"
            )
        for token in lacks:
            assert token in later_has, (
                f"{markers_path.name}: Feature {index} lacks:{token} is not a "
                "later Feature's has: token"
            )
            assert token not in has, (
                f"{markers_path.name}: Feature {index} both has and lacks {token}"
            )


def test_bank_oracle_runs_the_full_multi_step_flow() -> None:
    """The bank oracle implements all four Features of the prompt."""
    bank = load_oracle("bank")
    assert bank.run_bank("open ada") == "opened=ada"
    assert bank.run_bank("open bob") == "opened=bob"
    assert bank.run_bank("deposit ada 50") == "balance=50"
    assert bank.run_bank("withdraw ada 20") == "balance=30"
    assert bank.run_bank("transfer ada bob 10") == "moved=10"
    assert bank.run_bank("history ada") == "history=+50,-20,-10"
    assert bank.run_bank("history bob") == "history=+10"
    assert bank.run_bank("assets") == "assets=30"


def test_bank_oracle_refuses_bad_commands() -> None:
    """The bank oracle raises ValueError on overdraft, duplicates, and unknowns."""
    bank = load_oracle("bank")
    bank.run_bank("open ada")
    with pytest.raises(ValueError):
        bank.run_bank("open ada")
    with pytest.raises(ValueError):
        bank.run_bank("withdraw ada 5")
    with pytest.raises(ValueError):
        bank.run_bank("deposit zoe 5")
    with pytest.raises(ValueError):
        bank.run_bank("transfer ada ada 1")
    with pytest.raises(ValueError):
        bank.run_bank("fly ada")
