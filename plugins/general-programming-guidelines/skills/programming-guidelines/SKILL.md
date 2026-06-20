---
name: programming-guidelines
description: >-
  Mandatory general engineering workflow and coding standards. Use for every
  software task, including implementation, debugging, review, testing, and
  refactoring.
---

# General Programming Guidelines

## Work Loop

- Preserve the user's exact scope, paths, data, wording, and constraints. Do not
  normalize, reorder, truncate, or reinterpret input unless asked.
- Inspect the codebase before editing. Prefer `rg`/`rg --files`; understand
  existing patterns, tests, manifests, and deployment flow.
- Plan before changing code. For behavior changes, shared helpers, installers,
  regressions, refactors, and logging changes, add or update focused tests first
  when the repo has a practical test path. For docs-only or prompt-only edits,
  state and run direct verification instead of inventing noisy tests.
- Finish the requested work end to end: implement, verify, fix failures, and
  report what changed. Do not stop at a proposal unless the user asked for one.

## Scope and Safety

- Treat the user's files, config, sessions, secrets, and desktop state as
  production data.
- Stay within the request. Do not reformat, refactor, or "fix" unrelated files.
- Preserve existing values and project defaults; never reset user config to
  placeholders such as `0`, empty strings, or generic models.
- Keep installers, migrations, generators, and setup scripts idempotent and
  non-destructive. Preserve root-optional paths where the repo supports them.
- Before changing user-global state, installed skills, generated wrappers,
  desktop config, services, or installer output, test in a sandbox or temporary
  home when feasible. Deploy to the real environment only after focused tests
  pass.
- For GUI/session changes, use command-line live settings where possible and do
  not automate shell reloads, logout, reboot, `gnome-shell --replace`, or
  shell-kill commands.
- Do not commit unless explicitly asked. If committing is requested, stage only
  your own logical hunks and keep unrelated local changes out of the commit.

## Design and Structure

- Reuse project-local helpers, conventions, logging, tests, and manifests before
  adding new abstractions.
- Add an abstraction only when it removes real complexity, prevents drift, or
  matches an existing local pattern.
- Keep modules and components single-purpose. Split behavior by feature, not by
  arbitrary file size alone.
- Keep data that describes what the program operates on in config, manifests, or
  data files. Do not duplicate lists, ordering, or catalogs in code when a data
  source already owns them.
- Validate required environment variables, URLs, paths, credentials, and system
  settings before installing packages, mutating config, or starting long setup
  work.
- When adding runtime modules, update install scripts, copy lists, manifests,
  existence checks, package data, and deployment tests so installed copies do not
  fail on missing imports.

## Documentation

- Document public/exported functions, reusable helpers, scripts, non-obvious
  behavior, and compatibility surfaces when that helps maintainers.
- New reusable modules or scripts should have a concise top-level comment naming
  the file purpose, major components, and usage when non-obvious.
- Do not force function-doc, logging, or API-style comments into static prompt
  files, generated data, string constants, vendored code, or plain text content.
- Do not delete unused-looking CLI flags, aliases, exports, wrappers, or
  parameters until you check whether they are compatibility surfaces; document
  intentional compatibility instead.
- Update README/docs only when installation, commands, behavior, architecture,
  logging, configuration, troubleshooting, or module layout changes. Avoid docs
  churn for private implementation details.

## Logging and Diagnostics

- When the user reports broken, failing, crashing, or misbehaving software, read
  relevant logs before forming a hypothesis: repo `.log/`, journald/systemd
  units, tracker logs, or the app's documented log sink.
- Prefer the existing centralized logger. If missing and runtime logging is
  needed, add the smallest shared utility with `verbose`, `debug`, `info`,
  `warn`, and `error` levels, timestamps, context, idempotent setup, and no
  duplicate handlers.
- Store repository-generated file logs under repo-root `.log/` and ensure
  `.log/` is gitignored. Do not scatter log files into the repo root, `data/`,
  `/tmp`, or component folders.
- Make sinks environment-aware: use journald/systemd or GNOME Shell logging for
  services/extensions when that is the canonical sink; use stderr for
  installer-compatible contracts; use file-only logging for TUIs where terminal
  output would corrupt the UI; mirror to `.log/` only when useful and safe.
- Preserve stdout/stderr contracts for status bars, command-substitution helpers,
  CLI filters, shell heredocs, probes, and installers. Logging must not change
  externally observed output unless that behavior change is intentional and
  tested.
- Logging coverage means action paths, state transitions, boundary failures,
  external calls, and meaningful decisions are observable. Pure predicates,
  parsers, formatters, recursive generators, hot loops, logging primitives, and
  generated shims may be covered by caller-level logs instead.
- Avoid log spam in polling ticks, tight filters, and recursive traversal.
- Logging in hooks, installers, and setup scripts must be best-effort and never
  abort user workflows; fall back to stderr, a null handler, or no-op stubs.
- API clients should log request lifecycle, cache hits, retries, response/failure
  classes, parse errors, and network errors, while never logging secrets, tokens,
  or sensitive payloads.

## Errors and Warnings

- Handle critical errors at the right boundary with clear user-facing messages
  and technical logs.
- Replace silent broad exception swallowing with specific exception handling,
  logged context, and graceful fallback.
- Fix warnings; do not hide them with comments.

## Testing and Verification

- Add focused tests for bugs, validation guards, logging utilities, deployment
  copy lists, manifest changes, and refactoring extractions.
- When tests already exist, run relevant tests before and after risky refactors
  or behavior changes to prove behavior was preserved.
- If adding a shared dependency such as `log` to a sourced shell module, update
  isolated tests and stubs so tests exercise the real dependency shape.
- Verify target-system conventions in installer work: APT source extensions,
  service names, desktop entry paths, executable names, and copied helper files.
- Run configured lint/type/build commands only when the repo already provides
  them. Do not install new tools ad hoc just to satisfy a checklist.
- For larger changes, review the diff for duplication, dead code, unused imports,
  misleading indentation, obsolete tests, config hardcoding, and accidental
  behavior changes.
- For prompt edits derived from an audit or improvement list, verify each listed
  issue maps to prompt text and remove duplicated or contradictory wording.

## Frontend and API Work

- For UI work, use semantic markup, accessible controls, sufficient contrast,
  responsive layout, keyboard support, and the repo's design system.
- Keep component state minimal and scoped; use global state only when shared
  behavior requires it.
- For API work, use the repo's HTTP/client pattern, handle auth and timeouts,
  expose loading/error states, and mock external dependencies in tests.

## Python Supply-Chain Protection

When adding Python or initializing a Python project, invoke the `init-project`
skill for supply-chain protection with UV by Astral.

- Require `[tool.uv]` with `exclude-newer = "24 hours"`; uv enforces the rolling
  cutoff natively.
- Never let plain `pip` resolve dependencies directly; use hash-locked exports.
- Document emergency overrides as explicit, auditable, opt-in actions.

## Packages, Builds, and Run Instructions

- Add or update package/build/run instructions only when dependencies, scripts,
  setup, commands, environment variables, or deployment behavior changed.
- When package metadata changes, include install, test, type/lint, build, and
  production verification commands that match the repo's actual tooling and the
  supply-chain policy above.

## Tool Discipline

- Execute needed terminal commands with tools; do not print commands for the user
  to run.
- Do not repeat a diagnostic command unless rerunning proves a change, verifies
  idempotence, or collects new information.
- If a command fails or returns empty, try one sensible alternative, then explain
  the blocker instead of looping.
