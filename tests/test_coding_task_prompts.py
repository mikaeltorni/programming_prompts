"""Existing coding-task metadata and reference-solution checks."""

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
def test_prompt_declares_artifact_and_oracle(prompt: Path) -> None:
    """Every prompt names an artifact and has an oracle."""
    fields = parse_frontmatter(prompt)
    assert fields.get("artifact", "").startswith("/app/"), prompt.name
    assert fields.get("description"), f"{prompt.name}: missing description"
    oracle = ORACLES_DIR / f"{prompt.stem}.py"
    assert oracle.is_file(), f"{prompt.name}: missing oracle {oracle}"


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


def test_stats_oracle_runs_the_full_multi_step_flow() -> None:
    """The stats oracle implements all four Features of the prompt."""
    stats = load_oracle("stats")
    assert stats.run_stats("add 4") == "count=1"
    assert stats.run_stats("add 1") == "count=2"
    assert stats.run_stats("add 7") == "count=3"
    assert stats.run_stats("mean") == "mean=4"
    assert stats.run_stats("low") == "low=1"
    assert stats.run_stats("high") == "high=7"
    assert stats.run_stats("median") == "median=4"
    assert stats.run_stats("add 5") == "count=4"
    assert stats.run_stats("median") == "median=4.5"
    assert stats.run_stats("reset") == "cleared=4"


def test_stats_oracle_refuses_bad_commands() -> None:
    """The stats oracle raises ValueError on an empty set and unknown commands."""
    stats = load_oracle("stats")
    with pytest.raises(ValueError):
        stats.run_stats("mean")
    with pytest.raises(ValueError):
        stats.run_stats("median")
    with pytest.raises(ValueError):
        stats.run_stats("add")
    with pytest.raises(ValueError):
        stats.run_stats("fly")
