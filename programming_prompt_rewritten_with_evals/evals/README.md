# Harbor evaluation

There is one small evaluation for the current programming skill:
`tasks/calculator-comments`.

The task starts with a working calculator whose four comments are in English.
The agent is asked only to make the file follow the programming skill. A Codex
LLM judge then answers one binary question: ignoring code and string literals,
are all four `#` comment lines in `calculator.py` written in Finnish?

There is no Finnish vocabulary list or other language-detection heuristic. The
expected reward is `1` for a Finnish rewrite and `0` when the English comments
are left unchanged.

## Task files

```text
tasks/calculator-comments/
├── instruction.md
├── task.toml
├── environment/
│   ├── Dockerfile
│   └── calculator.py
├── solution/
│   └── solve.sh
└── tests/
    ├── finnish-comments.toml
    └── test.sh
```

- `environment/calculator.py` is the English starting file.
- `solution/solve.sh` is Harbor's known-good oracle solution.
- `tests/finnish-comments.toml` contains the single LLM evaluation question.
- `tests/test.sh` runs Reward Kit and writes the judge's reward.

## Tested platform

The complete oracle, negative, and Codex runs were tested end to end on Ubuntu
24.04.4 LTS (Noble). The verified setup used Docker Engine `29.5.3`, Harbor
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

TASK="$PWD/tasks/calculator-comments"
SKILL="$PWD/../prompts/programming-skill"
JOBS="$(mktemp -d)"
MOUNTS="$(python3 -c 'import json, pathlib; print(json.dumps([{"type": "bind", "source": str(pathlib.Path.home() / ".codex" / "auth.json"), "target": "/root/.codex/auth.json", "read_only": True}]))')"
```

The read-only mount gives the LLM verifier access to the existing ChatGPT
subscription login. It does not copy the credential into this repository or
the saved Harbor job.

## Positive test

The oracle replaces the English comments with Finnish comments. This must
produce reward `1`:

```bash
harbor run -p "$TASK" -a oracle --mounts "$MOUNTS" \
  -o "$JOBS" --job-name positive-oracle
find "$JOBS/positive-oracle" -name reward.json -print -exec cat {} \;
```

## Negative test

Harbor's `nop` agent deliberately changes nothing. The calculator still works,
but its comments remain English, so this must produce reward `0`:

```bash
harbor run -p "$TASK" -a nop --mounts "$MOUNTS" \
  -o "$JOBS" --job-name negative-english
find "$JOBS/negative-english" -name reward.json -print -exec cat {} \;
```

This negative run proves that the verifier rejects English comments rather than
merely checking that the calculator executes.

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
./run_codex_benchmark.sh --job-name codex-finnish -k 5 -n 5
```

`-k 5` schedules five attempts of the task; `-n 5` runs up to five of them at
once. The wrapper defaults to the same `-k 5 -n 5` when you pass no Harbor
flags.

Equivalent explicit Harbor invocation:

```bash
PYTHONPATH="$PWD" CODEX_FORCE_AUTH_JSON=1 harbor run \
  -c "$PWD/harbor.codex.yaml" \
  --ak "version=$(tr -d '[:space:]' <codex-version.txt)" \
  --mounts "$MOUNTS" \
  -o "$JOBS" \
  --job-name codex-finnish \
  -k 5 \
  -n 5
```

Do not use a bare `-a codex` for these skill benchmarks: that path can leave
host/user skill directories untouched and does not default to the pinned CLI
version. The expected Codex reward is `1` on each successful Finnish rewrite.
Codex supports ChatGPT subscription sign-in; see the official
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
./run_codex_benchmark.sh --job-name codex-finnish -k 5 -n 5

# Same model, higher reasoning, still five trials
./run_codex_benchmark.sh --job-name codex-finnish-high \
  -k 5 -n 5 --ak reasoning_effort=high

# Different Codex model, one attempt
./run_codex_benchmark.sh --job-name codex-other \
  -k 1 -n 1 -m openai/gpt-5.4 --ak reasoning_effort=medium

# Explicit harbor run with another model
PYTHONPATH="$PWD" CODEX_FORCE_AUTH_JSON=1 harbor run \
  -c "$PWD/harbor.codex.yaml" \
  -m openai/o3 \
  --ak reasoning_effort=medium \
  --ak "version=$(tr -d '[:space:]' <codex-version.txt)" \
  --mounts "$MOUNTS" \
  -o "$JOBS" \
  --job-name codex-o3 \
  -k 1 -n 1
```

CLI `-m` / `--ak` values override the matching fields in `harbor.codex.yaml` for
that job. Keep ChatGPT subscription auth via `CODEX_FORCE_AUTH_JSON=1` and the
`auth.json` mount unless you intentionally switch to API-key auth.

## Verified results

This task was run successfully on 2026-08-09 with Harbor `0.20.0`, Docker
`29.5.3`, Codex CLI `0.147.0`, and model `gpt-5.6-luna` at low reasoning effort
using ChatGPT subscription authentication:

| Run | Expected | Observed |
| --- | ---: | ---: |
| Oracle positive | `1` | `1` |
| English `nop` negative | `0` | `0` |
| Codex with the programming skill | `1` | `1` |

All three Harbor jobs completed without exceptions.

## Add the next evaluation

Keep each new rule equally small:

1. copy `tasks/calculator-comments` to a clearly named task directory;
2. put the smallest useful starting file in `environment/`;
3. describe one behavior in `instruction.md`;
4. make `solution/solve.sh` demonstrate a passing answer;
5. express the check as one clear binary criterion when practical;
6. run the oracle, the negative `nop` case, and one real model before keeping
   the task.

Harbor records the complete jobs under the temporary `$JOBS` directory, so the
repository stays free of model transcripts, credentials, and generated output.
