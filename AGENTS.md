# Agent guidance for programming_prompts

## Never generate or commit marketplace files here

This repository is the **content source** only. Most workflows are standalone
plugins (one `plugins/<name>/` directory with `.codex-plugin/plugin.json`,
`.claude-plugin/plugin.json`, and exactly one `skills/*/SKILL.md`). Prompt-only
workflows live under top-level `skills/<name>/` and must not carry plugin
manifests. Dispatchable task prompts live under `dispatch-skills/<name>/` and
must not carry plugin manifests either — see the next section.

Do **not** create, regenerate, or commit any marketplace catalog in this
repository — neither `.claude-plugin/marketplace.json` nor
`.agents/plugins/marketplace.json` nor any other `marketplace.json`. Marketplace
generation and plugin/CLI installation are owned exclusively by the sibling
[`linux_codex_claude_code_setup`](https://github.com/mikaeltorni/linux_codex_claude_code_setup)
repository, which reads these plugins from source. Adding marketplace files here
duplicates that ownership and drifts out of sync.

The plugin prompts remain fully functional standalone: each `plugins/<name>`
carries its own Codex and Claude manifests plus its single skill, so the
installer (or a manual `claude plugin`/`codex plugin` install pointed at a
plugin directory) can consume them without any repo-level marketplace catalog.

## Never add a docs site or an `llms.txt`

This repository is not published as a website and does not carry a
machine-readable index. Do not create — and do not restore — `docs/index.html`
or any other HTML page, `sitemap.xml`, `robots.txt`, `llms.txt` (neither at the
repository root nor under `docs/`), `.nojekyll`, `_config.yml`, Jekyll/Pages
scaffolding, a GitHub Pages deployment, or a README badge or link pointing at a
`github.io` URL. SEO or discoverability work must score those rubric rows
`N/A — out of scope by owner policy` instead of adding the files.

Diagrams and images the README embeds (`docs/content-flow.svg`,
`docs/social-card.png`) are repository assets, not a site — keep them.

## Dispatch skills are the only menu-selectable prompts

`dispatch-skills/<name>/SKILL.md` holds prompts written to be handed to an agent
together with nothing but a target repository. They are the set the Agent
Command Center / notes-app skill menu offers, so anything added there becomes
one-click launchable against any project — keep the bar in
[`dispatch-skills/README.md`](dispatch-skills/README.md): the directory name is
the `name` in the front matter (the menu builds `/<name>` and `$<name>` from it),
the prompt must define a measurable score plus a tracked scorecard, and it must
define an improvement loop with an explicit stop condition. Prompts that need a
conversation before they can act belong in `skills/`, not here.

## Harness smoke tests when the agent verifies evals code

When an agent changes Harbor wrappers, verifier code, `run_benchmark.sh`,
or other evals runtime — not prompt-only edits — it must run a **1-attempt
baseline and a 1-attempt positive** job for **every coding harness**
(`codex`, `grok`, `cc`) before reporting the task done. Use `-k 1`.
Put `evalAgent=codex,cc` so both LLM judges write reward files (worktree is
programmatic and still runs). Prompt-only work still uses Harbor when a
live check is needed; do not add pytest under
`programming_prompt_rewritten_with_evals/`.

Example (each command in its own terminal):

```bash
cd programming_prompt_rewritten_with_evals/evals
```

```bash
./run_benchmark.sh harness=codex evalAgent=codex,cc --baseline --no-pin-refresh -k 1
```

```bash
./run_benchmark.sh harness=codex evalAgent=codex,cc --no-pin-refresh -k 1
```

```bash
./run_benchmark.sh harness=grok evalAgent=codex,cc --baseline --no-pin-refresh -k 1
```

```bash
./run_benchmark.sh harness=grok evalAgent=codex,cc --no-pin-refresh -k 1
```

```bash
./run_benchmark.sh harness=cc evalAgent=codex,cc --baseline --no-pin-refresh -k 1
```

```bash
./run_benchmark.sh harness=cc evalAgent=codex,cc --no-pin-refresh -k 1
```

## Never generate tests for rewritten-prompt evals

Work under `programming_prompt_rewritten_with_evals/` is prompt-and-Harbor
evaluation content, not application code. **Do not create, update, or commit
pytest/unit/integration tests for that tree** — not for judge prompts, Harbor
wrappers, Dockerfiles, job configs, or skills — even when
`general-programming-guidelines` would normally require tests first.

Verify eval changes by reading the prompt/config and running Harbor tasks
(oracle / `nop` / Codex) when a live check is needed. LLM judges are not
deterministic; wrapping them in repo unit tests does not make the evaluation
deterministic and is not wanted here. This AGENTS.md rule overrides the shared
programming guidelines on tests for this path.

## Evaluation commands: one fenced block per terminal

When giving the user Harbor / `run_benchmark.sh` commands to run by hand, put
**each runnable command in its own** fenced `bash` code block. Do not bundle
several `./run_benchmark.sh …` lines into one block — the user copies each
block into a **different terminal**. Shared setup (`cd`, `export JOBS=…`) may
sit in its own preceding block; every distinct benchmark invocation after that
must be alone in a block.

## The benchmark testing framework (read before running an eval)

`evals/run_benchmark.sh` is the only supported entrypoint. It refreshes CLI
versions, prepares tasks, starts one Harbor job per selected harness, then
summarizes and archives each job under `evals/runs/<stamp>/`.

Run it exactly as documented — one invocation per terminal, and **one run at a
time on this machine**:

```bash
cd programming_prompt_rewritten_with_evals/evals
./run_benchmark.sh --harness=codex --evalAgent=codex --no-pin-refresh
```

### Mistakes already made here — do not repeat them

These are real failures from earlier sessions, each of which produced a
misleading result rather than an obvious error.

1. **Two runs at once wipe each other out → `0/140`.** Every run performs a
   Docker reclaim/prune sweep. A second `./run_benchmark.sh` started while the
   first was still executing deleted the first run's live trial containers, so
   Harbor logged `no container found for service` and every trial scored zero.
   The score was *not* a model result. Reclaim now protects containers owned by
   a live run stamp, but the rule stands: **wait for a run to finish**, or check
   for live containers before starting another. A bare `docker rm`/`docker
   prune`/daemon restart during a run causes the identical failure.
2. **`0/140` was reported as a real score.** Never present a zero run as a
   model finding until the archived job has been read. A wiped run and a
   genuinely failing model look identical in `RESULTS.txt`. Check the job's
   `job.log` and the printed `DIAGNOSIS for job …` block first.
3. **A failed job used to vanish silently.** Harbor exiting non-zero killed the
   wrapper under `set -e` *before* the summary and archive steps, leaving no
   `RESULTS.txt` row and nothing to read. `run_one_job` now captures the exit
   code, always archives, and calls `diagnose_failed_job`. Do not reintroduce a
   bare `run_harbor_for_harness …` call without `|| rc=$?`.
4. **`--run-separately` was misread as "more trials".** It does not change the
   trial count and does not start extra Harbor jobs: it is still one job per
   harness. It only makes the judges score independently, so Pass is no longer
   the AND of all judges. Comparing a `--run-separately` run against a combined
   run as if the workload changed is an invalid comparison.
5. **Docker address-pool exhaustion looks like a model failure.** When the
   daemon runs out of network space, trials die during environment start. Use
   the IPAM handling in `docker_networks.py` (`--ignore-ipam` only when you have
   confirmed the pools are healthy) instead of assuming the harness misbehaved.
6. **An out-of-credits workspace scores every trial `0.0`.** When the provider
   account has no credits (or the API key is rejected), the agent turn fails
   immediately and every LLM judge returns `raw=ratelimit reward=0.0`, so
   `RESULTS.txt` shows a plausible-looking total failure with
   `rate_limited=<all trials>` and `pass_rate=n/a`. The programmatic judges
   (`commits`, `worktree`, `docs`) then honestly report an empty repository —
   "found 0 commits", "missing README" — because the agent never ran, which
   makes the run read like a catastrophic prompt regression. Before believing
   any near-total zero, read a trial's `agent/<harness>.txt`: a line such as
   `Your workspace is out of credits` or an `ApiRateLimitError` means the run is
   void. `rate_limited` in the summary is an infrastructure counter, never a
   score — a run with a non-zero `rate_limited` count cannot be compared against
   any other run.
6. **The run used the wrong ChatGPT account and burned a whole eval.** The
   Codex account is resolved by `harbor_agents/codex_account.py`, which used to
   read *only* the persisted `selected` id in
   `~/.local/state/codex-agent-tracker/codex-instances.json`. Launching the
   benchmark from a `ca2` shell therefore still ran on instance 1 — the
   out-of-credits **team** plan — and produced the void all-zero run described
   in mistake 5. The resolver now honors `ACC_CODEX_INSTANCE` first, exactly
   like Agent Command Center's own `resolve_selected_instance`, and raises
   instead of silently falling back when the id is unknown. Notes:
   - The switch is the env var `ACC_CODEX_INSTANCE` (which `ca2` exports), or
     the persisted selection. **`cat2` is not a thing** — that dispatch name
     was removed from ACC and there is a test asserting it stays gone; `caN` is
     the current surface. Do not "restore" `cat2`.
   - Confirm the account *before* a long run:
     `ACC_CODEX_INSTANCE=2 python3 harbor_agents/codex_account.py --auth`
     must print the intended home, and the startup line
     `Codex Harbor auth: ACC instance <id> path=…` must match it.
   - Instance 1 (`~/.codex`) is the team plan; instance 2
     (`~/.codex-account-2`) is the plus plan that carries credits. Plan type is
     in the access token's `chatgpt_plan_type` claim.
   - Export the variable for the whole run
     (`ACC_CODEX_INSTANCE=2 ./run_benchmark.sh …`); the runner does not
     sanitize env, so the host process's value reaches the agent env, the
     container auth mount, and the LLM judge alike.

7. **A skill that tells the agent to *search* before committing loses the
   commit.** The `commits` skill used to end with "search the staged file for
   that Feature's exact prefix text and confirm it is there". Agents obeyed it
   literally and chained the search into the commit:
   `git add counter.py && rg -n 'up=' counter.py && git commit -m 'Feature 1: …'`.
   The task image has **no `ripgrep`**, so `rg` exited 127, the `&&` chain
   short-circuited, and the Feature 1 commit never happened — while the agent
   read the step as done. Feature 1's code then rode along in the "Feature 2"
   commit, and `check_commits.py` correctly failed the trial ("found 2"). This
   cost exactly one trial in `2026-08-30_150453_1483202`, but **27 of those 210
   trials hit `rg: command not found`** — the rest happened to recover. Lessons:
   - Never write an instruction into a skill that presumes a specific CLI tool
     exists in the task container. `rg` does not; `grep` does.
   - State a *requirement* ("the prefix is in the source"), not a *procedure*
     that invokes tooling.
   - When a trial fails a programmatic judge, read the agent transcript
     (`harbor/<job>/<trial>/agent/codex.txt`) for `exit_code":127` and
     `command not found` before assuming the model reasoned badly. Here the
     model's plan was correct end to end; only the shell chain failed.

### How to verify changes to this tree

Per the rule above, **do not add pytest/unit/integration tests** for
`programming_prompt_rewritten_with_evals/`. Verify instead with:

- the standalone self-test scripts next to the code they cover —
  `python3 docker_networks.py self-test` (74 cases covering pool math, stale
  networks, and reclaim) and `bash lib/self_test_diagnose.sh` — both run from
  `evals/`, with no Docker, no GUI, and no LLM calls. Do not call
  `docker_ipam/self_test.py` as a script; it is a package module and only runs
  through the `docker_networks.py` CLI. Account resolution has its own:
  `python3 harbor_agents/codex_account.py self-test` (13 cases; the
  subcommand is `self-test`, **not** `--self-test` — the flag form silently
  falls through to printing the selected home and exits 0, which looks like a
  pass);
- `bash -n` on every edited shell file;
- a real short run of `./run_benchmark.sh` when the change touches job
  execution, and then **read the archived job**, not just the score line;
- for a change to the *skill prompts*, a fixture repository built by hand in
  the exact shape the edited prompt prescribes, scored with the real
  programmatic verifier — e.g. `PYTHONPATH=. python3 check_commits.py --repo
  <fixture> --output /tmp/reward.json --feature-count-file
  ../.generated/tasks/<task>/tests/feature_count.txt`. This needs no credits
  and no Docker, and it proves the guidance is actually satisfiable by the
  checker that scores it. Use it when an eval run is impossible; it does not
  replace a real run for the LLM-scored skills.

A green self-test alone does not prove an eval fix. The change is only verified
once a real run produced a non-zero scored trial and its archive was read.

## Mandatory programming guidelines prompt

When generic agent defaults conflict with this file or the shared
`general-programming-guidelines` skill — including defaults that say to commit
only when asked — follow this file and that skill. Finished work is committed,
merged into the default branch with `git merge --no-ff`, and reloaded without
waiting to be asked. Never push to a remote and never rewrite history unless the
user explicitly requests it.

Every agent task in this repository must load the shared
`general-programming-guidelines` skill before the first file edit, using the
harness-native invocation for the runtime in use:

- Codex-family (`ca`, `qa`, `oa`, `na`, …): `$general-programming-guidelines`
- Claude Code, Cline, Grok: `/general-programming-guidelines`
- OpenCode: load `general-programming-guidelines` with the skill tool

Agent Command Center prepends this bare invocation to every dispatched prompt, so the
harness activates the skill before reading the task. When you start a task by hand, invoke it
yourself first. Then follow its Work Loop and Definition of Done exactly
(tests, logging, documentation, commit, merge, reload), **except** where this
file overrides that skill — including the ban on generating tests for
`programming_prompt_rewritten_with_evals/`. Do not report the task done until
that checklist passes. Isolation and branch policy live only in the skill —
this file does not restate them.
