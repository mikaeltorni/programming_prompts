#!/usr/bin/env bash
# Self-test default and explicit skill discovery without Docker, a GUI, or LLMs.
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/skills_tasks.sh"

fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
SKILLS_ROOT="$fixture/skills"
JUDGES_ROOT="$fixture/judges"
mkdir -p "$SKILLS_ROOT/standard" "$SKILLS_ROOT/workflow" \
  "$SKILLS_ROOT/logging-vague" "$JUDGES_ROOT/standard" \
  "$JUDGES_ROOT/workflow" "$JUDGES_ROOT/logging"
printf '%s\n' '---' >"$SKILLS_ROOT/standard/SKILL.md"
printf '%s\n' '---' >"$SKILLS_ROOT/workflow/SKILL.md"
printf '%s\n' '---' >"$SKILLS_ROOT/logging-vague/SKILL.md"
printf '%s\n' 'explicit-only' >"$SKILLS_ROOT/workflow/.opt-in"
: >"$JUDGES_ROOT/standard/prompt.md"
: >"$JUDGES_ROOT/workflow/prompt.md"
: >"$JUDGES_ROOT/logging/prompt.md"

fails=0

check() {
  # Check an independently expected public helper result.
  # Parameters: $1 - case label; $2 - expected value; $3 - observed value.
  # Returns: None; increments fails when the comparison fails.
  printf 'label=%s expected=%s actual=%s\n' "$1" "$2" "$3" >&2
  if [[ "$3" == "$2" ]]; then
    echo "PASS $1"
  else
    echo "FAIL $1 (expected: $2 | actual: $3)"
    fails=$((fails + 1))
  fi
  printf 'None\n' >&2
}

check "default excludes opt-in and vague skills" "standard" \
  "$(list_available_skills)"
check "default resolution stays legacy-only" "standard" \
  "$(resolve_skills '')"
check "explicit workflow selection resolves" "workflow" \
  "$(resolve_skills workflow)"
check "mixed explicit selection preserves order" $'standard\nworkflow' \
  "$(resolve_skills standard,workflow)"

SKILLS_ROOT="$(cd "$SCRIPT_DIR/../../prompts/programming-skills" && pwd)"
JUDGES_ROOT="$(cd "$SCRIPT_DIR/../judges" && pwd)"
eight=$'commenting\ncommits\ndebug\ndocs\nlogging\nsrp\ntesting\nworktree'
check "real default discovery is the available companions" "$eight" \
  "$(list_available_skills)"
check "omitting --skills resolves the available companions" "$eight" \
  "$(resolve_skills '')"
check "explicit workflow still resolves" "workflow" \
  "$(resolve_skills workflow)"
check "explicit debug_logs still resolves" "debug_logs" \
  "$(resolve_skills debug_logs)"
check "explicit logging-vague still resolves" "logging-vague" \
  "$(resolve_skills logging-vague)"


CODING_PROMPTS_DIR="$(cd "$SCRIPT_DIR/../coding-prompts" && pwd)"
DEBUG_PROMPTS_DIR="$(cd "$SCRIPT_DIR/../debug-prompts" && pwd)"
SUITE_ARG=''
SELECTED_SKILLS=(debug)
check "debug-only default selects repair cases" $'debug-cache\ndebug-catalog\ndebug-clock\ndebug-orders\ndebug-scheduler\ndebug-stock' "$(resolve_tasks '')"
SELECTED_SKILLS=(testing)
check "testing-only default keeps coding tasks" 8 "$(resolve_tasks '' | wc -l | tr -d ' ')"
if resolve_tasks debug-clock >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL unrelated skill accepted explicit debug case' >&2; exit 1
fi
grep -q 'requires --skills debug' "$fixture/error"
SUITE_ARG=debug
if resolve_tasks '' >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL unrelated skill accepted debug suite' >&2; exit 1
fi
SELECTED_SKILLS=(debug testing)
SUITE_ARG=''
check "mixed default includes both task families" 14 "$(resolve_tasks '' | wc -l | tr -d ' ')"
SUITE_ARG=coding
check "explicit coding suite excludes repairs" 8 "$(resolve_tasks '' | wc -l | tr -d ' ')"
if resolve_tasks debug-clock >"$fixture/output" 2>"$fixture/error"; then
  echo 'FAIL coding suite accepted debug case' >&2; exit 1
fi
SUITE_ARG=all
check "explicit mixed tasks resolve across families" $'counter\ndebug-clock' "$(resolve_tasks counter,debug-clock)"
echo 'ALL TASK FAMILY SELF-TESTS PASSED'

task_scope="$fixture/task-scope"
mkdir -p "$task_scope/counter/tests" "$task_scope/debug-clock/tests"
: > "$task_scope/counter/task.toml"
: > "$task_scope/debug-clock/task.toml"
printf 'Original counter request\n' > "$task_scope/counter/tests/task.md"
printf 'Original debug request\n' > "$task_scope/debug-clock/tests/task.md"
cp "$task_scope/counter/tests/task.md" "$task_scope/counter/instruction.md"
cp "$task_scope/debug-clock/tests/task.md" "$task_scope/debug-clock/instruction.md"
cp "$SCRIPT_DIR/../debug-cases/debug-clock.json" "$task_scope/debug-clock/tests/debug-cases.json"
TASKS_DIR="$task_scope" "$SCRIPT_DIR/../sync_judges.sh" > "$fixture/sync.log" 2>&1 || exit 1
check "default judge sync isolates repair judges" $'debug\ndebug_behavior' \
  "$(find "$task_scope/debug-clock/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
check "coding tasks never receive debug behavior checker" absent \
  "$(if [[ ! -d "$task_scope/counter/tests/judges/debug_behavior" && ! -d "$task_scope/counter/tests/judges/debug" ]]; then echo absent; fi)"
TASKS_DIR="$task_scope" "$SCRIPT_DIR/../sync_judges.sh" testing > "$fixture/sync.log" 2>&1 || exit 1
check "partial coding sync preserves repair judges" $'debug\ndebug_behavior' \
  "$(find "$task_scope/debug-clock/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
check "partial coding sync limits coding judges" testing \
  "$(find "$task_scope/counter/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"

# Coverage inventory: mixed positive/baseline scheduling -> one run_one_job
# invocation with both tasks; coding-only/debug-only -> retained routing;
# per-task documents -> exact selected skill bodies, excluding the other family;
# native registration -> all three runtimes and both families in temporary homes;
# baseline -> no instructions; legacy bundle -> original root document;
# missing trial identity/document -> setup rejection, never another family's body.
source "$SCRIPT_DIR/run_jobs.sh"
source "$SCRIPT_DIR/prepare_tasks.sh"
source "$SCRIPT_DIR/job_config.sh"

run_one_job() {
  # Capture the public scheduler invocation without starting Harbor.
  # Parameters: $1 - harness; $2 - job name; $3 - mode.
  # Returns: the captured harness, name, mode, tasks and skills on stdout.
  printf 'harness=%s job_name=%s mode=%s\n' "$1" "$2" "$3" >&2
  printf '%s|%s|%s|%s|%s\n' "$1" "$2" "$3" "${SELECTED_TASKS[*]}" "${SELECTED_SKILLS_FOR_JOB[*]}"
}
RUN_STAMP=fixture
RUN_SEPARATELY=0
BASELINE=0
SELECTED_SKILLS=(testing debug)
SELECTED_TASKS=(counter debug-clock)
check "mixed families use one positive job" \
  'codex|codex-skills__fixture|positive|counter debug-clock|testing debug' \
  "$(run_jobs_for_harness codex)"
BASELINE=1
check "mixed families use one baseline job" \
  'codex|codex-baseline__fixture|baseline|counter debug-clock|testing debug' \
  "$(run_jobs_for_harness codex)"
BASELINE=0
RUN_SEPARATELY=1
check "independent skill scores retain one mixed job" \
  'codex|codex-skills__fixture|positive|counter debug-clock|testing debug' \
  "$(run_jobs_for_harness codex)"
RUN_SEPARATELY=0
SELECTED_TASKS=(counter)
check "coding-only job keeps coding skills" \
  'codex|codex-skills__fixture|positive|counter|testing' \
  "$(run_jobs_for_harness codex)"
SELECTED_TASKS=(debug-clock)
check "debug-only job keeps debug skills" \
  'codex|codex-debug-skills__fixture|positive|debug-clock|debug' \
  "$(run_jobs_for_harness codex)"

SCRIPT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
JOBS="$fixture/jobs"
TASKS_DIR="$task_scope"
SELECTED_TASKS=(counter debug-clock)
SELECTED_SKILLS=(testing debug)
task_tree="$(prepare_job_tasks combined testing debug)" || exit 1
bundle="$JOBS/instruction-bundles/combined/global-instructions"
prepare_instruction_bundle "$bundle" testing debug || exit 1
all_bundle="$JOBS/instruction-bundles/all-policies/global-instructions"
mapfile -t all_skills < <(resolve_skills '')
prepare_instruction_bundle "$all_bundle" workflow "${all_skills[@]}" || exit 1
check "mixed task tree keeps coding judges" testing \
  "$(find "$task_tree/counter/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
check "mixed task tree keeps repair judges" $'debug\ndebug_behavior' \
  "$(find "$task_tree/debug-clock/tests/judges" -mindepth 1 -maxdepth 1 -type d -printf '%f\n' | sort)"
RUN_SEPARATELY=1
independent_tree="$(prepare_job_tasks independent testing debug)" || exit 1
for task in counter debug-clock; do
  check "$task keeps independent scoring marker" 1 \
    "$(cat "$independent_tree/$task/tests/eval_run_separately")"
done

PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" python3 - "$bundle" "$fixture" "$all_bundle" <<'PY'
import os
from pathlib import Path
import subprocess
import sys

from harbor_agents.clean_skills import (
    build_clean_skills_register_command,
    build_clean_claude_skills_register_command,
    build_clean_grok_skills_register_command,
)

bundle, fixture, all_bundle = map(Path, sys.argv[1:])
coding = (bundle / 'task-instructions/counter.md').read_text()
debug = (bundle / 'task-instructions/debug-clock.md').read_text()
assert '## Policy: v2:testing' in coding and '## Policy: v2:debug' not in coding
assert '## Policy: v2:debug' in debug and '## Policy: v2:testing' not in debug
all_coding = (all_bundle / 'task-instructions/counter.md').read_text()
all_debug = (all_bundle / 'task-instructions/debug-clock.md').read_text()
for name in ('workflow','commits','worktree','docs','srp','commenting','logging','testing'):
    assert f'## Policy: v2:{name}\n' in all_coding, name
    assert f'## Policy: v2:{name}\n' not in all_debug, name
assert '## Policy: v2:debug_logs\n' not in all_coding
assert '## Policy: v2:debug\n' not in all_coding
assert '## Policy: v2:debug\n' in all_debug

for runtime, builder, native in (
    ('codex', build_clean_skills_register_command, 'codex/AGENTS.md'),
    ('claude', build_clean_claude_skills_register_command, 'claude/CLAUDE.md'),
    ('grok', build_clean_grok_skills_register_command, '.grok/AGENTS.md'),
):
    for task, expected in (('counter', coding), ('debug-clock', debug)):
        home = fixture / f'{runtime}-{task}'
        home.mkdir()
        repo = home / 'repo'
        repo.mkdir()
        (repo / '.git').mkdir()
        command = builder(str(bundle.parent), f'{task}__trial__agent')
        # Wipe commands must stay inside fixture homes; /etc is never touched.
        command = command.replace('/Projects/app', str(repo)).replace('/etc/codex/skills', str(home / 'etc/skills'))
        env = dict(os.environ, HOME=str(home), CODEX_HOME=str(home/'codex'), CLAUDE_CONFIG_DIR=str(home/'claude'))
        result = subprocess.run(['bash', '-c', command], env=env, text=True, capture_output=True)
        assert result.returncode == 0, result.stderr
        target = home / native
        assert target.read_text() == expected, (runtime, task)
        assert subprocess.run(['bash', '-c', builder(None).replace('/Projects/app',str(repo)).replace('/etc/codex/skills',str(home/'etc/skills'))], env=env, capture_output=True).returncode == 0
        assert not target.exists(), runtime
        for bad_trial in (None, 'unknown__trial__agent'):
            bad_command = builder(str(bundle.parent), bad_trial).replace('/Projects/app',str(repo)).replace('/etc/codex/skills',str(home/'etc/skills'))
            assert subprocess.run(['bash','-c',bad_command], env=env, capture_output=True).returncode != 0
            assert not target.exists()
    # A pre-existing legacy bundle still installs its root instruction document.
    legacy = fixture / f'legacy-{runtime}' / 'global-instructions'
    legacy.mkdir(parents=True)
    (legacy/'instructions.md').write_text('Legacy selected policy\n')
    (legacy/'builder.py').write_text((bundle/'builder.py').read_text())
    command = builder(str(legacy.parent)).replace('/Projects/app',str(repo)).replace('/etc/codex/skills',str(home/'etc/skills'))
    assert subprocess.run(['bash','-c',command], env=env, capture_output=True).returncode == 0
    assert target.read_text() == 'Legacy selected policy\n'
print('PASS per-task policy isolation and native registration in all runtimes')
PY
if [[ $? -ne 0 ]]; then
  fails=$((fails + 1))
fi

if [[ $fails -eq 0 ]]; then
  echo "ALL SKILL DISCOVERY SELF-TESTS PASSED"
else
  echo "$fails skill discovery self-test(s) failed"
fi
exit $((fails > 0))
