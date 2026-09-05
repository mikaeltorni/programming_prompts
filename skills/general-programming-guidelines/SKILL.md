---
name: general-programming-guidelines
description: >-
  v1.14.0 — Mandatory engineering workflow and coding standards for every software task:
  implementation, debugging, review, testing, and refactoring.
---

# General Programming Guidelines

## Project instructions first

Before applying these guidelines, read and respect the repository's own
`AGENTS.md` and `CLAUDE.md` when either file is present. Those project files
take precedence over conflicting generic agent defaults and over conflicting
parts of this skill for project-specific ownership, routing, deployment, and
local policy. Where this skill and those files agree — including commit, merge,
and reload delivery — follow both. Do not skip this skill; load it after
honoring the project files.

## Skill ownership

The independently selected `commits` skill owns Feature boundaries, commit
sequencing, and commit verification. The `worktree` skill owns isolation,
project/instance paths, branch policy, merging, and consumer reapplication.
The `linux-configuration` skill owns Linux desktop and session deployment,
reload and reboot safety, clean-install compatibility, and the root-optional
(sudo-free) installer pattern — load it for any GNOME, gsettings, systemd user
unit, or `install.sh` change.
Follow those selected skills alongside this engineering workflow; this file
does not duplicate their policies. ACC's installer baseline enables all three.
Use `acc pp enable --both --skill general-programming-guidelines,v2:commits,v2:worktree`
to apply them and `acc pp status --skill general-programming-guidelines,commits,worktree --check`
to verify the selection. Changes to skill source require reapplication through
that selector; existing conversations may retain earlier instructions.

## Work Loop

1. **Capture scope.** Preserve the user's exact paths, data, wording, and
   constraints. Do not normalize or reinterpret input unless asked.
2. **Inspect first.** Read the codebase, existing tests, centralized logger,
   manifests, and deployment flow before editing.
3. **Plan and verify the baseline.** For behavior changes with a practical
   test path, add focused regression tests before implementation. For docs or
   prompt edits, state and run direct verification instead of noisy tests.
4. **Implement.** Follow project helpers and conventions, preserving existing
   behavior outside the requested scope.
5. **Instrument and document.** Cover new actions, transitions, boundaries,
   and external calls through the centralized logger. Document public helpers
   and non-obvious behavior, including parameters, subject to the exceptions below.
6. **Verify.** Run relevant tests and configured lint/type/build checks, inspect
   relevant logs, and resolve failures. Review the diff for duplication, dead
   code, unused imports, debug spam, and accidental changes.
7. **Deliver and self-check.** Follow the selected delivery skills and project
   deployment instructions. Verify the actual consumer, then report what
   changed, the evidence, and any remaining limitations.

If the user challenges completeness, run a bounded compliance audit, fix
concrete gaps in scope, and report the evidence and remaining risks.

## Definition of Done

- [ ] The change implements the requested scope with no unrelated edits.
- [ ] Applicable selected skills and project instructions were followed.
- [ ] Changed action paths and boundaries use the centralized logger, honoring
      the stdout/stderr and spam exceptions below.
- [ ] Public helpers and non-obvious behavior are documented, honoring the
      static-file and compatibility exceptions below.
- [ ] Relevant tests or direct prompt/document checks pass.
- [ ] The diff was reviewed for accidental changes and maintainability.
- [ ] Consumers are verified and the final report states evidence and limits.

## Scope and Safety

- Treat the user's files, config, sessions, secrets, and desktop state as
  production data.
- Stay within the request; do not reformat, refactor, or "fix" unrelated files.
- Preserve existing values and project defaults. Never reset user config to
  placeholders such as `0`, empty strings, or generic models.
- Keep installers, migrations, generators, and setup scripts idempotent and
  non-destructive.
- **Never add CI to a repository unless the user explicitly asks for it.** Do
  not create `.github/workflows/`, GitHub Actions, or any other CI/CD pipeline,
  and do not add a CI or build-status badge to a README. Verification runs
  locally through the Work Loop (tests, lint, type, build) — a hosted pipeline
  is not a substitute and is not a deliverable. When a repository already ships
  CI, leave it exactly as it is: keep it working, do not delete it to satisfy
  this rule, and do not expand it. Propose CI under pending user actions
  instead of adding it unprompted.
- Before touching user-global state — installed skills, generated wrappers,
  desktop config, services, installer output — test in a sandbox or temporary
  home when feasible; deploy for real only after focused tests pass.
- For desktop, session, service, or installer changes, follow the
  `linux-configuration` skill rather than any rule restated here; it owns silent
  deployment, reload and reboot safety, clean-install compatibility, and the
  root-optional installer pattern.

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
- **Keep non-visual automated tests silent.** Tests must not open visible
  GUI windows, terminal emulators (kitty, gnome-terminal, xterm, …), dialogs,
  or other desktop surfaces that interrupt the user, unless the run is a
  deliberate visual or screenshot check. Mock or inject process spawn
  (`Popen`, `subprocess.run`, terminal launchers), window managers, and GUI
  toolkits so the desktop stays undisturbed; prefer asserting on captured
  argv/env/kwargs over live windows. Keep such side effects fully stubbed or
  backgrounded — never leave a real console flashing on every test run.
- **Patch mocks at the defining module.** When code is extracted and
  re-exported, monkeypatch the name the function body resolves in its own
  module globals (the defining module), not only a re-export surface. A
  re-export-only patch is a no-op: the real launcher still runs and can open
  windows while the test's capture list stays empty.

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
