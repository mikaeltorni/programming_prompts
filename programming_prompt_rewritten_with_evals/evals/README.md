# Harbor evaluation

Five small write-from-scratch tasks measure whether Codex follows selected
programming skills while implementing tiny Python programs:

| Task | Entrypoint |
| --- | --- |
| [`tasks/calculator`](tasks/calculator) | `/app/calculator.py` → `run_calculator` |
| [`tasks/todo`](tasks/todo) | `/app/todo.py` → `run_todo` |
| [`tasks/counter`](tasks/counter) | `/app/counter.py` → `run_counter` |
| [`tasks/greeter`](tasks/greeter) | `/app/greeter.py` → `run_greeter` |
| [`tasks/temperature`](tasks/temperature) | `/app/temperature.py` → `run_temperature` |

Each task instruction is the product prompt (what to build) plus “Follow the
provided programming skill.” Skills under
[`../prompts/programming-skills/`](../prompts/programming-skills/) guide *how*
to write it. Each skill has its own judge under [`judges/<skill>/`](judges/).

## Edit surfaces

Skills and judges — two of each right now:

- [`../prompts/programming-skills/srp/SKILL.md`](../prompts/programming-skills/srp/SKILL.md)
- [`../prompts/programming-skills/commenting/SKILL.md`](../prompts/programming-skills/commenting/SKILL.md)
- [`judges/srp/prompt.md`](judges/srp/prompt.md)
- [`judges/commenting/prompt.md`](judges/commenting/prompt.md)

Coding tasks — one short sentence each under `tasks/*/instruction.md`.
Negative wording is generated at runtime (no per-task negative files).
Judge copies under `tasks/*/tests/judges/` are runtime-only (gitignored).

## CLI parameters

| Flag | Meaning |
| --- | --- |
| `--skills srp,commenting` | Which skills to inject/judge (default: all discovered) |
| `--skills=srp` / `-skills=srp` | Same, equals form |
| `--run-separately` / `--runSeparately` | One Harbor job per skill (costlier) |
| `--baseline` | No skills injected; selected judges still score |
| `--negative` | Auto-invert the selected skill (one skill unless separate) |
| `--install-only` | Reinstall/verify pinned Codex in the task image |
| `-k` / `-n` / `-m` / `--ak` | Passed through to Harbor |

Without `--run-separately`, all selected skills are installed in **one** Codex
session and **each** matching judge scores the same written code. With
`--run-separately`, each skill gets its own prompt instance + its own judge
(more subscription usage).

Trial math: default `-k 5` is **5 attempts per coding task**. With 5 tasks that
is **25 trials per skill-job**. `--run-separately` with 2 skills ≈ **50
trials**. Model stays **gpt-5.6-luna / low**.

After each job the wrapper prints trials, per-task rates, **per-skill judge**
rates (answer + **reasoning**), and a TOTAL line.

## Layout

```text
evals/
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
│   └── run_judges.sh       # shared Harbor verifier (edit here only)
├── testing/
│   ├── README.md
│   ├── verify_with_ca.sh
│   ├── verify_with_cca.sh
│   └── lib/verify_prompt.sh
├── sync_judges.sh          # syncs judges + run_judges.sh into tasks/*/tests/
├── run_codex_benchmark.sh
├── harbor.codex.yaml
├── harbor.codex.baseline.yaml
└── tasks/
    ├── calculator/
    ├── todo/
    ├── counter/
    ├── greeter/
    └── temperature/
```

Each task directory:

```text
tasks/<name>/
├── instruction.md          # one-sentence write prompt
├── artifact.txt
├── task.toml
├── environment/Dockerfile
├── solution/solve.sh
└── tests/
    ├── test.sh             # thin wrapper → synced run_judges.sh
    └── (runtime) judges/ + run_judges.sh from sync_judges.sh
```

## Judge reasoning in results

`verifier/run_judges.sh` (synced into each task) runs rewardkit per selected
skill, keeps `reward-<skill>-details.json` (including the judge’s `reasoning`
string), and writes an aggregate `reward-details.json` with per-skill `raw` +
`reasoning`. `run_codex_benchmark.sh` prints those lines in the post-run
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
`0.20.0`, Codex CLI `0.147.0`, and GPT-5.6 Luna at low reasoning effort.

## Clean Codex instance (required for skill benchmarks)

Codex skill trials must not reuse the host Codex home. Every Harbor Codex trial
already gets a fresh `CODEX_HOME=/tmp/codex-home`. This suite goes further:

- The pin in [`codex-version.txt`](codex-version.txt) is the Codex CLI version
  installed in the task image and verified by Harbor (`0.147.0` for now).
- [`harbor_agents/benchmark_codex.py`](harbor_agents/benchmark_codex.py) wipes
  `$HOME/.agents/skills`, `/etc/codex/skills`, and `$CODEX_HOME/skills`, then
  installs only the skills configured for that job (`--skill` /
  `harbor.codex.yaml`).
- Prefer [`./run_codex_benchmark.sh`](run_codex_benchmark.sh) or
  [`harbor.codex.yaml`](harbor.codex.yaml) over a bare `-a codex` invocation so
  the clean agent and version pin stay in force.

Reinstall or verify the pinned CLI inside the task environment:

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
./run_codex_benchmark.sh --install-only
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
./run_codex_benchmark.sh --negative --skills srp -k 5 -n 5
./run_codex_benchmark.sh --negative --skills commenting -k 5 -n 5
./run_codex_benchmark.sh --negative --skills srp,commenting --run-separately -k 5 -n 5
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

To measure how often the model satisfies single responsibility **without** the
programming skill, keep the same task + Luna-low setup and inject **no
skills**.

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
export JOBS="$(mktemp -d)" MOUNTS
./run_codex_benchmark.sh --baseline -k 5 -n 5
```

That uses [`harbor.codex.baseline.yaml`](harbor.codex.baseline.yaml)
(`skills: []`). The wrapper prints each trial’s reward, judge reasoning, the
downloaded `*.py` artifact(s), and a `pass_rate=…` summary. Compare that rate
to the with-skill run:

```bash
./run_codex_benchmark.sh --job-name codex-srp -k 5 -n 5
```

## Test the real skill with Codex

**Default model:** `openai/gpt-5.6-luna` at **low** reasoning effort
(`harbor.codex.yaml`). The LLM judge in `verifier/run_judges.sh` also uses low
effort.

Sign Codex into the ChatGPT subscription on the host:

```bash
codex login
codex login status
```

Then run five independent Luna-low attempts of **each** discovered task with the
clean, version-pinned BenchmarkCodex agent (25 trials total at `-k 5`):

```bash
export JOBS MOUNTS
./run_codex_benchmark.sh --job-name codex-srp -k 5 -n 5
```

`-k 5` schedules five attempts **per task**; `-n 5` runs up to five trials at
once. The wrapper defaults to the same `-k 5 -n 5` when you pass no Harbor
flags. After the job finishes it prints a console summary for every trial:
reward, per-skill judge answer/reasoning, and downloaded `/app/*.py`
artifacts, plus a `pass_rate=…` line.

Do not use a bare `-a codex` for these skill benchmarks: that path can leave
host/user skill directories untouched and does not default to the pinned CLI
version. The expected Codex reward is `1` when the written file uses
single-responsibility functions. Codex supports ChatGPT subscription sign-in;
see the official
[Codex authentication documentation](https://learn.chatgpt.com/docs/auth).
Never copy `~/.codex/auth.json` into this repository.

## Model and run parameters

Override the default Luna-low setup on the command line (or edit
`harbor.codex.yaml`). Useful Harbor flags:

| Flag | Meaning |
| --- | --- |
| `-m` / `--model` | Agent model id, e.g. `openai/gpt-5.6-luna` (repeatable) |
| `--ak reasoning_effort=…` | Codex reasoning: `low`, `medium`, or `high` |
| `--ak version=…` | Codex CLI pin (defaults from `codex-version.txt`) |
| `-k` / `--n-attempts` | Independent attempts per task (default example: `5`) |
| `-n` / `--n-concurrent` | How many trials run in parallel (default example: `5`) |
| `--skill` | Extra skill directory (job config already injects the programming skill) |

Examples:

```bash
# Default: five concurrent Luna-low trials
./run_codex_benchmark.sh --job-name codex-srp -k 5 -n 5

# Same model, higher reasoning, still five trials
./run_codex_benchmark.sh --job-name codex-srp-high \
  -k 5 -n 5 --ak reasoning_effort=high

# Different Codex model, one attempt
./run_codex_benchmark.sh --job-name codex-other \
  -k 1 -n 1 -m openai/gpt-5.4 --ak reasoning_effort=medium
```

CLI `-m` / `--ak` values override the matching fields in `harbor.codex.yaml` for
that job. Keep ChatGPT subscription auth via `CODEX_FORCE_AUTH_JSON=1` and the
`auth.json` mount unless you intentionally switch to API-key auth.

## Add the next evaluation

Keep each new coding task equally small:

1. copy an existing `tasks/<name>` directory;
2. write a one-sentence product prompt in `instruction.md`;
3. put the artifact path in `artifact.txt` (e.g. `/app/foo.py`);
4. make `solution/solve.sh` write a reference implementation that can pass the
   selected judges;
5. add new skills only as `../prompts/programming-skills/<skill>/SKILL.md` plus
   `judges/<skill>/prompt.md` (+ `judge.toml`); edit the shared verifier at
   `verifier/run_judges.sh` (not the five thin `tasks/*/tests/test.sh` wrappers);
6. run `./sync_judges.sh` (runtime), then oracle / `nop` / one real model trial.

`./run_codex_benchmark.sh` auto-discovers every `tasks/*/` directory and every
selected skill. Prefer the wrapper over bare Harbor YAML.

Harbor records the complete jobs under the temporary `$JOBS` directory, so the
repository stays free of model transcripts, credentials, and generated output.
