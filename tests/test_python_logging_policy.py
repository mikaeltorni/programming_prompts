"""Policy tests for the python-logging plugin prompt.

The plugin must teach a single centralized logging module per project and the
standard call-tracing decorator (arguments on entry, return value on exit), and
the general guidelines must delegate Python logging mechanics to it.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = (
    ROOT / "plugins" / "python-logging" / "skills" / "python-logging" / "SKILL.md"
)
GENERAL_PATH = (
    ROOT
    / "plugins"
    / "general-programming-guidelines"
    / "skills"
    / "programming-guidelines"
    / "SKILL.md"
)


def skill_text() -> str:
    """Return the canonical python-logging skill text."""
    return SKILL_PATH.read_text(encoding="utf-8")


def test_skill_requires_one_centralized_logging_module():
    """The skill must mandate a single per-project logging module."""
    content = skill_text()

    assert "One logging module per project" in content
    assert "No mid-file logging helpers" in content
    assert "log_info()" in content and "log_error()" in content


def test_skill_decorator_logs_arguments_on_entry_and_return_on_exit():
    """The standard decorator must log args in and return value out, nothing else."""
    content = skill_text()

    assert "log_call" in content
    assert "argument" in content
    assert "return value on exit" in content
    assert "nothing else" in content.lower()


def test_skill_records_file_and_function_name():
    """Records must carry the wrapped function's file and qualified name."""
    content = skill_text()

    assert "file:qualname" in content or "file and" in content
    assert "co_filename" in content
    assert "__qualname__" in content


def test_skill_logging_is_best_effort_and_repo_local():
    """Logging must be best-effort, idempotent, and default to repo .log/."""
    content = skill_text()

    assert "best-effort" in content.lower()
    assert "NullHandler" in content
    assert ".log/" in content


def test_general_guidelines_delegate_python_logging_to_skill():
    """The main prompt should route Python logging mechanics to this skill."""
    content = GENERAL_PATH.read_text(encoding="utf-8")

    assert "python-logging" in content
    assert "centralized logging module" in content
