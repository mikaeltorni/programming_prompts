# Harbor evaluation

Five small write-from-scratch tasks measure whether Codex, Claude Code, and/or
Grok follow selected programming skills while implementing tiny Python programs:

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
- [`../prompts/programming-skills/logging/SKILL.md`](../prompts/programming-skills/logging/SKILL.md)
- [`../prompts/programming-skills/logging-vague/SKILL.md`](../prompts/programming-skills/logging-vague/SKILL.md)
  (control — vague one-liner; scored by the logging judge)
- [`../prompts/programming-skills/worktree/SKILL.md`](../prompts/programming-skills/worktree/SKILL.md)
- [`judges/srp/prompt.md`](judges/srp/prompt.md)
- [`judges/commenting/prompt.md`](judges/commenting/prompt.md)
- [`judges/logging/prompt.md`](judges/logging/prompt.md)
- [`judges/worktree/judge.toml`](judges/worktree/judge.toml)
  (programmatic git-layout checker; no LLM prompt)

Coding tasks — one markdown file each under
[`coding-prompts/`](coding-prompts/). Harbor task trees are **generated** under
[`.generated/tasks/`](.generated/tasks/) by [`sync_tasks.sh`](sync_tasks.sh)
(gitignored / hidden). Judge copies
under `.generated/tasks/*/tests/judges/` are also runtime-only.

## CLI parameters

| Flag | Meaning |
| --- | --- |
| `harness=codex` / `--harness cc` / `harness=grok` | Agent harness: `codex`, `cc` (Claude Code), `grok`, `both`, `all`, or a comma list |
| *(omit harness)* | Runs **Codex and Claude Code** (not Grok) |
| `evalAgent=cc,codex,grok` / `--evalAgent cc` / `--eval-agent=all` | LLM **judge** harness(es). Same aliases/groups as `harness=`. Omit to use the **same** harness as the coding agent |
| `evalAgentModel=claude-opus-5` / `--evalAgentModel …` / `--eval-agent-model=…` | Judge model id (same idea as `-m` / `--model`). One value for every eval agent, or one per agent |
| `evalAgentReasoningEffort=low` / `--evalAgentReasoningEffort high` | Judge effort: `low`, `medium`, or `high` (same idea as `--ak reasoning_effort=`). One value or one per agent |
| `--skills srp,commenting` | Which skills to inject (default: all non-`*-vague`) |
| `--skills=srp` / `-skills=srp` | Same, equals form |
| `--skills srp,logging-vague` | Vague control skill; scored by `judges/logging/` |
| `--tasks todo,calculator` | Which coding prompts to run (default: all) |
| `--tasks=greeter` / `task=todo,counter` | Same, equals / bare forms |
| `--run-separately` / `--runSeparately` | One Harbor job per skill (costlier) |
| `--baseline` | No skills injected; selected judges still score |
| `--install-only` | Reinstall/verify newest stable CLI(s) in the task image (no LLM) |
| `--no-pin-refresh` | Skip registry lookup; use committed `*-version.txt` pins |
| `-k` / `-n` / `-m` / `--ak` | Passed through to Harbor |

Harness aliases: `cc`, `claude`, `claude-code`, `claudecode` → Claude Code;
`codex`, `openai`, `gpt` → Codex; `grok`, `xai`, `grok-build`, `grok-code` →
Grok CLI; `both` / empty → Codex + Claude Code; `all` → Codex + Claude Code +
Grok. `evalAgent` uses the same aliases (`evalAgent=both`, `evalAgent=all`,
`evalAgent=cc,codex`). Empty `evalAgent` is **not** `both`: each job’s judge
matches that job’s coding harness (`harness=cc` → Claude Code judge).

Without `--run-separately`, all selected skills are installed in **one** agent
session and **each** matching judge scores the same written code. With
`--run-separately`, each skill gets its own prompt instance + its own judge
(more subscription usage). Each Harbor job gets an **isolated** copy of the
selected tasks under `$RUN_DIR/harbor/task-trees/<job>/` so `/tests/judges` cannot be
clobbered by the next skill job or a concurrent benchmark sharing
`evals/.generated/tasks/`.

Trial math: default `-k 5` is **5 attempts per selected coding task**. With all
5 tasks that is **25 trials per skill-job per harness**. `--run-separately`
with 2 skills ≈ **2×** that. Omit harness (both) ≈ **2×** again — e.g.
`harness` omitted + `--run-separately` + 2 skills + 5 tasks + `-k 5` ≈
**100 trials**. `evalAgent=cc,codex` does **not** multiply trials; it reruns
the LLM judge on each trial (2× verifier time/cost). Programmatic judges
(worktree) still run once. Defaults: Codex `openai/gpt-5.6-luna` @ low; Claude
Code `claude-opus-5` @ low (`--effort`); Grok `grok-4.6` @ low
(`--reasoning-effort`). Judge defaults match those models at **low** effort
unless `evalAgentModel` / `evalAgentReasoningEffort` override them.

After each job the wrapper prints trials, then categorized rollups: **by
harness**, **by eval agent**, **harness × eval agent**, **harness × skill**,
**harness × task**, **harness × task × skill**, plus a harness comparison
table when both ran, and a GRAND TOTAL. Per-eval-agent answers show as
`judge[srp/cc]` / `judge[srp/codex]`. A skill (and the trial) passes only
when **every** selected eval agent says yes.

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
│   ├── commenting/
│   │   ├── prompt.md
│   │   └── judge.toml
│   ├── logging/
│   │   ├── prompt.md
│   │   └── judge.toml
│   └── worktree/
│       └── judge.toml          # programmatic
├── verifier/
│   ├── README.md
│   ├── run_judges.sh
│   ├── check_worktree.py       # worktree layout judge + --self-test
│   ├── run_llm_judge.py        # Codex / Claude Code / Grok eval agent
│   ├── run_grok_judge.py       # shim → run_llm_judge.py --agent grok
│   └── llm_judge/              # shared pin-and-retry helpers for every eval agent
├── harbor_agents/          # BenchmarkCodex / Claude / Grok + version refresh
├── testing/
├── sync_tasks.sh           # coding-prompts → .generated/tasks/
├── sync_judges.sh          # judges + verifier → .generated/tasks/*/tests/
├── run_benchmark.sh        # Codex + Claude Code + Grok runner
├── run_codex_benchmark.sh  # thin shim → run_benchmark.sh harness=codex
├── run_grok_benchmark.sh   # thin shim → run_benchmark.sh harness=grok
├── archive_benchmark_run.py
├── docker_networks.py      # prune leftover Harbor nets + cross-process IPAM slots
├── launch_benchmarks.sh    # interactive preset menu; normal windows on this monitor
├── launch_benchmarks.py
├── presets/                # git-tracked launch presets (positive/baseline matrices)
├── runs/                   # timestamped archives; RESULTS.txt is the table index
├── codex-version.txt
├── claude-version.txt
├── grok-version.txt
└── .generated/tasks/       # GENERATED (gitignored, hidden) — do not edit
```

After every non-install run the wrapper writes a durable archive under
[`runs/`](runs/) and prints `written to: <path>`. [`runs/RESULTS.txt`](runs/RESULTS.txt)
is an aligned table (newest row at the top, under the header): mode, harness,
judge, skills, tasks, k/n, separately, trial/scored/pass counts, and per-skill
plus per-task rates. Folder names start with
`YYYY-MM-DD_HHMMSS_<pid>` so they sort by time in the explorer, and encode
harness, **evalagent** (`inherit` or `cc+codex`), mode, skills,
`--run-separately`, tasks, and `-k`/`-n`. Harbor job
dirs live in that same archive (`<run>/harbor/`, not `/tmp`) and use the same
stamp (`codex-skills__YYYY-MM-DD_HHMMSS_<pid>`). Each trial’s simulated host
layout is copied to `<run>/Projects/<trial>/` (`app/` clone + `.worktrees/`).

`sync_tasks.sh` builds each Harbor task directory from
`coding-prompts/<name>.md` + `oracles/<name>.py` + `task-template/`.

## Judge reasoning in results

`verifier/run_judges.sh` (synced into each task) runs
[`verifier/run_llm_judge.py`](verifier/run_llm_judge.py) once per selected
skill and eval agent (Codex, Claude Code, or Grok). Codex and Claude Code
still go through pinned harbor-rewardkit; Grok uses the CLI because
rewardkit 0.1.7 has no grok backend. Every agent gets the same workspace
`*.py` listing and one retry on skip-inspect / invented paths. It keeps
`reward-<skill>-<evalAgent>-details.json` plus an aggregate
`reward-<skill>.json` that passes only if every eval agent passed.
`run_benchmark.sh` prints those lines in the post-run console summary:

```text
  judge[srp] answer: yes
  judge[srp] reason: cc=yes; codex=yes
  judge[srp/cc] answer: yes
  judge[srp/cc] reason: …
  judge[srp/codex] answer: yes
  judge[srp/codex] reason: …
```

## Verify finished run archives

After positive and baseline runs, pass the two run `harbor/` dirs (or the
pretty `jobs/` trees) to the scripts under [`testing/`](testing/):

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
`0.20.0`, Codex CLI `0.149.0`, Claude Code `2.1.241`, Grok CLI `1.0.5`,
GPT-5.6 Luna at low reasoning effort, Claude Opus 5 at low effort, and
Grok 4.6 at low effort. Each `./run_benchmark.sh` invocation looks up those
CLI versions again (npm `latest`, Grok `stable` channel) so a new instance
installs whatever is newest at start time. Pass `--no-pin-refresh` to freeze
the committed pin files. The lookup is a few HTTP GETs and does not call an
LLM.

## Clean agent instances (required for skill benchmarks)

Skill trials must not reuse host skill trees.

### Codex (`harness=codex`)

Every Harbor Codex trial already gets a fresh `CODEX_HOME=/tmp/codex-home`. This
suite goes further:

- Pin fallback: [`codex-version.txt`](codex-version.txt) (`0.149.0`).
  Instance start prefers npm `@openai/codex` `latest`.
- [`harbor_agents/benchmark_codex.py`](harbor_agents/benchmark_codex.py) wipes
  `$HOME/.agents/skills`, `/etc/codex/skills`, and `$CODEX_HOME/skills`, then
  installs only the skills configured for that job.
- Auth: host `~/.codex/auth.json` bind-mount + `CODEX_FORCE_AUTH_JSON=1`.

### Claude Code (`harness=cc`)

- Pin fallback: [`claude-version.txt`](claude-version.txt) (`2.1.241`).
  Instance start prefers npm `@anthropic-ai/claude-code` `latest`.
- [`harbor_agents/benchmark_claude_code.py`](harbor_agents/benchmark_claude_code.py)
  wipes `$HOME/.claude/skills` and `$CLAUDE_CONFIG_DIR/skills`, then installs
  only the job’s skills (Harbor would otherwise copy host `~/.claude/skills`).
- Auth (agent): reads `~/.claude/.credentials.json` → `CLAUDE_CODE_OAUTH_TOKEN`
  with `CLAUDE_FORCE_OAUTH=true` (token never printed). Also bind-mounts the
  credentials file into the trial.
- Auth (verifier): **default `evalAgent` inherits the coding harness**, so
  `harness=cc` grades with Claude Code and needs Claude OAuth — not Codex.
  Codex `auth.json` is still mounted so `evalAgent=codex` (or a mix) can run.
  The verifier copies credentials into a writable `CLAUDE_CONFIG_DIR` (the
  trial mount is read-only) and runs `claude -p` with `IS_SANDBOX=1` plus
  `--permission-mode bypassPermissions`, matching Harbor's coding agent.
  Without the matching judge auth you get a verifier error such as
  `Claude Code eval agent needs CLAUDE_CODE_OAUTH_TOKEN`.
- Do not pass `…=1` for `*AUTH*` / `*OAUTH*` / `*TOKEN*` flags via Harbor
  `--ae`: Harbor scrubs those values from trial outputs, and the literal `1`
  rewrites every `reward: 1.0` into broken `[REDACTED].0` JSON.

### Grok CLI (`harness=grok`)

- Pin fallback: [`grok-version.txt`](grok-version.txt) (`1.0.5`).
  Instance start prefers the Grok `https://x.ai/cli/stable` channel pointer.
- Model: `grok-4.6` @ **low** reasoning (`--reasoning-effort low`). Harbor's
  stock Grok agent defaults to high; this wrapper pins low unless you pass
  `--ak reasoning_effort=high`.
- [`harbor_agents/benchmark_grok.py`](harbor_agents/benchmark_grok.py) wipes
  `$HOME/.grok/skills` and `$HOME/.grok/installed-plugins`, then installs only
  the job’s skills (host SuperGrok marketplace skills never enter the trial).
- Auth (agent): SuperGrok OAuth from `~/.grok/auth.json` (the `key` field) is
  forwarded as `XAI_API_KEY` and the file is bind-mounted at
  `/root/.grok/auth.json`. Or export `XAI_API_KEY` yourself (xAI API key).
  The runner never prints the key.
- Auth (verifier): **default `evalAgent` inherits Grok**, so SuperGrok /
  `XAI_API_KEY` must reach the verifier. Codex `auth.json` is still mounted
  for `evalAgent=codex`. [`verifier/run_llm_judge.py`](verifier/run_llm_judge.py)
  runs every eval agent. Grok shells out to the CLI (`--json-schema`); Codex
  and Claude Code use pinned harbor-rewardkit. Shared helpers in
  [`verifier/llm_judge/`](verifier/llm_judge/) list and inline the real
  `*.py` files under `/Projects/app` so no agent can score a hallucinated
  `app.py`. A no whose reasoning admits non-inspection or cites a `.py` path
  that is not in that listing is retried once (still inside the judge timeout).
- Sign in once on the host: `grok login --oauth` (SuperGrok / Grok.com).
  Confirm with `test -f ~/.grok/auth.json && grok --version`.

Prefer [`./run_benchmark.sh`](run_benchmark.sh) over bare `-a grok-build`
so the clean agent, version pin, and low reasoning stay in force.

Reinstall or verify pinned CLIs inside the task environment:

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
./run_benchmark.sh --install-only                  # Codex + Claude Code (newest CLIs)
./run_benchmark.sh --install-only harness=codex
./run_benchmark.sh --install-only harness=cc
./run_benchmark.sh --install-only harness=grok
./run_benchmark.sh --no-pin-refresh --install-only # committed pins only
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

Docker's built-in IPAM gives each user-defined network a whole `/16` (~30
networks on the host). Harbor creates one network **per trial**, so twelve
terminals at `-n 5` exhaust the pool (`all predefined address pools have been
fully subnetted`) and crash in `_prepare`. [`docker_networks.py`](docker_networks.py)
prunes leftover empty Harbor networks and makes concurrent `./run_benchmark.sh`
processes **wait for a slot** instead of stampeding. Optional: give Docker
thousands of `/24` trial networks (254 hosts each — enough for a Harbor
compose project) so many jobs can run at full `-n` in parallel. Merge these
pools into `/etc/docker/daemon.json` (keep any other keys) and restart Docker
when no Harbor jobs are running:

```bash
python3 docker_networks.py recommended-daemon-json
```

```json
{
  "default-address-pools": [
    {"base": "172.18.0.0/16", "size": 24},
    {"base": "172.19.0.0/16", "size": 24},
    {"base": "172.20.0.0/14", "size": 24},
    {"base": "172.24.0.0/13", "size": 24},
    {"base": "192.168.0.0/16", "size": 24}
  ]
}
```

Do not overlap `172.17.0.0/16` (the default `bridge`). Prove the helper without
Harbor:

```bash
python3 docker_networks.py self-test
```

```bash
python3 docker_networks.py prune
```

```bash
python3 docker_networks.py capacity
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

TASK="$PWD/.generated/tasks/calculator"
SKILL="$PWD/../prompts/programming-skills/srp"
JOBS="$PWD/runs/manual-$(date +%Y-%m-%d_%H%M%S)_$$"
mkdir -p "$JOBS"
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

## Verifier sanity (`nop`)

Harbor's `nop` agent deliberately changes nothing. The workspace stays empty, so
this must produce reward `0`:

```bash
harbor run -p "$TASK" -a nop --mounts "$MOUNTS" \
  -o "$JOBS" --job-name nop-empty
find "$JOBS/nop-empty" -name reward.json -print -exec cat {} \;
```

This proves the verifier rejects missing/non-SRP code. It is **not** a model
baseline.

## Baseline / no-skill (model pass rate without the prompt)

To measure how often the model satisfies the skill **without** injecting it,
keep the same tasks and inject **no skills**.

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
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

## Logging skill (plain `print`, pair with SRP)

The logging skill asks for plain `print(...)` of parameters at function entry
and of the return value just before exit — no `logging` module, no log files.
Always pair it with **`srp`** in the same session (omit `--run-separately`) so
the agent writes several helpers; a single monolithic function does not give
the logging judge enough entry/exit sites.

`logging-vague` injects only “Use logging.” and has **no** judge of its own —
the runner scores it with `judges/logging/`.

Recommended six-command smoke set (`-k 2 -n 2` keeps cost down while
debugging). Each `./run_benchmark.sh` line is its own fenced block so it can
be pasted into a separate terminal (see repo `AGENTS.md`):

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

```bash
./run_benchmark.sh harness=codex --baseline --skills srp,logging -k 2 -n 2
```

```bash
./run_benchmark.sh harness=cc --baseline --skills srp,logging -k 2 -n 2
```

```bash
./run_benchmark.sh harness=codex --skills srp,logging -k 2 -n 2
```

```bash
./run_benchmark.sh harness=cc --skills srp,logging -k 2 -n 2
```

```bash
./run_benchmark.sh harness=codex --skills srp,logging-vague -k 2 -n 2
```

```bash
./run_benchmark.sh harness=cc --skills srp,logging-vague -k 2 -n 2
```

## Worktree skill (sibling `/Projects/.worktrees/<project>/`, pair with SRP)

Each trial image starts `/Projects/app` as a git repo with **one empty initial
commit** (`/app` is a symlink to that clone). The worktree skill requires a
feature-branch worktree at `/Projects/.worktrees/app/<dir>/`. Commit each
finished part there, merge back, **never push**. Scoring is **programmatic**
(`verifier/check_worktree.py`), not an LLM judge.

After a run, open `evals/runs/<stamp>/Projects/<trial>/` — `app/` is the cloned
initial state and `.worktrees/app/<dir>/` holds the work.

Pair with **`srp`** so there are several helpers to commit one-by-one. Prove the
checker against every pass/fail layout before a Harbor run:

```bash
python3 verifier/check_worktree.py --self-test
```

```bash
python3 archive_benchmark_run.py self-test
```

```bash
python3 docker_networks.py self-test
```

```bash
python3 launch_benchmarks.py --self-test
```

Rebuild the newest-first table index (also happens automatically at the
end of each `./run_benchmark.sh`):

```bash
python3 archive_benchmark_run.py results-index --runs-root runs
```

Recommended smoke set (each `./run_benchmark.sh` in its own terminal):

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

```bash
./run_benchmark.sh harness=codex --baseline --skills srp,worktree -k 2 -n 2
```

```bash
./run_benchmark.sh harness=cc --baseline --skills srp,worktree -k 2 -n 2
```

```bash
./run_benchmark.sh harness=codex --skills srp,worktree -k 2 -n 2
```

```bash
./run_benchmark.sh harness=cc --skills srp,worktree -k 2 -n 2
```

Grok (SuperGrok quota; `-k 5 -n 5` ≈ 25 trials, ~2.5× the k2n2 smoke):

```bash
./run_benchmark.sh harness=grok --baseline --skills srp,worktree -k 5 -n 5
```

```bash
./run_benchmark.sh harness=grok --skills srp,worktree -k 5 -n 5
```

## Eval agent (LLM judge harness)

The **coding** agent is `harness=`. The **judge** is `evalAgent=`. They are
independent. Omit `evalAgent` and the judge is the same CLI as that job’s
coding harness (`harness=cc` → Claude Code judge, `harness=grok` → Grok
judge). Pass a comma list to score the same workspace two or three times; the
skill (and trial) passes only when every eval agent agrees.

`evalAgentModel` and `evalAgentReasoningEffort` use the same equals / dashed
forms as `harness=` and the same meaning as `-m` / `--ak reasoning_effort=`.
One value applies to every eval agent; N values must match N agents.

Checked-in `judges/*/judge.toml` still says `judge = "codex"` — that is the
rewardkit default. The wrapper overwrites it at runtime via Harbor `--ve`
(`EVAL_AGENTS`, `EVAL_AGENT_MODELS`, `EVAL_AGENT_REASONING_EFFORT`).

Auth for the judge is the matching CLI: Codex `~/.codex/auth.json`, Claude
`CLAUDE_CODE_OAUTH_TOKEN`, Grok `XAI_API_KEY` / `~/.grok/auth.json`. Mixing
eval agents requires every listed judge’s credentials.

Cheap smoke (`calculator` + `srp`, `-k 1 -n 1`). Shared setup, then **each**
`./run_benchmark.sh` in its own terminal (see repo `AGENTS.md`):

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

Baseline, inherit judge (Codex codes and Codex grades):

```bash
./run_benchmark.sh harness=codex --baseline --skills srp --tasks calculator -k 1 -n 1
```

Positive, inherit judge:

```bash
./run_benchmark.sh harness=codex --skills srp --tasks calculator -k 1 -n 1
```

Baseline, Claude Code grades Codex output:

```bash
./run_benchmark.sh harness=codex evalAgent=cc --baseline --skills srp --tasks calculator -k 1 -n 1
```

Positive, Claude Code grades Codex output:

```bash
./run_benchmark.sh harness=codex evalAgent=cc --skills srp --tasks calculator -k 1 -n 1
```

Baseline, checked twice (Claude Code + Codex judges):

```bash
./run_benchmark.sh harness=codex evalAgent=cc,codex --baseline --skills srp --tasks calculator -k 1 -n 1
```

Positive, checked twice:

```bash
./run_benchmark.sh harness=codex evalAgent=cc,codex --skills srp --tasks calculator -k 1 -n 1
```

Same twice-check with explicit judge model/effort (format matches `-m` /
`--ak reasoning_effort=`):

```bash
./run_benchmark.sh harness=codex evalAgent=cc,codex \
  evalAgentModel=claude-opus-5,gpt-5.6-luna \
  evalAgentReasoningEffort=low,low \
  --skills srp --tasks calculator -k 1 -n 1
```

Grok as both coder and judge (inherit):

```bash
./run_benchmark.sh harness=grok --baseline --skills srp --tasks calculator -k 1 -n 1
```

```bash
./run_benchmark.sh harness=grok --skills srp --tasks calculator -k 1 -n 1
```

Expect baseline pass rate well below positive for `srp`. Dual eval agents
print `judge[srp/cc]` and `judge[srp/codex]`; the trial fails if they
disagree. Bump `-k`/`-n` once the smoke looks right.

## Test the real skill (Codex, Claude Code, and/or Grok)

**Defaults:** Codex `openai/gpt-5.6-luna` @ **low**; Claude Code `claude-opus-5`
@ **low**; Grok `grok-4.6` @ **low**. The LLM judge uses the same low effort
unless `evalAgentReasoningEffort` overrides it.

Sign in on the host:

```bash
codex login && codex login status
# Claude Code subscription token lives in ~/.claude/.credentials.json
# (Claude CLI `claude setup-token` / normal login on the host).
# Grok SuperGrok: grok login --oauth  (writes ~/.grok/auth.json).
# Optional: export XAI_API_KEY=... to override the SuperGrok key.
```

Then run (examples), or use the **preset launcher** so each job opens in its
own window **on the same monitor as this terminal**:

```bash
cd ~/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

```bash
./launch_benchmarks.sh
```

The menu prints ``[N coding × judges=…]`` so a two-harness slice shows both
judges on the same coding runs (not one job per judge). Each terminal is
**one coding harness**; every included harness judges that same tree
(`evalAgent=codex,cc,grok` on a 3-way job). If you drop grok because of a
rate limit, grok is not a coder and not a judge.

Shipped files under [`presets/`](presets/):

| Preset | Coding runs | Judges |
| --- | ---: | --- |
| `positive-all-harnesses-all-judges` / `baseline-all-harnesses-all-judges` | 3 | codex,cc,grok |
| `positive-codex-cc` / `baseline-codex-cc` (no grok) | 2 | codex,cc |
| `positive-codex-grok` / `baseline-codex-grok` (no cc) | 2 | codex,grok |
| `positive-cc-grok` / `baseline-cc-grok` (no codex) | 2 | cc,grok |
| `positive-codex` / `baseline-codex` | 1 | codex |
| `positive-cc` / `baseline-cc` | 1 | cc |
| `positive-grok` / `baseline-grok` | 1 | grok |

Each job is `harness=… evalAgent=<included harnesses> --skills srp,commenting,logging,worktree -k 5 -n 5`
(baseline adds `--baseline`). Windows open at a
normal size on this monitor (cascaded, not maximised). After a job finishes the
terminal stays open as a shell; Up-arrow recalls the `./run_benchmark.sh`
command. Or skip the menu:

```bash
./launch_benchmarks.sh --preset positive-all-harnesses-all-judges
```

```bash
./launch_benchmarks.sh --preset baseline-codex-cc
```

```bash
./launch_benchmarks.sh --preset positive-grok
```

Regenerate the 14 shipped JSON files after changing the matrix builder:

```bash
./launch_benchmarks.sh --write-presets
```

`s` in the menu pastes new `./run_benchmark.sh` lines and writes another JSON
file under `presets/` (commit it if you want it in git). Extra user JSON files
appear **after** the shipped catalog. The Docker slot lock
still queues extra jobs when IPAM is tight.

Manual examples:

```bash
# Codex positive, both skills in one session (~25 trials at -k 5)
./run_benchmark.sh harness=codex --skills srp,commenting -k 5 -n 5
```

```bash
# Claude Code positive, one skill per job (~50 trials)
./run_benchmark.sh harness=cc --skills srp,commenting --run-separately -k 5 -n 5
```

```bash
# Both harnesses × separately × 2 skills × 5 tasks × -k 5 ≈ 100 trials
./run_benchmark.sh --skills srp,commenting --run-separately -k 5 -n 5
```

`-k 5` schedules five attempts **per task**; `-n 5` runs up to five trials at
once. The wrapper defaults to the same `-k 5 -n 5` when you pass no Harbor
flags. After the job finishes it prints a categorized console summary.
Several terminals may start at once: the wrapper serializes Docker networks
across processes when the daemon's address pool is tight (see
[Install Docker](#install-docker-on-ubuntu-2404)).

Do not use bare `-a codex` / `-a claude-code` / `-a grok-build` for these skill
benchmarks: those paths can leave host/user skill directories untouched and do
not default to the pinned CLIs / low reasoning.

## Model and run parameters

Override defaults on the command line (or edit `harbor.codex.yaml` /
`harbor.claude.yaml` / `harbor.grok.yaml`). Useful Harbor flags:

| Flag | Meaning |
| --- | --- |
| `-m` / `--model` | Agent model id (applies to the selected harness job) |
| `--ak reasoning_effort=…` | Effort: `low`, `medium`, or `high` (Codex, Claude, Grok) |
| `evalAgentModel=…` | Judge model id (same idea as `-m`; one value or one per eval agent) |
| `evalAgentReasoningEffort=…` | Judge effort (same idea as `--ak reasoning_effort=`) |
| `--ak version=…` | CLI pin override |
| `-k` / `--n-attempts` | Independent attempts per task (default example: `5`) |
| `-n` / `--n-concurrent` | How many trials run in parallel (default example: `5`) |
| `--skill` | Extra skill directory (job config already injects skills) |

Examples:

```bash
# Default Luna-low / Opus-low / Grok-4.6-low via harness selection
# (judge inherits the same harness when evalAgent is omitted)
./run_benchmark.sh harness=codex --skills srp -k 5 -n 5
```

```bash
./run_benchmark.sh harness=cc --skills srp -k 5 -n 5
```

```bash
./run_benchmark.sh harness=grok --skills srp -k 5 -n 5
```

```bash
# Higher reasoning for the coding agent
./run_benchmark.sh harness=codex --skills srp -k 5 -n 5 --ak reasoning_effort=high
```

```bash
./run_benchmark.sh harness=cc --skills srp -k 5 -n 5 --ak reasoning_effort=high
```

```bash
./run_benchmark.sh harness=grok --skills srp -k 5 -n 5 --ak reasoning_effort=high
```

```bash
# Different coding-agent model, one attempt
./run_benchmark.sh harness=codex --skills srp -k 1 -n 1 \
  -m openai/gpt-5.4 --ak reasoning_effort=medium
```

```bash
# Different judge: Claude grades Codex output
./run_benchmark.sh harness=codex evalAgent=cc --skills srp -k 1 -n 1 \
  evalAgentModel=claude-opus-5 evalAgentReasoningEffort=low
```

CLI `-m` / `--ak` values override the matching fields in the generated Harbor
job YAML. Keep subscription auth via the wrapper (Codex auth.json mount /
Claude OAuth token) unless you intentionally switch to API-key auth.

## Add the next evaluation

Keep each new coding task equally small:

1. add `coding-prompts/<name>.md` (frontmatter: `artifact`, `description`);
2. add `oracles/<name>.py` that implements the API for Harbor oracle runs;
3. run `./sync_tasks.sh` (or just the benchmark wrapper) to materialize
   `.generated/tasks/<name>/`;
4. add new skills only as `../prompts/programming-skills/<skill>/SKILL.md` plus
   `judges/<skill>/prompt.md` (+ `judge.toml`); for a vague control, add only
   `../prompts/programming-skills/<skill>-vague/SKILL.md` and reuse
   `judges/<skill>/`; for a programmatic git-layout skill, use
   `judge = "programmatic"` in `judge.toml` (no prompt.md) and a checker under
   `verifier/`; edit the shared verifier at `verifier/run_judges.sh`;
5. run `./sync_judges.sh` (runtime), then oracle / `nop` / one real model trial.

`./run_benchmark.sh` auto-discovers every selected coding-prompt (materialized
under `.generated/tasks/`) and every selected skill. Prefer the wrapper over bare
Harbor YAML.

Harbor records complete jobs under `evals/runs/<stamp>/` (`harbor/` for raw
output, `jobs/` for the pretty copy, `Projects/` for the simulated clone +
worktrees). Nothing is written to `/tmp` for the job tree.
