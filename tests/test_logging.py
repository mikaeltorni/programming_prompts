"""Tests for programming prompt utility logging."""

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "copy_prompts_to_projects.py"


def load_module():
    """Load the prompt-copy utility for path assertions."""
    spec = importlib.util.spec_from_file_location("copy_prompts_logging_test", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_log_file_is_stored_in_repository_log_directory():
    """Utility file logs should live under the repository .log directory."""
    module = load_module()
    assert module.LOG_FILE == MODULE_PATH.parent / ".log" / "copy_prompts_to_projects.log"
