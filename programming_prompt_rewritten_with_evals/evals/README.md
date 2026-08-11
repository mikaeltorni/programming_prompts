# Harbor evaluation

Five small write-from-scratch tasks measure whether Codex and/or Claude Code
follow selected programming skills while implementing tiny Python programs:

| Prompt | Entrypoint |
| --- | --- |
| [`coding-prompts/calculator.md`](coding-prompts/calculator.md) | `/app/calculator.py` → `run_calculator` |
| [`coding-prompts/todo.md`](coding-prompts/todo.md) | `/app/todo.py` → `run_todo` |
| [`coding-prompts/counter.md`](coding-prompts/counter.md) | `/app/counter.py` → `run_counter` |
| [`coding-prompts/greeter.md`](coding-prompts/greeter.md) | `/app/greeter.py` → `run_greeter` |
| [`coding-prompts/temperature.md`](coding-prompts/temperature.md) | `/app/temperature.py` → `run_temperature` |

Each coding prompt is the product instruction (what to build) plus “Follow the
provided programming skill.” Skills under
[`../prompts/programming-skills/`](../prompts/programming-skills/) guide *how*
to write it. Each skill has its own judge under [`judges/<skill>/`](judges/).

## Edit surfaces

Skills and judges:

- [`../prompts/programming-skills/srp/SKILL.md`](../prompts/programming-skills/srp/SKILL.md)
- [`../prompts/programming-skills/commenting/SKILL.md`](../prompts/programming-skills/commenting/SKILL.md)
- [`judges/srp/prompt.md`](judges/srp/prompt.md)
- [`judges/commenting/prompt.md`](judges/commenting/prompt.md)

Coding tasks — one markdown file each under
[`coding-prompts/`](coding-prompts/). Harbor `tasks/` trees are **generated**
by [`sync_tasks.sh`](sync_tasks.sh) (gitignored). Negative wording is generated
at runtime. Judge copies under `tasks/*/tests/judges/` are also runtime-only.

## CLI parameters

| Flag | Meaning |
| --- | --- |
| `harness=codex` / `--harness cc` | Agent harness: `codex`, `cc` (Claude Code), or `both` |
| *(omit harness)* | Runs **both** Codex and Claude Code |
| `--skills srp,commenting` | Which skills to inject/judge (default: all discovered) |
| `--skills=srp` / `-skills=srp` | Same, equals form |
| `--tasks todo,calculator` | Which coding prompts to run (default: all) |
| `--tasks=greeter` / `task=todo,counter` | Same, equals / bare forms |
| `--run-separately` / `--runSeparately` | One Harbor job per skill (costlier) |
| `--baseline` | No skills injected; selected judges still score |
| `--negative` | Auto-invert the selected skill (one skill unless separate) |
| `--install-only` | Reinstall/verify pinned CLI(s) in the task image |
| `-k` / `-n` / `-m` / `--ak` | Passed through to Harbor |

Harness aliases: `cc`, `claude`, `claude-code`, `claudecode` → Claude Code;
`codex`, `openai`, `gpt` → Codex; `both` / `all` / empty → both.

Without `--run-separately`, all selected skills are installed in **one** agent
session and **each** matching judge scores the same written code. With
`--run-separately`, each skill gets its own prompt instance + its own judge
(more subscription usage). Each Harbor job gets an **isolated** copy of the
selected tasks under `$JOBS/task-trees/<job>/` so `/tests/judges` cannot be
clobbered by the next skill job or a concurrent benchmark sharing
`evals/tasks/`.

Trial math: default `-k 5` is **5 attempts per selected coding task**. With all
5 tasks that is **25 trials per skill-job per harness**. `--run-separately`
with 2 skills ≈ **2×** that. Omit harness (both) ≈ **2×** again — e.g.
`harness` omitted + `--run-separately` + 2 skills + 5 tasks + `-k 5` ≈
**100 trials**. Defaults: Codex `openai/gpt-5.6-luna` @ low; Claude Code
`claude-opus-5` @ low (`--effort`).

After each job the wrapper prints trials, then categorized rollups: **by
harness**, **harness × skill**, **harness × task**, **harness × task × skill**,
plus a harness comparison table when both ran, and a GRAND TOTAL.

## Layout

```text
evals/
├── coding-prompts/         # edit these — one .md per coding task
│   ├── calculator.md
│   ├── counter.md
│   ├── greeter.md
│   ├── temperature.md
│   └── todo.md
├── oracles/                # reference solutions for Harbor oracle
├── task-template/          # shared Dockerfile + thin test.sh
├── judges/
│   ├── README.md
│   ├── srp/
│   │   ├── prompt.md
│   │   └── judge.toml
│   └── commenting/
│       ├── prompt.md
│       └── judge.toml
├── verifier/
│   ├── README.md
│   └── run_judges.sh
├── testing/
├── sync_tasks.sh           # coding-prompts → generated tasks/
├── sync_judges.sh          # judges + verifier → tasks/*/tests/
├── run_benchmark.sh        # Codex + Claude Code runner
├── run_codex_benchmark.sh  # thin shim → run_benchmark.sh harness=codex
├── codex-version.txt
├── claude-version.txt
└── tasks/                  # GENERATED (gitignored) — do not edit
```

`sync_tasks.sh` builds each Harbor task directory from
`coding-prompts/<name>.md` + `oracles/<name>.py` + `task-template/`.

## Judge reasoning in results

`verifier/run_judges.sh` (synced into each task) runs rewardkit per selected
skill, keeps `reward-<skill>-details.json` (including the judge’s `reasoning`
string), and writes an aggregate `reward-details.json` with per-skill `raw` +
`reasoning`. `run_benchmark.sh` prints those lines in the post-run
console summary:

```text
  judge[srp] answer: yes
  judge[srp] reason: …
  judge[commenting] answer: yes
  judge[commenting] reason: …
```

## Verify finished `/tmp` job roots

After positive and baseline runs, pass the two job temp dirs to the scripts
under [`testing/`](testing/):

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals/testing
./verify_with_ca.sh  "$POSITIVE_JOBS" "$BASELINE_JOBS"
./verify_with_cca.sh "$POSITIVE_JOBS" "$BASELINE_JOBS"
```

Each script opens a **new terminal window** and launches `ca -h -sol` or
`cca -opus -h` with a prompt that points at those exact paths plus the skill
and judge files.

## Tested platform

The Harbor workflow was exercised on Ubuntu 24.04 with Docker Engine, Harbor
`0.20.0`, Codex CLI `0.147.0`, Claude Code `2.1.227`, GPT-5.6 Luna at low
reasoning effort, and Claude Opus 5 at low effort.

## Clean agent instances (required for skill benchmarks)

Skill trials must not reuse host skill trees.

### Codex (`harness=codex`)

Every Harbor Codex trial already gets a fresh `CODEX_HOME=/tmp/codex-home`. This
suite goes further:

- Pin: [`codex-version.txt`](codex-version.txt) (`0.147.0`).
- [`harbor_agents/benchmark_codex.py`](harbor_agents/benchmark_codex.py) wipes
  `$HOME/.agents/skills`, `/etc/codex/skills`, and `$CODEX_HOME/skills`, then
  installs only the skills configured for that job.
- Auth: host `~/.codex/auth.json` bind-mount + `CODEX_FORCE_AUTH_JSON=1`.

### Claude Code (`harness=cc`)

- Pin: [`claude-version.txt`](claude-version.txt) (`2.1.227`).
- [`harbor_agents/benchmark_claude_code.py`](harbor_agents/benchmark_claude_code.py)
  wipes `$HOME/.claude/skills` and `$CLAUDE_CONFIG_DIR/skills`, then installs
  only the job’s skills (Harbor would otherwise copy host `~/.claude/skills`).
- Auth: reads `~/.claude/.credentials.json` → `CLAUDE_CODE_OAUTH_TOKEN` with
  `CLAUDE_FORCE_OAUTH=1` (token never printed). Also bind-mounts the credentials
  file into the trial.

Prefer [`./run_benchmark.sh`](run_benchmark.sh) over bare `-a codex` /
`-a claude-code` so the clean agents and version pins stay in force.

Reinstall or verify pinned CLIs inside the task environment:

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
./run_benchmark.sh --install-only                  # both harnesses
./run_benchmark.sh --install-only harness=codex
./run_benchmark.sh --install-only harness=cc
```

## Install Docker on Ubuntu 24.04

Harbor runs this evaluation in Docker. If `docker version` reports that the
command is missing, install Docker Engine from Docker's official Ubuntu
repository:

```bash
sudo apt update
sudo apt install -y ca-certificates curl

sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: noble
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF

sudo apt update
sudo apt install -y \
  docker-ce \
  docker-ce-cli \
  containerd.io \
  docker-buildx-plugin \
  docker-compose-plugin

sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"
```

## Activate Docker access in VS Code, Cursor, and tmux

Adding your user to the `docker` group does not update terminals that are
already running. VS Code, Cursor, and Agent Command Center may reconnect to an
older tmux server even after the IDE is restarted, so the old shell can continue
reporting `permission denied` for `/var/run/docker.sock`.

Replace the current shell with one that has the new group membership:

```bash
exec newgrp docker
```

The prompt will reappear without printing a success message. Stay in that new
shell and verify that `docker` is listed before testing Docker:

```bash
id -nG
docker version
docker compose version
docker run --rm hello-world
```

If `id -nG` does not contain `docker`, confirm Docker access for one command
with:

```bash
sg docker -c 'docker version && docker compose version && docker run --rm hello-world'
```

The Harbor commands below must still run from a shell whose `id -nG` output
contains `docker`; do not run Harbor with `sudo`, because that would use the
wrong home directory and Codex authentication.

These steps follow Docker's official
[Ubuntu installation instructions](https://docs.docker.com/engine/install/ubuntu/).
Do not install the similarly named `python3-karborclient` package suggested by
Ubuntu's command-not-found helper; it is an unrelated OpenStack client.

## Install Harbor and check Codex

Install the tested Harbor version and confirm that Codex is authenticated:

```bash
uv tool install harbor==0.20.0
harbor --version
codex login status
```

The layout follows Harbor's official
[task format](https://www.harborframework.com/docs/tasks).

## Set the paths once

Run the remaining commands in order from the Docker-enabled shell. Start by
entering this repository's `evals` directory:

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals

TASK="$PWD/tasks/calculator"
SKILL="$PWD/../prompts/programming-skills/srp"
JOBS="$(mktemp -d)"
MOUNTS="$(python3 -c 'import json, pathlib; print(json.dumps([{"type": "bind", "source": str(pathlib.Path.home() / ".codex" / "auth.json"), "target": "/root/.codex/auth.json", "read_only": True}]))')"
```

The read-only mount gives the LLM verifier access to the existing ChatGPT
subscription login. It does not copy the credential into this repository or
the saved Harbor job.

## Positive test

The oracle writes a single-responsibility reference implementation. This must
produce reward `1` (example uses the calculator task):

```bash
harbor run -p "$TASK" -a oracle --mounts "$MOUNTS" \
  -o "$JOBS" --job-name positive-oracle
find "$JOBS/positive-oracle" -name reward.json -print -exec cat {} \;
```

## Negative test (auto-invert the programming skill)

`--negative` auto-inverts the selected skill and rewrites each task instruction
with a one-line anti-skill note (no checked-in negative instruction files).
Multi-skill negative requires `--run-separately`.

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
# Codex only
./run_benchmark.sh harness=codex --negative --skills srp -k 5 -n 5
./run_benchmark.sh harness=codex --negative --skills commenting -k 5 -n 5
./run_benchmark.sh harness=codex --negative --skills srp,commenting --run-separately -k 5 -n 5
# Claude Code only
./run_benchmark.sh harness=cc --negative --skills srp -k 5 -n 5
# Both harnesses (≈ 2× trials)
./run_benchmark.sh --negative --skills srp,commenting --run-separately -k 5 -n 5
```

Expected rewards are mostly `0` for the inverted behavior.

## Verifier sanity (`nop`)

Harbor's `nop` agent deliberately changes nothing. The workspace stays empty, so
this must produce reward `0`:

```bash
harbor run -p "$TASK" -a nop --mounts "$MOUNTS" \
  -o "$JOBS" --job-name negative-empty
find "$JOBS/negative-empty" -name reward.json -print -exec cat {} \;
```

This proves the verifier rejects missing/non-SRP code. It is **not** a model
baseline.

## Baseline / no-skill negative (model pass rate without the prompt)

To measure how often the model satisfies the skill **without** injecting it,
keep the same tasks and inject **no skills**.

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
export JOBS="$(mktemp -d)"
./run_benchmark.sh harness=codex --baseline --skills srp,commenting -k 5 -n 5
./run_benchmark.sh harness=cc --baseline --skills srp,commenting -k 5 -n 5
# both harnesses:
./run_benchmark.sh --baseline --skills srp,commenting -k 5 -n 5
```

Compare to the with-skill runs:

```bash
./run_benchmark.sh harness=codex --skills srp,commenting --run-separately -k 5 -n 5
./run_benchmark.sh harness=cc --skills srp,commenting --run-separately -k 5 -n 5
```

## Test the real skill (Codex and/or Claude Code)

**Defaults:** Codex `openai/gpt-5.6-luna` @ **low**; Claude Code `claude-opus-5`
@ **low**. The LLM judge in `verifier/run_judges.sh` also uses low effort.

Sign in on the host:

```bash
codex login && codex login status
# Claude Code subscription token lives in ~/.claude/.credentials.json
# (Claude CLI `claude setup-token` / normal login on the host).
```

Then run (examples):

```bash
export JOBS="$(mktemp -d)"
# Codex positive, both skills in one session (~25 trials at -k 5)
./run_benchmark.sh harness=codex --skills srp,commenting -k 5 -n 5
# Claude Code positive, one skill per job (~50 trials)
./run_benchmark.sh harness=cc --skills srp,commenting --run-separately -k 5 -n 5
# Both harnesses × separately × 2 skills × 5 tasks × -k 5 ≈ 100 trials
./run_benchmark.sh --skills srp,commenting --run-separately -k 5 -n 5
```

`-k 5` schedules five attempts **per task**; `-n 5` runs up to five trials at
once. The wrapper defaults to the same `-k 5 -n 5` when you pass no Harbor
flags. After the job finishes it prints a categorized console summary.

Do not use bare `-a codex` / `-a claude-code` for these skill benchmarks: those
paths can leave host/user skill directories untouched and do not default to the
pinned CLIs.

## Model and run parameters

Override defaults on the command line (or edit `harbor.codex.yaml` /
`harbor.claude.yaml`). Useful Harbor flags:

| Flag | Meaning |
| --- | --- |
| `-m` / `--model` | Agent model id (applies to the selected harness job) |
| `--ak reasoning_effort=…` | Effort: `low`, `medium`, or `high` (Codex + Claude) |
| `--ak version=…` | CLI pin override |
| `-k` / `--n-attempts` | Independent attempts per task (default example: `5`) |
| `-n` / `--n-concurrent` | How many trials run in parallel (default example: `5`) |
| `--skill` | Extra skill directory (job config already injects skills) |

Examples:

```bash
# Default Luna-low / Opus-low via harness selection
./run_benchmark.sh harness=codex --skills srp -k 5 -n 5
./run_benchmark.sh harness=cc --skills srp -k 5 -n 5

# Higher reasoning
./run_benchmark.sh harness=codex --skills srp -k 5 -n 5 --ak reasoning_effort=high
./run_benchmark.sh harness=cc --skills srp -k 5 -n 5 --ak reasoning_effort=high

# Different model, one attempt
./run_benchmark.sh harness=codex --skills srp -k 1 -n 1 \
  -m openai/gpt-5.4 --ak reasoning_effort=medium
```

CLI `-m` / `--ak` values override the matching fields in the generated Harbor
job YAML. Keep subscription auth via the wrapper (Codex auth.json mount /
Claude OAuth token) unless you intentionally switch to API-key auth.

## Add the next evaluation

Keep each new coding task equally small:

1. add `coding-prompts/<name>.md` (frontmatter: `artifact`, `description`);
2. add `oracles/<name>.py` that implements the API for Harbor oracle runs;
3. run `./sync_tasks.sh` (or just the benchmark wrapper) to materialize
   `tasks/<name>/`;
4. add new skills only as `../prompts/programming-skills/<skill>/SKILL.md` plus
   `judges/<skill>/prompt.md` (+ `judge.toml`); edit the shared verifier at
   `verifier/run_judges.sh`;
5. run `./sync_judges.sh` (runtime), then oracle / `nop` / one real model trial.

`./run_benchmark.sh` auto-discovers every `tasks/*/` directory and every
selected skill. Prefer the wrapper over bare Harbor YAML.

Harbor records the complete jobs under the temporary `$JOBS` directory, so the
repository stays free of model transcripts, credentials, and generated output.
