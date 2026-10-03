"""Public checks for the instruction builder; run with unittest discovery."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts/global_instructions.py"
SPEC = importlib.util.spec_from_file_location("global_instructions", SOURCE)
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class GlobalInstructionsTests(unittest.TestCase):
    def test_native_filenames_follow_explicit_instance_homes(self):
        self.assertEqual(builder.instruction_path("claude", Path("/isolated/claude")), Path("/isolated/claude/CLAUDE.md"))
        self.assertEqual(builder.instruction_path("codex", Path("/isolated/codex")), Path("/isolated/codex/AGENTS.md"))

    def test_complete_sources_and_unrelated_text_survive_reconfiguration(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            target.write_text("My own instructions.\n", encoding="utf-8")
            builder.write_instructions(target, [builder.Instruction("one", "First policy.")])
            self.assertIn("My own instructions.", target.read_text())
            self.assertIn("First policy.", target.read_text())
            builder.write_instructions(target, [builder.Instruction("two", "Second policy.")], owned_keys=["one"])
            self.assertNotIn("First policy.", target.read_text())
            self.assertIn("Second policy.", target.read_text())
            self.assertFalse(builder.write_instructions(target, [builder.Instruction("two", "Second policy.")]))

    def test_incomplete_markers_preserve_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "AGENTS.md"
            original = "<!-- programming-prompts:one:start -->\nUser text"
            target.write_text(original)
            with self.assertRaises(ValueError):
                builder.write_instructions(target, [], owned_keys=["one"])
            self.assertEqual(target.read_text(), original)

    def test_duplicate_or_empty_policy_is_rejected(self):
        with self.assertRaises(ValueError):
            builder.render_instructions([builder.Instruction("one", "")])
        with self.assertRaises(ValueError):
            builder.render_instructions([builder.Instruction("one", "x"), builder.Instruction("one", "y")])
