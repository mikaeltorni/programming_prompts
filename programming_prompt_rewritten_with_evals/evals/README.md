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
`0.20.0`, and GPT-5.6 Luna at low reasoning effort.

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

Completely close and reopen the terminal or IDE after adding your user to the
`docker` group. In VSC/Cursor etc, restart the whole application, not only the terminal
panel. Then verify the installation:

```bash
docker version
docker compose version
docker run --rm hello-world
```

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

Run the remaining commands from this `evals` directory:

```bash
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
find "$JOBS/positive-oracle" -name reward.json -print -exec sed -n '1p' {} \;
```

## Negative test

Harbor's `nop` agent deliberately changes nothing. The calculator still works,
but its comments remain English, so this must produce reward `0`:

```bash
harbor run -p "$TASK" -a nop --mounts "$MOUNTS" \
  -o "$JOBS" --job-name negative-english
find "$JOBS/negative-english" -name reward.json -print -exec sed -n '1p' {} \;
```

This negative run proves that the verifier rejects English comments rather than
merely checking that the calculator executes.

## Test the real skill with Codex

Sign Codex into the ChatGPT subscription on the host:

```bash
codex login
codex login status
```

Then tell Harbor to use that login and inject the skill:

```bash
CODEX_FORCE_AUTH_JSON=1 harbor run \
  -p "$TASK" \
  -a codex \
  -m openai/gpt-5.6-luna \
  --ak reasoning_effort=low \
  --skill "$SKILL" \
  --mounts "$MOUNTS" \
  -o "$JOBS" \
  --job-name codex-finnish

find "$JOBS/codex-finnish" -name reward.json -print -exec sed -n '1p' {} \;
```

The evaluated agent and the LLM judge both use `gpt-5.6-luna` at low reasoning
effort. The expected Codex reward is `1`. Codex supports ChatGPT subscription
sign-in; see the official
[Codex authentication documentation](https://learn.chatgpt.com/docs/auth).
Never copy `~/.codex/auth.json` into this repository.

## Verified results

This task was run successfully on 2026-08-09 with Harbor `0.20.0`, Docker
`29.5.3`, and Codex `gpt-5.6-luna` at low reasoning effort using ChatGPT
subscription authentication:

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
