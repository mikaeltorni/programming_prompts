# Programming Prompts — AI Coding-Agent Prompts

[![Last commit](https://img.shields.io/github/last-commit/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/commits/master)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/graphs/commit-activity)
[![Issues](https://img.shields.io/github/issues/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/issues)

Programming Prompts is a prompt library that provides reusable AI coding-agent prompts and engineering guidance for Codex and Claude Code users.

![Diagram showing Programming Prompts flowing into plugin prompts, direct skills, and dispatch skills for agents and installers](docs/content-flow.svg)

This repository is the canonical content source for the engineering standards
used across this workspace's projects. It contains installable plugins, direct
skills, and dispatch skills; the separate installer repository owns marketplace
generation and deployment.

## Contents

- [AI coding-agent prompt features](#ai-coding-agent-prompt-features)
- [Installation and usage of AI coding-agent prompts](#installation-and-usage-of-ai-coding-agent-prompts)
- [Plugins](#plugins)
- [Direct Skills](#direct-skills)
- [Testing](#testing)
- [Troubleshooting and FAQ](#troubleshooting-and-faq)
- [Contributing](#contributing)

The install catalog intentionally distinguishes plugins from direct skills:

- Plugins: Commit Guidelines and Linux Desktop Configuration.
- Direct skills: Docs, Init Project,
  Refactoring, Setup Repository Guidelines, and Workflow.
- Python Logging is retired and has been removed from this repository.

## Repository dependencies

This repository has no runtime dependency.

Repository ownership and routing are documented in [AGENTS.md](AGENTS.md).

Related research is documented in [Prompt Engineering for Software Development](https://github.com/mikaeltorni/prompt_engineering_for_software_development),
and challenge generation is covered by the
[Prompt Challenge Generator](https://github.com/mikaeltorni/prompt_challenge_generator).
For local conventional commit suggestions from Git diffs, see the
[coding_tools local AI commit message generator](https://github.com/mikaeltorni/coding_tools).

## Quickstart

Clone the content source and inspect a skill directly:

```bash
git clone https://github.com/mikaeltorni/programming_prompts.git
cd programming_prompts
sed -n '1,120p' programming_prompt_rewritten_with_evals/prompts/programming-skills/testing/SKILL.md
```

The command prints the independent testing skill. The programming suite
contains workflow, commits, worktree, docs, srp, commenting, logging, debug,
and testing; see its [skill catalog](programming_prompt_rewritten_with_evals/prompts/programming-skills/README.md).

## AI coding-agent prompt features

This repository maintains the canonical engineering standards used across all
development projects in this workspace. Plugin prompts package exactly one skill
and carry manifests for both Codex and Claude Code; direct skills carry only
`SKILL.md` content.

- **Testing Skill** — Focused regression checks, public-interface coverage, existing project tooling, and isolated execution; source: [testing](programming_prompt_rewritten_with_evals/prompts/programming-skills/testing/SKILL.md).
- **Workflow Skill** — Explicit-only orchestration that plans first, coordinates only selected companion skills, always writes code, and conditionally uses worktree and documentation guidance.
- **Docs Skill** — User-facing project documentation for completed programming changes.
- **Commit Guidelines** — Cautious Git commit workflow (inspect → plan → stage hunks → verify → compose).
- **SSH VM** — Connect to a VM for remote software deployment or verification, with Ubuntu live USB setup guidance.
- **Linux Desktop Configuration** — Shared GNOME/Ubuntu desktop rules: applying changes silently from the command line (gsettings/dconf live, `systemctl --user restart`, `gnome-extensions enable/disable`), activating edited extension code with the sanctioned in-place X11 run-dialog reload (`xdotool` `Alt+F2 r`) while still forbidding destructive session restarts, asking for manual logout to activate extension code on Wayland, preserving user sessions, maintaining clean-install compatibility, and using root-optional (sudo-free) installer patterns.
- **Refactoring Skill** — Test-driven refactoring methodology for restructuring monolithic codebases into clean modules.
- **Init Project Skill** — Auto-triggered secure project initialization with UV + supply-chain protection.
- **Setup Repository Guidelines** — On-request (or new-project) repository-family routing and installer integration based on the orchestration manifest; no longer auto-triggered on every task.

## Repository Structure

```
programming_prompts/
├── AGENTS.md                               # Rule: no marketplace files in this repo
├── plugins/                                # One directory per plugin; each has
│   │                                       #   .codex-plugin/ + .claude-plugin/ manifests
│   │                                       #   and exactly one skills/<name>/SKILL.md
│   ├── commit-guidelines/                  # Cautious Git commit workflow
│   ├── linux-desktop-configuration/        # Console-only desktop deployment + sudo-free installers
├── skills/                                 # Direct skills, not plugins
│   ├── workflow/                            # Explicit-only programming orchestrator
│   ├── docs/                                # Post-code project documentation
│   ├── init-project/                       # Secure init with UV + supply-chain protection
│   ├── refactoring/                        # Test-driven refactoring workflow
│   ├── setup-repository-guidelines/        # On-request setup-family routing & install policy
│   └── ssh-vm/                             # SSH deployment and testing on a VM
├── dispatch-skills/                        # Menu-selectable task skills: repo in, score out
│   ├── github-seo/                        # GitHub discoverability audit, scored 0–100, looped
│   ├── github-portfolio-scan/             # Directory-wide resume/portfolio release-readiness audit
│   └── worktree-cleanup/                  # Finished-worktree reclaim, scored, never stored
├── tests/                                  # pytest policy tests for the plugin prompts
├── .log/                                  # Runtime logs (gitignored)
├── LICENSE.md                             # MIT License
└── README.md                              # This file
```

## Installation and usage of AI coding-agent prompts

Installation belongs to the sibling installer repository. Its committed
`default.json` maps each prompt to either a plugin or a direct skill and
controls default selection. This repository intentionally
contains no `install.sh`, installer libraries, or marketplace catalogs — marketplace
generation is owned entirely by the installer repository (see `AGENTS.md`). Each
`plugins/<name>` directory stays standalone-installable via its own Codex and
Claude manifests plus its single skill. Top-level `skills/<name>` directories
are installed directly as skills and do not appear in plugin marketplaces.

## Plugins

### commit-guidelines

Packages the cautious Git commit workflow as a Codex/Claude plugin (skill name:
`commit`). Guides agents to inspect all changes (staged + unstaged), split diffs
into logical commits, stage exact hunks, and compose clean conventional commits,
executing the complete cross-repository commit plan in one run.

**Install:** The programming-prompts marketplace installs this as `commit-guidelines@programming-prompts`. Confirm with:
```bash
codex plugin list
```

### linux-desktop-configuration

Packages the shared Linux desktop configuration rules as a Codex plugin (skill name: `linux-configuration`). Applies to any task touching GNOME Shell extensions, gsettings, themes, hotkeys, systemd user services, or repository installers:

- **Apply changes silently from the console:** most changes need no Shell reload — `gsettings set` (hotkeys/themes/shell keys/an extension's own settings) applies live, `systemctl --user restart <unit>` restarts only the affected service, and `gnome-extensions enable/disable` toggles extension state without a GUI flash. For extension *code* changes, deploy and verify the files, then activate the edited source with the in-place reload that matches the session: on X11 drive GNOME's run dialog with `xdotool` (`Alt+F2 r`) to restart the Shell in place; on Wayland ask the user to log out and back in. Never force changes through with logout, reboot, `gnome-shell --replace`, or shell-kill commands.
- **Clean installation compatibility:** every change must reproduce on a fresh checkout via `installation_scripts/install.sh`; installers stay idempotent.
- **Root-optional installers:** all project `install.sh` scripts run sudo-free in user mode (root-only steps are skipped and reported via `SUDO_REQUIRED_STEPS`); only `linux_installations_setup` hard-requires root.

**Install:** The programming-prompts marketplace installs it as `linux-desktop-configuration@programming-prompts`. Confirm with:
```bash
codex plugin list
```

## Direct Skills

### ssh-vm

Use `$ssh-vm`, or let it apply automatically, for tasks that deploy or test
software on a VM over SSH. On first contact, if the user provides an IP or
hostname without confirming SSH setup, it gives Ubuntu VM-console setup
commands, including setting the account password, and waits for confirmation
before any network attempt. Once confirmed, it connects using a key or an
interactive password prompt, updates the project copy, and installs and checks
it on the VM. For visual behavior, it captures and inspects a VM screenshot
when a safe capture path is available. If visual confirmation would help but
no capture path exists, it asks the user for a screenshot. SSH alone does not
guarantee guest desktop access. Installed as a native skill under each
harness's skill directory.

### workflow

An explicit-only orchestrator for programming tasks. Invoke `$workflow` to
create a repository-local Markdown plan, apply only the companion skills
enabled in the current prompt, write the code, and conditionally use worktree
or documentation guidance when those companions are enabled. With no companion
skills it falls back to plan-then-code. Installing or discovering the skill
does not activate it, and other skills do not depend on it.

The initial plan contains both the four workflow phases and a concrete
`## Microsteps` table with `Step`, `Phase`, `Action`, `Status`, and `Evidence`
columns. Actions name real files or entrypoints and their observable outcomes;
implementation, integration, required checks and delivery steps are planned
before code changes. Agents update the same plan at each microstep boundary,
retain completed work and evidence, and refine pending work when discovery
changes the task. Microsteps do not change capability-sentence commit boundaries.

ACC launches pass `ACC_WORKFLOW_FILE` as an absolute path under the launch
project's `tmp/workflow/`. Otherwise the public `$workflow` entrypoint uses
`<project-root>/tmp/workflow.md`. Both tables use `pending`, `in_progress`,
`complete`, and `skipped`; optional phases and their actions are skipped when
their companions are unavailable. The plan stays ignored and is retained across
worktree changes. ACC reads these tables for its top-right segmented progress
bar, phase counts, and each task's menu background progress.

After changing the prompt, run `acc pp rebuild` to refresh saved selections;
`acc pp status --skill v2:workflow --check` verifies the selected V2 consumer.
The original and V2 workflow prompts use the same microstep schema.

### docs

Writes or updates the user-facing documentation affected by a completed code
change. It covers the public entrypoint, commands or API, supported inputs,
configuration, and important usage constraints without taking ownership of
function docstrings from a separately selected commenting skill.

### testing and the programming suite

The independent [testing skill](programming_prompt_rewritten_with_evals/prompts/programming-skills/testing/SKILL.md)
requires reusable behavior checks, bug regressions, meaningful public-interface
coverage, isolated execution, and existing project tooling. Static content uses
direct checks or the project's prescribed evaluation method. It does not create
CI or install a new test framework by default.

Coverage distinguishes argument shape, numeric conversion, and domain rejection.
Commands may share a representative rejection check when they execute the same
validation path; independent handlers need their own coverage. When a later
requirement changes accepted inputs or output, revise every affected retained
assertion and recompute its expected result from that case's fixture and
preceding public calls.
Different operation names do not create independent copies of one shared
predicate. Text/name operands require no numeric-conversion case unless their
contract makes them numeric. Resource lookup cases follow their actual owners.

The coverage inventory maps public commands and operands to saved assertions
for argument shape, conversion and requested domain rules. Missing and extra
operands are separate rejection classes. Current-source runners retain only
current-contract expectations; historical stage checks require matching source.
Add executable future-capability cases only at their implementing revision.
When a new command replaces its former unknown-command rejection, update that
current-suite assertion and continue the remaining stages; a historical runner
is not needed solely to preserve the retired expectation.
Review every retained rejection loop when a query becomes available, using
populated fixtures and immediate public observations when preservation is
required. New complete cases do not repair incomplete older cases. Generated
interpreter caches can stay unstaged; incidental cleanup never blocks delivery.
Document the cumulative final runner with its working directory, discovery
flags and required environment. Development selectors must not leave current
assertions using obsolete expectations or silently omit delivered capabilities.
Public history or aggregate queries can be the strongest available observation;
an empty-state rejection keeps its required empty fixture. Supplemental private
checks do not replace those public observations.
Reject malformed clear/reset forms while the fixture is still populated,
before successfully clearing it. When all public queries reject the required
empty fixture, document that observation limit rather than inventing a query.

Agent Command Center's default installation enables V2 `commits`, `worktree`,
`workflow`, `docs`, and `testing`. Other skills remain independently selectable;
manual selections are preserved. Apply this baseline across every harness with:

```bash
acc pp enable --both --skill v2:commits,v2:worktree,v2:workflow,v2:docs,v2:testing
```

```bash
acc pp status --both --skill v2:commits,v2:worktree,v2:workflow,v2:docs,v2:testing --check
```

The generic programming guidelines and their global bootstrap are retired and
removed. Installer postflight disables their previous managed blocks and native
skill paths, including registered Codex accounts. Existing conversations may
retain previously supplied instructions; new sessions receive the current
selection. Python setup remains owned by `init-project`, and desktop deployment
remains owned by `linux-configuration`.

The testing skill has a semantic Harbor judge under `evals/judges/testing/`.
The judge resolves the current contract, traces assertions in execution order,
and checks validation coverage, immediate public observations after rejection,
and the saved runner's isolation fixtures. Historical coverage is assessed from
the corresponding Git revision. A passing runner still needs this coverage audit.
The judge derives command shape from public operands, follows actual shared
validation helpers, and requires a request or task-log basis for numeric ranges.
The declared input type bounds required validation; a defensive non-string
guard does not add non-string cases to a string-command contract. Strict numeric
bounds need their excluded endpoint and a value beyond it in each independent
path. Preservation checks concern the resources affected by that operation.
When only aggregate state queries exist, it uses those observations and records
their limits. Source review alone does not establish a new benchmark pass rate.
Default benchmark skill discovery and shipped launcher presets select the eight
companions (`commenting`, `commits`, `debug`, `docs`, `logging`, `srp`,
`testing`, `worktree`). `workflow` stays explicit `--skills workflow`.
To inject and score only testing on Codex instance 1, use the public benchmark
entrypoint below. Omitted `--tasks` selects all coding tasks, `-k 3` requests
three attempts per task, and omitted concurrency uses automatic capacity. The
runner copies the authoritative testing skill and judge into the new job.

```bash
cd /home/mk/projects/programming_prompts/programming_prompt_rewritten_with_evals/evals
```

```bash
ACC_CODEX_INSTANCE=1 ./run_benchmark.sh --harness codex --eval-agent codex --skills testing -k 3
```

To evaluate the full suite including workflow:

```bash
cd programming_prompt_rewritten_with_evals/evals
```

```bash
ACC_CODEX_INSTANCE=1 ./run_benchmark.sh --harness codex --eval-agent codex --skills workflow,commits,worktree,docs,srp,commenting,logging,debug,testing -k 3
```

Run one benchmark wrapper at a time. Judge verdicts inspect saved checks against
the original request; without an agent trace, execution order remains unverified.
The testing-only command requests 24 trials across the current eight tasks.
Increasing `-k` increases attempts, independently of judge-worker concurrency.
Use `-k 7` to repeat the 56-trial testing-only workload.
Only the selected testing judge runs for each trial. Its verdict must use the
final contract and actual assertion body: a retired command's rejection can be
correct, and a historical expectation is not a current expectation. Judge
execution must follow the saved invocation, including explicit discovery flags;
zero tests from a different probe do not establish a submission defect.

### init-project

Secure project initialization as a direct skill. Guides agents to set up new projects with UV by Astral as the required package manager, implementing a rolling 24-hour publication delay via uv's native `[tool.uv] exclude-newer = "24 hours"` setting to protect against supply-chain attacks. Plain `pip` installs must consume a hash-locked `uv export` rather than resolve dependencies directly.

### refactoring

A direct skill that implements the **Test-Driven Refactoring** paradigm. Guides agents to restructure monolithic codebases into well-organized, single-responsibility modules without changing behavior — tests first, then extraction, then integration.

Key principles:
1. Analyze before touching code (identify monoliths, orphaned functions, missing tests).
2. Plan the module structure with clear responsibilities.
3. Write tests for existing functionality before extracting anything.
4. Extract one cohesive module at a time by default; for explicitly broad workspace requests, inventory every repository first and verify each extraction independently.
5. Update imports, documentation, logging paths, and project tree after each extraction.
6. Commit each completed extraction in the task worktree by default.

### setup-repository-guidelines

A direct skill (not an auto-applied global instruction) that applies owner
routing, component selection, clean-install, deployment, and prompt-free
keyring requirements to the repository family discovered from the sibling
`installation_scripts` manifest. Invoke it only when the user requests repository
initialization or explicitly invokes `setup-repository-guidelines` by name or tag
(`$setup-repository-guidelines` or `/setup-repository-guidelines`). Missing
guidelines or a new directory do not trigger it. It is not merged into
`AGENTS.md`/`CLAUDE.md` as a managed
global conditional that fires at the start of every task. Membership is still
read dynamically from `CLONE_REPOS`, so newly added repositories enter scope
without changing this skill.

## Dispatch Skills

`dispatch-skills/` holds the task prompts that are meaningful with no context
beyond "here is a repository". They are the only prompts offered by the
notes-app skill menu, which launches one agent per selected project with the
harness-native invocation — `/name` for Claude Code, Cline, and Grok, `$name`
for the Codex family — built from the skill's directory name.

A prompt qualifies for this folder only if it defines a measurable score — kept
in a tracked scorecard file, or reported in the run output when storing the
audit would commit private detail — and an improvement loop with an explicit
stop condition; see [`dispatch-skills/README.md`](dispatch-skills/README.md).

### github-portfolio-scan

Audits **any directory** of git checkouts for GitHub resume / portfolio
release-readiness. It inventories live original repositories, scores each one
on product story, docs, tests, license, secrets, personal-machine coupling, and
authorship, then reports a tier list with evidenced positives and flaws. The
run is read-only: it does not edit, push, or change visibility, and it does not
apply SEO extras — those wait for a later [`github-seo`](dispatch-skills/github-seo/SKILL.md)
dispatch after a repository is chosen for public release. The audit lives in
the run report, not in the scanned trees.

### github-seo

Audits a GitHub project's discoverability against a weighted 100-point rubric —
repository metadata and topics, README above the fold, keyword coverage,
AI/LLM citability (question-shaped FAQ, a quotable definitional
sentence), community health signals, docs-site technical SEO, registry presence,
cross-links, and freshness — minus penalties for keyword stuffing,
unsupported claims, badge and topic spam, artificial engagement, and dead links.
For mikaeltorni's repositories, per-criterion evidence and round history live
in the private `seo_optimization` repository, not in this public content
source. The loop closes the highest-value gap, re-measures from scratch, and
repeats until a re-audit independently reproduces 100/100, then switches to
maintenance. Points are only awarded against recorded evidence, and nothing is
published, renamed, or posted on the user's behalf.

## Logging

Per the programming guidelines, any repository-generated log files must be
written under the repository-root `.log/` directory (created on demand) and are
gitignored to keep the working tree clean. No runtime utilities currently ship
in this repository, but the convention is reserved for any that are added later:

```bash
# Repository-generated logs live here (gitignored)
.log/<component>.log
```

## Testing

Run the test suite with pytest:

```bash
python3 -m pytest tests -v
```

Each plugin is standalone-installable and can be validated directly:

```bash
claude plugin validate --strict plugins/<name>
codex plugin list
claude plugin list --json
```

The Harbor benchmark's public entrypoint is
[`run_benchmark.sh`](programming_prompt_rewritten_with_evals/evals/run_benchmark.sh).
Coding tasks live under
[`evals/coding-prompts/`](programming_prompt_rewritten_with_evals/evals/coding-prompts/);
`greeter` is the remaining log-driven debug task (`/app/greeter.py` →
`run_greeter` for `<name> <hour>`, `bye <name>`, and `period <hour>`).
The runner accepts `--harness`, selects the Codex judge with
`--eval-agent codex`, selects programming skills with `--skills`, and accepts
`--tasks`, `--concurrency`, `--baseline`, and Harbor's `-k` attempt count.
Without `--concurrency`, all selected tasks × attempts remain eligible, subject
to configured LLM caps and available per-trial Docker network slots. The automatic
[launch guard](programming_prompt_rewritten_with_evals/evals/harbor_agents/launch_guard.py)
uses the full configured trial ceiling immediately. It holds new container
starts only when a running agent's remaining execution time falls within
measured setup headroom: the 95th percentile of the latest setup durations plus
five seconds. Holds clear as agents finish; there is no ramp-up or permanent
capacity reduction. Waiting happens before container setup and
before the waiting trial's agent timer, so each trial receives its full budget.
The guard applies to Codex, Claude Code and Grok in positive and baseline runs.
It avoids starting new containers close to active deadlines but cannot guarantee
a task finishes before its own deadline. Use `--concurrency N` only to impose a
lower ceiling; no flag is needed
for pacing. `-k` controls attempts per task independently.
Run one benchmark invocation at a time. See the
[evals README](programming_prompt_rewritten_with_evals/evals/README.md) for the
command surface and [AGENTS.md](AGENTS.md) for the repository's run policy and
required full-suite command.

`--skills` selects the Harbor skills and corresponding verifier judges;
positive jobs install the selected skill bodies, while baseline jobs omit them.
`workflow` requires explicit selection. Generated task instructions explain
that `/Projects/app` is the writable Git checkout and `/app` resolves to it.
Creation tasks may start empty; agents are authorized to create the requested
files there and must finish implementation before reporting delivery. Baseline
and positive jobs receive the same workspace setup. Verifier task context keeps
the unmodified original coding request.
An initial file search with no matches or exit status 1 is expected in an empty
creation checkout; continue by creating the authorized files. The counter task
explicitly uses one process-local value initially zero, retained across calls
to increment, decrement, get and set. This clarification matches its oracle.

For a local content deployment without starting a benchmark, run
`./sync_tasks.sh` followed by `./sync_judges.sh testing` from `evals/`.
They rebuild ignored `.generated/tasks/` copies and copy the selected judge
and shared verifier. `TASKS_DIR` can target a specific generated task directory.
Do this when no benchmark is running; the benchmark wrapper also regenerates
its own isolated job copies from canonical source when a new run starts.

The [SRP skill](programming_prompt_rewritten_with_evals/prompts/programming-skills/srp/SKILL.md)
also guides focused edits: start with a small working slice, extend its existing
helpers and command path, and preserve simple responsibilities as requirements
change. The `todo`, `bank`, and `stats` benchmark prompts repeatedly revise
earlier behavior as well as adding commands. Each stage requires public-entrypoint
checks and a working commit; the SRP judge receives historical source and diffs
to assess unnecessary churn alongside the final function structure. A justified
local extraction is allowed, and diff size alone is not the score.
Before introducing another operation, compare its decisions with existing
owners and extract any shared classification, calculation or validation once.
Keep operation labels and effects in their respective owners. Successful token
conversion establishes representability; operation-specific sign, magnitude,
finite-value and integral-value requirements stay in the operation helper,
including historical revisions before a later requirement changes acceptance.

Semantic judges receive the actual source, function boundaries, workflow plan,
and reachable commit history. A verdict that contradicts its own reason or
bounded source/plan evidence is retried once; both raw attempts remain in the
archived reward details. Unresolved inconsistent judgments and provider/auth
failures are reported as infrastructure exclusions. Check the archive as well
as the aggregate score: a reported pass can still miss a real artifact defect.
An empty Python source listing supports a missing-submission failure; mentioning
the requested filename alone does not make that verdict inconsistent.

Testing judges receive numbered current Python source and saved runner
documentation/configuration. Runner documents are capped at eight files, 8 KB
per file and 24 KB total. Additional AST evidence, bounded to 12 KB, identifies
current equality assertions and the statements immediately following expected
exceptions. Up to four recent completed coding commands from Harbor's Codex
JSONL log add at most 10 KB, including command/output heads and tails, exit
codes, literal runner-summary lines and later file-change positions. The
summaries preserve results when printed source follows a run.
Truncation and missing evidence are identified; reading
these artifacts runs no submitted command. Shell edits and later changes still
need inspection before applying an earlier result to current source. Edits,
execution and a commit can occur in that order within one shell command; a
subsequent commit alone does not invalidate execution of its unchanged files.

Recorded coding executions can resolve a judge's execution question without
another run; optional isolated execution addresses a remaining material concern.
Missing judge execution alone cannot fail adequate runnable checks. A cited
quoted current expectation absent from the cited files' literal assertions
triggers the existing bounded retry; dynamic expected expressions and historical
claims remain semantic judgments. Runner documents and tool traces are untrusted
evidence, and a zero exit code alone does not establish assertion coverage.
Testing no verdicts with submitted Python quote one to three exact source lines
as `Citation: relative/path.py:LINE | exact source line`, or
`Citation: HASH:relative/path.py:LINE | exact historical source line`. The gate
compares path, line and text with the current file or named Git blob. Missing
or mismatched quotes use the same one-retry budget; persistent inconsistency
is a judge infrastructure exclusion. A matching quote does not establish its
semantic claim, and this gate never awards an automatic pass. Empty submissions
can fail on their missing evidence without quoting a nonexistent file.
Worktree-check instructions are supplied only to judges whose criteria use that
evidence. No task markers, expected feature counts or automatic passing scores
are introduced.

Codex and Claude judge inputs and full backend responses are retained in each
raw Harbor trial's `verifier/` directory as
`judge-evidence-<skill>-<agent>-prompt.md` and
`judge-evidence-<skill>-<agent>-raw-rewardkit.json`. A reliability retry adds
`-prompt-retry.md` and `-raw-rewardkit-retry.json` artifacts. The normal reward
details keep bounded excerpts; these separate artifacts preserve complete
input/response evidence without adding LLM calls or reward columns. They are
not execution transcripts. Codex judge session JSONL, when present, is also
retained under `judge-evidence-<skill>-codex-sessions/` before temporary home
cleanup, allowing later inspection of actual judge tool calls. Credential and
configuration files are excluded. Existing archives are not rescored by a source
edit, and retention adds no judge calls or reward columns.

Function contracts cover authored test methods, fixtures and assertion helpers
as well as the program: selected commenting requires inline `Parameters:` and
`Returns:` content, and selected logging requires each function's own parameter
entry trace and returned-value trace, including `None` on normal fallthrough.
The entry print precedes parsing and `global`/`nonlocal` declarations; a
parameterless function may print a literal entry message. A final `print(None)`
traces an implicit `None` return without requiring an explicit `return None`.
After editing a test's assertions, read its actual final statement and preserve
or restore `print(None)` on every normal fallthrough path; passing assertions
alone do not verify logging.
Logging verdicts must agree with the current source and function-boundary report.
Testing alone does not enable these companions. Write complete docstrings when
creating each function, including the initial regression test, and review test
methods independently of their assertions and logging. With SRP selected,
identify the parser and operation owners before the first source write. The
first working slice and repairs to existing code keep raw-command parsing,
state changes and computed results in helpers. The public dispatcher receives
an operation and its arguments from one shared parsing call before branching;
parsers may compose helpers internally. Extracting only formatting, token
conversion or history recording leaves the operation mixed.
Command-shape validation has one owner: a dispatcher does not repeat guards
already enforced by its shared parser. Moving a guard removes its former copy
in the same edit.

The testing judge accepts meaningful saved assertion scripts or framework tests
by source inspection when execution is unavailable, with that limit disclosed.
It inspects available historical checks against their own revisions, so retired
rules are not required in the final suite. Missing historical source is an
unverified limit, rather than evidence that earlier tests were absent. Agents
should retain unaffected regressions and meaningful negative assertions as they
extend a suite; terminal-only assertions do not replace saved checks. Choose
saved stdlib assertions or unittest checks when no framework exists; an empty
creation checkout or absent existing suite does not block implementation.
Read back delivered files before claiming that code or checks were saved.
Save runnable public-interface checks with each working revision, covering
explicitly requested empty commands, unknown operations and invalid argument
shapes when those rejection classes are part of the original contract.
The testing policy uses ordered revision gates and a saved coverage inventory
that names executable cases and independently expected results. Its separate
shared-validation section saves empty/unknown command and missing/extra argument
assertions before application edits in the first dispatch revision when required
by the contract. Extend the same suite, transfer unaffected assertions before
replacing cases, and inspect the actual inputs and assertions before every
commit; a docstring or implemented rejection branch does not supply coverage.
A reported bug retains its exact input and expected result alongside boundary
checks. When a public state query first
appears, upgrade earlier rejection tests in that revision. Each required
state-preserving rejection is immediately followed by public observations of
affected values and available history, before another rejection, mutation,
reset or reload. A later successful mutation's count or a private-state read
does not replace that observation. Task examples demonstrating recovery still
need the intervening query. Later-stage rules stay deferred, and explicitly
replaced rules retire only at the revision that replaces them. Record each
superseded expectation's last valid commit and replacement case, and update case
names and docstrings to describe their current assertions. Broader numeric
acceptance keeps other required domain rejections, including zero/negative
values, in each independently implemented validation path.
Reusable rejection helpers may accept independently expected observations and
upgrade retained cases when queries appear; inline cases still need the same
review. When a stage selector retires an obsolete numeric expectation, preserve
its method's unaffected validation assertions in active cases.

Record the saved suite's runnable command and confirm it discovers and executes
assertions. Track required failures by operation and rejection reason, retain
shared empty/unknown checks, and preserve applicable cases when consolidating a
suite. Separately dispatched no-argument commands need their own extra-argument
checks. Function documentation and entry/exit traces cover authored test helpers
and fixtures as well as application functions; inspect the complete changed
method body so its docstrings and final return trace survive assertion edits.
Root README delivery remains required without workflow. Complete every required
command in a capability sentence before its introducing commit, and reuse shared
classification and token-validation helpers when extending the program.

Codex semantic judges stream complete prompts through file-backed stdin. This
avoids Linux's per-argument limit for large source/history evidence without
truncating it or changing judge prompts and scoring. The adapter is scoped to
rewardkit's child process; other backends keep their existing launch behavior.
Run its isolated standalone checks from the repository root with:

```bash
python3 programming_prompt_rewritten_with_evals/evals/verifier/run_llm_judge.py --self-test
```


Both debug and testing judges receive verifier-owned original failure logs
from `tests/task-logs/`. A saved regression assertion may use a literal expected
value that matches the original log; the test itself need not parse that log.
The docs checker treats authored test runners as checks rather than application
entrypoints and evaluates exclusions relative to the checkout, so an external
worktree's `.worktrees` parent does not hide its application source.

For stateful checks, establish fresh state before every independent case while
preserving state within each requested multi-call sequence. Fixture setup may
reset private state or load a fresh module; behavioral assertions use the
public interface. Run mutable suites again in the same process or another order
to check isolation. The testing judge traces repeatability case by case and
cites the actual conflicting assertion for an isolation failure. A no-op method
adds no coverage, but does not erase meaningful assertions elsewhere.

Before the first source write, verify the registered physical task path and
matching branch against the full `<parent>/.worktrees/<project>/<project>_<type>-<feature>`
layout. Resolve the live repository with Git and its physical path, then derive
the store from its immediate parent and the project component from its basename.
Neither a guessed filesystem root nor an in-repository `.worktrees` directory
satisfies that layout. Retain that live-derived destination when comparing
registration before edits and at handoff; a successful merge does not repair a
wrong location. Move this task's incorrectly placed checkout with
`git worktree move` to the unused correct destination while preserving its branch
and files.
Worktree recovery drafts belong inside the registered task checkout's `tmp/`,
keeping the external project worktree group free of stray files and unregistered
directories.

## Configuration

This content repository has no runtime configuration. Plugin manifests,
direct-skill directories, and `dispatch-skills/` are the source of truth; the
installer reads them when it deploys prompts to an agent environment.

## Troubleshooting and FAQ

### Where should I start with Programming Prompts?

Start with the [programming skill catalog](programming_prompt_rewritten_with_evals/prompts/programming-skills/README.md)
and select the capabilities your task needs. Use `workflow` for explicit
coordination and `testing` for verification. Browse the [plugin directories](plugins/)
for packaged Codex and Claude Code integrations.

### Is this repository a plugin marketplace?

No. It is the content source for plugins and skills. Marketplace generation and
installation are owned by the external installer workflow, so no marketplace
catalog is committed here.

### Which prompt is used for GitHub SEO audits?

Use the [github-seo dispatch skill](dispatch-skills/github-seo/SKILL.md). It
audits a repository, records a scorecard, and loops over verified gaps.

### Which prompt ranks a folder of repos for a GitHub resume portfolio?

Use the [github-portfolio-scan dispatch skill](dispatch-skills/github-portfolio-scan/SKILL.md).
Point it at any directory of git checkouts. It inventories live originals,
scores release-readiness, and reports positives and flaws without editing those
trees. Run `github-seo` only after you pick a repository to make public.

### How do I validate a plugin?

Run `claude plugin validate --strict plugins/<name>` from a checkout with the
Claude Code CLI installed. The two plugin directories each contain their own
Codex and Claude manifests.

### Why is there no install.sh in this repository?

The repository deliberately keeps deployment ownership in the sibling
installer. Direct skill and plugin content remains independently inspectable
and can also be installed from its directory by compatible CLIs.

## Contributing

Keep each skill self-contained, preserve the plugin/direct-skill ownership
rules in [AGENTS.md](AGENTS.md), and run `python3 -m pytest tests -v` before
opening a pull request. Changes to prompt-only content should include a clear
description of the behavior or policy they improve.

## License

This project is licensed under the [MIT License](LICENSE.md).

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.

## Global instruction assembly

`scripts/global_instructions.py` provides `render_instructions` and
`write_instructions` to combine selected instruction texts into one global
Markdown file. The writer replaces only owned blocks and preserves unrelated
user instructions.

Build selected policies with Python 3.11 or newer (standard library only):

```bash
python3 scripts/global_instructions.py --skills v2:workflow,v2:commits,v2:worktree,v2:docs,v2:testing --runtime codex --config-home ~/.codex
```

Accepted parameters: `--list`, `--skills` (comma-separated, family-qualified
when ambiguous), `--source-root`, `--output`, `--runtime`, `--config-home`, and
`--bundle-dir`. An empty `--skills ''` clears managed selections while retaining
personal instructions. `--output` writes an explicit destination; otherwise
`--runtime` and `--config-home` resolve the native file. `--bundle-dir` creates
a transport bundle for isolated evaluation instances. `--list` prints available
policy names. Harbor uses the same builder to package one document
per job, then places it in each trial's native global file. Baselines clear
native instruction and skill surfaces; task prompts and judges are unchanged.
Generated documents contain a global overview, the selected policy list, and
one section per source with its original metadata and complete body. Markdown
headings are nested while fenced examples remain verbatim. Source files and
judge definitions are never rewritten by assembly.
The same CLI supports Codex, Claude, Grok, Cline, OpenCode, Cursor, and the
Local/Qwen, OpenRouter, and NVIDIA Codex homes (their ACC aliases are accepted).
Codex destinations receive at least a 1 MiB document budget to accommodate the
full combined instructions. ACC installs the tool as `acc-build-instructions`.
`instruction_path` resolves Codex's `AGENTS.md` and Claude's `CLAUDE.md`
under an explicit instance home, or `CODEX_HOME` / `CLAUDE_CONFIG_DIR`.

## Log reading and debugging

The existing read-logs-first policy is now [`debug_logs`](programming_prompt_rewritten_with_evals/prompts/programming-skills/debug_logs/SKILL.md). The separate [`debug`](programming_prompt_rewritten_with_evals/prompts/programming-skills/debug/SKILL.md) skill guides evidence-based diagnosis, reproduction, focused repair and verification. Select either through `run_benchmark.sh --skills debug_logs` or `--skills debug`; they remain independently selectable global instructions.

Dedicated debug scenarios use `verifier/check_debug_behavior.py --repo PATH --cases CONTRACT.json --output REWARD.json`. It executes immutable public-call sequences with fresh module state and a per-sequence timeout. Harbor includes this functional judge alongside the semantic `debug` judge only on dedicated cases; missing contracts and execution failures cannot silently pass.

The benchmark accepts `--suite coding`, `--suite debug`, or `--suite all` to select task families, and `--tasks NAME[,NAME]` to narrow the selected family. Dedicated debugging prompts are maintained separately under `evals/debug-prompts/`.

The dedicated debug cases cover UTC offset/date rollover (`debug-clock`), tenant-aware cache results (`debug-catalog`), and rejected reservations preserving stock (`debug-stock`). Each has an intentionally broken seed, an independent reference repair, and cumulative public behavior sequences in `evals/debug-cases/`.

Before materialization, `python3 evals/verify_debug_fixtures.py` (from the rewritten-prompt project) verifies every broken seed against saved public calls, compares its actual output byte-for-byte with the original `log/failure.log`, and checks each reference repair twice with fresh state. `--refresh-logs` explicitly regenerates captures after an intentional fixture change. Agents receive these files in the project-root `.log/` directory; judges retain an independent original under `tests/task-logs/`. The `debug` skill contains no scenario names, paths or hints.

With no `--suite` or `--tasks`, selecting only `debug` runs dedicated repair cases. Selecting `debug` alongside coding skills runs both task families in one wrapper invocation; each harness uses isolated coding and debugging jobs with only the applicable skills and judges. A default all-skill run includes both families. Baselines use the identical tasks and judges while omitting skill instructions.

Other-skill runs keep the existing coding task pool and do not materialize or execute the new debugging cases. Explicit debug tasks require `debug` in `--skills`; incompatible suite/task selections fail before account preflight or Docker work. `sync_tasks.sh [TASK ...]` can materialize a selected set; no arguments materializes both canonical families.
