---
name: general-programming-guidelines
description: >-
  v1.8.3 — Mandatory engineering workflow and coding standards for every software task:
  implementation, debugging, review, testing, and refactoring.
---

# General Programming Guidelines

## Start here — the non-negotiables

Before you do anything else on a task that edits a repository:

1. **Create a git worktree and branch first (Step 1 below). Do it before your
   first file edit — no exceptions.** Not "later", not "if it seems worth it".
   The very first tool call that changes state is `git worktree add`.
2. Run the whole task through the numbered **Work Loop** in order.
3. Do not report the task done until the **Definition of Done** checklist passes.

If you skip the worktree step you have already failed the task, even if the code
is correct.

## Work Loop

Run every software task through these numbered steps in order. Do not skip a
step, and do not report the task done until Step 8 passes.

1. **Create an isolated worktree (do this first, before any edit).** For any
   task that will modify a repository, you MUST be on a dedicated worktree
   branch before your first file edit. This keeps the user's checkout clean and
   makes the work trivially reviewable and reversible. Read-only inspection may
   precede this, but the moment you intend to edit, stop and set up the
   worktree.

   **Worktree location (keep them out of the repo).** Do not create the worktree
   inside the repository you are editing — that nests a git worktree inside a git
   repo and clutters the user's checkout. Put every worktree under one *shared
   worktree store*: a `./worktrees/` directory inside the parent folder that holds
   the repository family. When the repos live under a `projects/` folder, they all
   share `projects/.worktrees/` (an absolute path under that parent). Concretely,
   from inside the target repository:

   ```bash
   git rev-parse --show-toplevel                    # confirm you are in a git repo
   git worktree add ../.worktrees/<repo>-wt-<task> -b <task-branch>   # shared store, not in-repo
   cd ../.worktrees/<repo>-wt-<task>                # do ALL edits here
   ```

   Do this in every repository the task will touch — when a task spans multiple
   repos, create a worktree on EACH one, not only the primary repo. Give every
   worktree the SAME task/branch name (e.g. `<repo>-wt-<task>` with branch
   `<task-branch>` in each repo) so the related changes stay grouped and easy to
   review. Do all edits for a given repo inside that repo's own worktree, and
   keep every original checkout unchanged. Only work directly in a current
   checkout when the user *explicitly* tells you to (e.g. "work in the current
   checkout / no worktree"). If a worktree genuinely cannot be created (not a
   git repo, or a hook/tool blocks it), say so explicitly and get agreement
   before editing in place — never silently fall back to editing the live
   checkout.

   **Name the worktree and branch with a type prefix.** Use a conventional
   commit-style type as the prefix (`fix/`, `feat/`, `docs/`, `refactor/`,
   `test/`, `chore/`, `build/`, `perf/`, `ci/` …) followed by the feature or
   task it addresses, e.g. `fix/worktree-policy` or `feat/model-monitor`.
   Apply the SAME `type/feature` name to both the branch and the worktree
   directory (so `<repo>-wt-<type-feature>` and branch `type/feature` match),
   keeping related changes grouped and easy to identify across every repo a
   task spans.
2. **Capture scope.** Preserve the user's exact scope, paths, data, wording,
   and constraints. Do not normalize, reorder, truncate, or reinterpret input
   unless asked.
3. **Inspect first.** Read the codebase before editing — prefer `rg` /
   `rg --files`. Learn the existing patterns, logging utility, tests,
   manifests, and deployment flow your change must match.
4. **Plan and write tests first.** For behavior changes, shared helpers,
   installers, regressions, refactors, and logging changes, add or update
   focused tests before changing code when the repo has a practical test path.
   For docs-only or prompt-only edits, state and run direct verification
   instead of inventing noisy tests.
5. **Implement.** Satisfy the requested scope using project-local helpers and
   conventions.
6. **Instrument and document the code you just wrote.** Logging (see *Logging and
   Diagnostics*) and comments/docstrings (see *Documentation*) are part of the
   change, not optional polish. Cover new action paths, state transitions,
   boundary failures, and external calls with logs; document new public
   functions, helpers, and non-obvious behavior including parameters. If one
   pass is error-prone, fall back to (a) make it work, (b) add logging,
   (c) add docs — but the task is not done until all three exist.
7. **Verify.** Run the relevant tests plus configured lint/type/build, read the
   logs the change should now emit, and iterate until clean.
8. **Self-check and report.** Walk the *Definition of Done* checklist; reopen
   any unchecked item, then report what changed and how it was verified. Do not
   stop at a proposal unless the user asked for one.

If the user challenges completeness or asks whether a repository follows these
guidelines, do not stop at "unproven": run a bounded compliance audit,
fix concrete gaps that are in scope, and report the evidence and remaining
risks.

## Definition of Done

Every item must be checked before reporting completion; an incomplete checklist
sends you back to the relevant Work Loop step.

- [ ] All edits were made on a dedicated git worktree branch (Work Loop Step 1),
      not the user's live checkout — unless the user explicitly waived it.
- [ ] The code implements the exact requested scope, with no unrelated edits.
- [ ] New or changed action paths, state transitions, boundary failures, and
      external calls are logged through the existing centralized logger,
      honoring the stdout/stderr and spam exceptions below.
- [ ] New or changed public functions, reusable helpers, scripts, and non-obvious
      behavior are documented including their parameters, honoring the
      static-file and compatibility exceptions below.
- [ ] Tests were added or updated for the change and pass; existing relevant
      tests still pass.
- [ ] The diff was reviewed for duplication, dead code, unused imports, debug
      spam, and accidental behavior changes.
- [ ] The final report states what changed, how it was verified, and any
      remaining risks.

## Scope and Safety

- Treat the user's files, config, sessions, secrets, and desktop state as
  production data.
- Stay within the request; do not reformat, refactor, or "fix" unrelated files.
- Preserve existing values and project defaults. Never reset user config to
  placeholders such as `0`, empty strings, or generic models.
- Keep installers, migrations, generators, and setup scripts idempotent and
  non-destructive; preserve root-optional paths where the repo supports them.
- Before touching user-global state — installed skills, generated wrappers,
  desktop config, services, installer output — test in a sandbox or temporary
  home when feasible; deploy for real only after focused tests pass.
- For GUI/session changes, use command-line live settings and never automate
  logout, reboot, `gnome-shell --replace`, or shell-kill commands. The only
  sanctioned Shell reload is the in-place X11 run-dialog reload
  (`xdotool` `Alt+F2 r`) used to activate edited extension code.
- When a commit is requested, commit in the worktree you are already working on —
  never in the user's live checkout. When the change spans multiple repositories,
  commit separately in each repo's own worktree. Commit one self-contained
  feature at a time:
  stage only that feature's logical hunks, keep unrelated local changes out, and
  complete its commit before starting the next feature's.
  **Format each commit message as `<type>(<worktree-name>): <summary>`**, where
  `<type>` is the conventional type (the same prefix used for the worktree/branch
  name) and `<worktree-name>` is the feature portion of that name — e.g. for a
  worktree/branch named `fix/worktree-policy` the message is
  `fix(worktree-policy): keep worktrees in the shared family store`. Do not commit
  unless the user asked, and never ask the user to commit for you when they
  instructed you to commit.
- Use a dedicated Git worktree and a new branch for every task by default (this
  is Work Loop Step 1 — set it up before your first edit, not afterwards). Keep
  the current checkout unchanged. Work in the current checkout only when the
  user explicitly requests it.

## Design and Structure

- Reuse project-local helpers, conventions, logging, tests, and manifests
  before adding new abstractions. Add an abstraction only when it removes real
  complexity, prevents drift, or matches an existing local pattern.
- When adding a new variant of something that already exists (a sibling command,
  launcher, wrapper, endpoint, or agent kind), route it through the SAME shared
  path the existing variants use instead of writing a fresh standalone
  implementation. Find how the closest working sibling is wired end to end and
  extend that mechanism (add the case/entry/parameter); do not fork a parallel
  copy that re-implements argument parsing, prompt/input handling, flag
  selection, or dispatch. A standalone re-implementation looks similar but
  silently drops the shared behaviors (multi-argument/quoting handling, default
  flags, option parsing), so it breaks the moment input differs from the trivial
  case. Standardize on the shared path; never ship duplicated code that only
  works for the simplest input.
- After adding or changing a command/flag surface, verify it with non-trivial
  input — multi-word arguments, each accepted flag, and the no-argument/default
  path — not just a single happy-path token, since parsing bugs hide behind the
  simple case.
- Keep modules and components single-purpose; split by feature, not by file
  size alone.
- Keep data describing what the program operates on in config, manifests, or
  data files. Never duplicate lists, ordering, or catalogs in code when a data
  source already owns them.
- Validate required environment variables, URLs, paths, credentials, and system
  settings before installing packages, mutating config, or starting long setup
  work.
- When adding runtime modules, update install scripts, copy lists, manifests,
  existence checks, package data, and deployment tests so installed copies do
  not fail on missing imports.

## Documentation

- Documenting the code you add or change is part of the change; the Work Loop
  self-check fails without it.
- Document public/exported functions, reusable helpers, scripts, non-obvious
  behavior, and compatibility surfaces when that helps maintainers. New
  reusable modules or scripts get a concise top-level comment naming purpose,
  major components, and usage when non-obvious.
- Do not force function-doc, logging, or API-style comments into static prompt
  files, generated data, string constants, vendored code, or plain text.
- Do not delete unused-looking CLI flags, aliases, exports, wrappers, or
  parameters before checking whether they are compatibility surfaces; document
  intentional compatibility instead.
- Update README/docs only when installation, commands, behavior, architecture,
  logging, configuration, troubleshooting, or module layout changes — no docs
  churn for private implementation details.

## Logging and Diagnostics

- Logging the code you touch has the same standing as tests and docs; the
  self-check fails without it. The exceptions below bound where coverage is
  unnecessary — they never license skipping it elsewhere.
- Every project routes through **one centralized logging module**. Reuse the
  existing logger before adding any new one, and never redefine `log()` /
  `log_info()` / `log_warning()` / `log_error()` inside a feature file — that
  logic lives in the one module. In Python, one logging module per project that
  every other module imports, with a standard call-tracing decorator: each
  record carries the function's file and name, arguments on entry, return value
  on exit.
- For Bash and other shell scripts, centralization means
  one sourced logging helper from the project or installer framework. Feature scripts
  source the shared helper and do not hardcode ad-hoc log helpers such as local `log()`,
  `log_info()`, `info()`, `warn()`, or `err()` implementations unless that file
  *is* the centralized helper. Keep
  installer-compatible status and errors on stderr;
  stdout must remain reserved for machine-readable output, command
  substitution, filters, probes, and documented CLI output.
- When the user reports broken or misbehaving software, read the relevant logs
  before forming a hypothesis: repo `.log/`, journald/systemd units, tracker
  logs, or the app's documented sink.
- Store repository-generated file logs under repo-root `.log/` (gitignored).
  Do not scatter log files into the repo root, `data/`, `/tmp`, or component
  folders.
- Make sinks environment-aware but still routed through the one module:
  journald/systemd or GNOME Shell logging for services/extensions where that is
  canonical; stderr for installer-compatible contracts; file-only logging for
  TUIs whose terminal output must stay clean; mirror to `.log/` only when
  useful and safe.
- Preserve stdout/stderr contracts for status bars, command-substitution
  helpers, CLI filters, heredocs, probes, and installers. Logging must not
  change externally observed output unless that change is intentional and
  tested.
- Coverage means action paths, state transitions, boundary failures, external
  calls, and meaningful decisions are observable. Pure predicates, parsers,
  formatters, recursive generators, hot loops, logging primitives, and
  generated shims may rely on caller-level logs.
- Avoid log spam in polling ticks, tight filters, and recursive traversal.
  Never log secrets, tokens, or sensitive payloads.
- Logging in hooks, installers, and setup scripts is best-effort and never
  aborts user workflows; fall back to stderr, a null handler, or no-op stubs.

## Errors and Warnings

- Handle critical errors at the right boundary with clear user-facing messages
  and technical logs.
- Replace silent broad exception swallowing with specific handling, logged
  context, and graceful fallback.
- Fix warnings; do not hide them with comments.

## Testing and Verification

- Add focused tests for bugs, validation guards, logging utilities, deployment
  copy lists, manifest changes, and refactoring extractions.
- For installed Python entrypoints or helper modules, add a deployment contract
  test verifying project-local imports appear in installer copy lists or
  package manifests.
- Where tests exist, run the relevant ones before and after risky refactors or
  behavior changes to prove behavior was preserved.
- If adding a shared dependency (such as `log`) to a sourced shell module,
  update isolated tests and stubs so tests exercise the real dependency shape.
- Verify target-system conventions in installer work: APT source extensions,
  service names, desktop entry paths, executable names, copied helper files.
- Run configured lint/type/build commands only when the repo already provides
  them; do not install new tools ad hoc to satisfy a checklist.
- For larger changes, review the diff for duplication, dead code, unused
  imports, misleading indentation, obsolete tests, config hardcoding, and
  accidental behavior changes.
- For prompt edits derived from an audit or improvement list, verify each
  listed issue maps to prompt text and remove duplicated or contradictory
  wording.

## Frontend and API Work

- UI work uses semantic markup, accessible controls, sufficient contrast,
  responsive layout, keyboard support, and the repo's design system.
- Keep component state minimal and scoped; global state only when shared
  behavior requires it.
- API work uses the repo's HTTP/client pattern, handles auth and timeouts,
  exposes loading/error states, and mocks external dependencies in tests.

## Python Supply-Chain Protection

When adding Python code or initializing a Python project, invoke the
`init-project` skill for supply-chain protection with UV by Astral as the
package manager, and hold every Python dependency change to these rules:

- Require `[tool.uv]` with `exclude-newer = "24 hours"` in `pyproject.toml`;
  uv enforces the rolling cutoff natively, shielding against
  newly-published malicious releases.
- Never let plain `pip` resolve dependencies directly; when pip compatibility
  is required, go through hash-locked exports
  (`uv export --format requirements.txt` with hashes) so installs verify
  integrity.
- Document any emergency override of the delay or hash checks as an explicit,
  auditable, opt-in action — never a silent default.

## Packages, Builds, and Run Instructions

- Add or update package/build/run instructions only when dependencies, scripts,
  setup, commands, environment variables, or deployment behavior changed.
- When package metadata changes, include install, test, type/lint, build, and
  production verification commands matching the repo's actual tooling and the
  supply-chain policy above.

## Tool Discipline

- Execute needed terminal commands with your tools; do not print commands for
  the user to run.
- Do not repeat a diagnostic command unless rerunning proves a change, verifies
  idempotence, or collects new information.
- If a command fails or returns empty, try one sensible alternative, then
  explain the blocker instead of looping.
