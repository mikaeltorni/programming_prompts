# Harbor evaluation

There is one small evaluation for the current programming skill:
`tasks/calculator-srp`.

The task starts with a working calculator whose parsing, arithmetic, and result
formatting all live in one `run_calculator` function. The agent is asked to make
the file follow the programming skill (single-responsibility functions/methods).
A Codex LLM judge answers one binary question: does every function in
`calculator.py` follow single responsibility?

Edit the judge wording here (this is the verifier prompt surface):

- [`tasks/calculator-srp/tests/srp.toml`](tasks/calculator-srp/tests/srp.toml)
  — criterion text plus `prompt_template`
- [`tasks/calculator-srp/tests/judge-prompt.md`](tasks/calculator-srp/tests/judge-prompt.md)
  — system prompt template (must keep the `{criteria}` placeholder)

The judge scores structure only. It must ignore comment language and must not
ask about Finnish or any other natural language. The expected reward is `1`
when functions are split by responsibility and `0` when the monolithic starting
function is left in place.

## Task files

```text
tasks/calculator-srp/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   └── calculator.py
├── solution/
│   └── solve.sh
└── tests/
    ├── srp.toml          # edit criterion + prompt_template here
    ├── judge-prompt.md   # edit judge system prompt here
    └── test.sh
```

- `environment/calculator.py` is the multi-responsibility starting file.
- `solution/solve.sh` is Harbor's known-good oracle solution.
- `tests/srp.toml` is the LLM evaluation criterion (edit this when the
  pass/fail question should change).
- `tests/judge-prompt.md` is the judge system prompt template (edit this to make
  the verifier stricter or clearer; keep `{criteria}`).
- `tests/test.sh` runs Reward Kit and writes the judge's reward.

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

TASK="$PWD/tasks/calculator-srp"
SKILL="$PWD/../prompts/programming-skill"
JOBS="$(mktemp -d)"
MOUNTS="$(python3 -c 'import json, pathlib; print(json.dumps([{"type": "bind", "source": str(pathlib.Path.home() / ".codex" / "auth.json"), "target": "/root/.codex/auth.json", "read_only": True}]))')"
```

The read-only mount gives the LLM verifier access to the existing ChatGPT
subscription login. It does not copy the credential into this repository or
the saved Harbor job.

## Positive test

The oracle refactors the monolithic calculator into single-responsibility
helpers. This must produce reward `1`:

```bash
harbor run -p "$TASK" -a oracle --mounts "$MOUNTS" \
  -o "$JOBS" --job-name positive-oracle
find "$JOBS/positive-oracle" -name reward.json -print -exec cat {} \;
```

## Negative test (verifier sanity)

Harbor's `nop` agent deliberately changes nothing. The calculator still works,
but it remains one multi-responsibility function, so this must produce reward
`0`:

```bash
harbor run -p "$TASK" -a nop --mounts "$MOUNTS" \
  -o "$JOBS" --job-name negative-monolith
find "$JOBS/negative-monolith" -name reward.json -print -exec cat {} \;
```

This proves the verifier rejects the starting structure. It is **not** a model
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
resulting `calculator.py` source, and a `pass_rate=X/5 (Y%)` summary. Compare
that rate to the with-skill run:

```bash
./run_codex_benchmark.sh --job-name codex-srp -k 5 -n 5
```

## Test the real skill with Codex

**Default model:** `openai/gpt-5.6-luna` at **low** reasoning effort
(`harbor.codex.yaml`). The LLM judge in `tests/test.sh` also uses low effort.

Sign Codex into the ChatGPT subscription on the host:

```bash
codex login
codex login status
```

Then run five independent Luna-low trials of the clean, version-pinned
BenchmarkCodex agent (only the programming skill from `harbor.codex.yaml`):

```bash
export JOBS MOUNTS
./run_codex_benchmark.sh --job-name codex-srp -k 5 -n 5
```

`-k 5` schedules five attempts of the task; `-n 5` runs up to five of them at
once. The wrapper defaults to the same `-k 5 -n 5` when you pass no Harbor
flags. After the job finishes it prints a console summary for every trial:
reward, judge answer/reasoning, and the downloaded `/app/calculator.py`
artifact, plus a `pass_rate=…` line.

Do not use a bare `-a codex` for these skill benchmarks: that path can leave
host/user skill directories untouched and does not default to the pinned CLI
version. The expected Codex reward is `1` when the file is refactored into
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

Keep each new rule equally small:

1. copy `tasks/calculator-srp` to a clearly named task directory;
2. put the smallest useful starting file in `environment/`;
3. describe one behavior in `instruction.md`;
4. make `solution/solve.sh` demonstrate a passing answer;
5. express the check as one clear binary criterion when practical;
6. run the oracle, the negative `nop` case, and one real model before keeping
   the task.

Harbor records the complete jobs under the temporary `$JOBS` directory, so the
repository stays free of model transcripts, credentials, and generated output.
