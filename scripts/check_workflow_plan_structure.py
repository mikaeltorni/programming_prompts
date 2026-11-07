#!/usr/bin/env python3
"""Check that workflow syntax evidence permits questions about unfinished work."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'programming_prompt_rewritten_with_evals/evals/verifier'))
from llm_judge.workspace import workflow_plan_structure


def main():
    """Exercise unfinished valid rows and malformed rows through the plan reader.

    Parameters: none.
    Returns: zero after independent structural assertions pass.
    """
    print('parameters=none')
    fixture = ROOT / 'programming_prompt_rewritten_with_evals/evals/seeds/workflow-question/tmp/workflow/benchmark.md'
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        plan = workspace / 'tmp/workflow.md'
        plan.parent.mkdir()
        original = fixture.read_text()
        plan.write_text(original)
        result = workflow_plan_structure(workspace)
        assert result['issues'] == [], result['issues']
        assert result['tasks'][2][2] == 'in_progress'
        assert result['microsteps'][3][5] == 'in_progress'
        for invalid in ('invalid', ''):
            plan.write_text(original.replace('| in_progress |', f'| {invalid} |'))
            result = workflow_plan_structure(workspace)
            assert result['issues'], (invalid, result)
        assert plan.read_text() != original
    print(0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
