"""Tests for rewritten-prompt BenchmarkCodex helpers."""

from __future__ import annotations

import re
import sys
from pathlib import Path

EVALS = (
    Path(__file__).resolve().parents[1]
    / "programming_prompt_rewritten_with_evals"
    / "evals"
)


def _import_helpers():
    path = str(EVALS)
    if path not in sys.path:
        sys.path.insert(0, path)
    from harbor_agents.clean_skills import (
        DEFAULT_CODEX_VERSION,
        build_clean_skills_register_command,
        load_codex_version,
    )

    return DEFAULT_CODEX_VERSION, build_clean_skills_register_command, load_codex_version


def test_codex_version_file_pins_0_147():
    version = (EVALS / "codex-version.txt").read_text(encoding="utf-8").strip()
    assert version == "0.147.0"


def test_dockerfile_pins_same_codex_version():
    version = (EVALS / "codex-version.txt").read_text(encoding="utf-8").strip()
    dockerfile = (
        EVALS / "tasks" / "calculator-comments" / "environment" / "Dockerfile"
    ).read_text(encoding="utf-8")
    assert f"CODEX_VERSION={version}" in dockerfile
    assert "npm uninstall --global @openai/codex" in dockerfile
    assert "rm -rf /root/.agents /root/.codex /etc/codex" in dockerfile


def test_harbor_job_config_pins_version_and_benchmark_agent():
    version = (EVALS / "codex-version.txt").read_text(encoding="utf-8").strip()
    config = (EVALS / "harbor.codex.yaml").read_text(encoding="utf-8")
    assert "harbor_agents.benchmark_codex:BenchmarkCodex" in config
    assert f'version: "{version}"' in config
    assert "../prompts/programming-skill" in config


def test_load_codex_version_reads_pin():
    default, _, load_codex_version = _import_helpers()
    loaded = load_codex_version(EVALS / "codex-version.txt")
    assert loaded == "0.147.0"
    assert loaded == default


def test_load_codex_version_falls_back_when_missing(tmp_path):
    default, _, load_codex_version = _import_helpers()
    assert load_codex_version(tmp_path / "missing-version.txt") == default


def test_clean_skills_command_wipes_without_skills():
    _, build_clean_skills_register_command, _ = _import_helpers()
    command = build_clean_skills_register_command(None)
    assert 'rm -rf "$HOME/.agents/skills"' in command
    assert "/etc/codex/skills" in command
    assert '"$CODEX_HOME/skills"' in command
    assert "cp -a" not in command


def test_clean_skills_command_installs_only_configured_dir():
    _, build_clean_skills_register_command, _ = _import_helpers()
    command = build_clean_skills_register_command("/harbor/skills")
    assert 'rm -rf "$HOME/.agents/skills"' in command
    assert 'cp -a /harbor/skills/. "$HOME/.agents/skills/"' in command
    assert 'cp -a /harbor/skills/. "$CODEX_HOME/skills/"' in command
    spaced = build_clean_skills_register_command("/tmp/skill dir")
    assert "cp -a '/tmp/skill dir'/." in spaced
    assert re.search(r"cp -a '.+'/\. \"\$HOME/\.agents/skills/\"", spaced)


def test_run_script_is_executable():
    script = EVALS / "run_codex_benchmark.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111
