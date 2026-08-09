# Code-Writing Rules Comparison

## Purpose — What This Document Compares

This document compares two implementations of the same OpenRouter ping MVP:

1. **Unstaged iteration without the Programming Prompt** — the current `master`
   working tree in `/home/mk/projects/chess_llm_analysis_tools`.
2. **OpenRouter worktree with the Programming Prompt** — the clean
   `feat/openrouter-mvp` worktree in
   `/home/mk/projects/.worktrees/chess_llm_analysis_tools-wt-feat-openrouter-mvp`.

The comparison distinguishes three kinds of evidence:

- **Observed difference** — directly present in the files or Git history.
- **Implied writing rule** — a consistent engineering preference inferred from
  the implementation.
- **Prompt-aligned rule** — an implementation choice that directly matches a
  rule in the Programming Prompts guidance.

## Executive Summary — Minimal Script Versus Production-Shaped Feature

The unstaged, no-prompt iteration follows a **minimal runnable script** rule. It
keeps the whole feature in `main.py`, accepts a prompt from the command line,
adds an environment example, limits response tokens, and avoids a test/build
framework.

The prompted worktree follows a **production-shaped feature** rule. It creates
an installable `src/` package, separates the API operation from the CLI,
injects the client for testing, adds logging and error boundaries, includes a
focused unit test, declares a build backend, and records supply-chain controls.

The prompted worktree is more maintainable and reproducible, but it is not
strictly better in every respect. It removes the command-line prompt argument,
removes the explicit `max_tokens` cap and OpenRouter attribution headers, does
not include an `.env.example`, and still misses several rules from its own
prompt.

## Compared Repository States — Exact Scope

### Unstaged Iteration — No Programming Prompt

- Branch: `master`
- HEAD: `8353f01786bd67263c41cb01969da8f8f3471613`
- Working state: one modified file and four untracked files
- Changed/new files:
  - `README.md`
  - `.env.example`
  - `main.py`
  - `pyproject.toml`
  - `uv.lock`
- Effective delta from HEAD: 453 added lines

### OpenRouter Worktree — With Programming Prompt

- Branch: `feat/openrouter-mvp`
- HEAD: `c4bb1c20e328765844d9a1c05c04f4012c57fcf9`
- Working state: clean
- Feature commit: `feat(...): add OpenRouter model ping MVP`
- Changed/new files:
  - `README.md`
  - `pyproject.toml`
  - `requirements.txt`
  - `src/chess_llm_analysis_tools/__init__.py`
  - `src/chess_llm_analysis_tools/ping.py`
  - `tests/test_ping.py`
  - `uv.lock`
- Committed delta from the common pre-feature state: 790 added lines

### Common Baseline — Why the Comparison Is Fair

The prompted feature commit branches from `629b2ce`. It was merged and then
reverted on `master`; the current unstaged files therefore form a separate
implementation on top of the restored pre-feature content. The useful
comparison is:

- prompted feature commit versus the common pre-feature tree;
- current unstaged files versus the restored pre-feature tree; and
- the two resulting implementations directly against each other.

## Rule Matrix — Writing Preferences Visible in the Code

| Rule area | Without prompt: unstaged iteration | With prompt: OpenRouter worktree |
| --- | --- | --- |
| Project shape | One top-level script | Installable `src/` package |
| Responsibility split | CLI, configuration, API call, and output in `main()` | API call in `ping_model()`; CLI orchestration in `main()` |
| Testability | Real client constructed and called inside `main()` | Client passed into `ping_model()` for a fake-client unit test |
| Automated tests | None | One focused pytest unit test |
| Logging | No logging | Module logger and request lifecycle messages |
| Error handling | Missing key handled; API errors propagate; empty content prints blank | Missing key handled; API failures mapped to exit 1; empty content rejected |
| Documentation | Module docstring and README usage | Module/function docstrings and README usage |
| Type posture | `main() -> int` | Future annotations plus typed public helper and `main()` |
| CLI input | Optional positional prompt | Prompt supplied through `LUNA_PROMPT` |
| Packaging | Script target points at top-level `main` | Hatchling build and package entry point |
| Dependency policy | `uv.lock` only; no repository-level UV policy | UV cutoff, hash settings, lockfile, and hashed pip export |
| Secret guidance | `.env.example`; key validation | README warning; key validation |
| API request bounds | Explicit `max_tokens=200` | No explicit output-token cap |
| OpenRouter metadata | `HTTP-Referer` and `X-Title` headers | No optional attribution headers |

## Architecture Rules — How Code Is Divided

### Without Prompt — Prefer the Smallest Executable Surface

The unstaged implementation places all behavior in a single 45-line `main.py`.
Its implied rules are:

- use one file while the MVP is small;
- avoid abstractions that are not necessary to make the command run;
- construct dependencies at the point of use;
- expose the file directly as the console-script target.

This is concise, but the API behavior cannot be tested independently without
patching `OpenAI` or exercising `main()`.

### With Prompt — Separate Reusable Behavior From the CLI Boundary

The worktree places runtime code under `src/chess_llm_analysis_tools/` and
splits the feature into:

- `ping_model(client, model, prompt)` for the API operation;
- `main()` for environment loading, client construction, printing, and exit
  codes;
- `tests/test_ping.py` for the behavior contract.

The implied rule is: **put reusable logic behind a small function with explicit
inputs, and keep process concerns at the entry-point boundary**. Passing the
client into `ping_model()` is dependency injection and allows a network-free
test.

## Interface Rules — How Users Supply Configuration

### Without Prompt — Prefer Explicit Command-Line Input

The unstaged CLI uses `argparse` and accepts an optional positional prompt:

```text
uv run python main.py "Say hello from a chess analysis agent."
```

Its default prompt is chess-specific, and the README shows both default and
custom-prompt usage. This is discoverable through `--help` and convenient for
one-off experiments.

### With Prompt — Prefer Environment-Based Runtime Configuration

The worktree reads all runtime choices from environment variables:

- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `LUNA_PROMPT`

This keeps `main()` small and suits automation, but removes CLI discoverability
and makes one-off prompt changes less ergonomic. Neither approach validates an
empty `OPENROUTER_MODEL` or an empty `LUNA_PROMPT` value.

## Function and Type Rules — Public Contracts

### Without Prompt — Type Only the Process Result

Only `main()` has an explicit return type. The module has a concise purpose
docstring, but there is no reusable public function to document or type.

### With Prompt — Type and Document Reusable Functions

The worktree adds:

- `from __future__ import annotations`;
- typed `client`, `model`, and `prompt` parameters;
- a `str` return type for `ping_model()`;
- docstrings on both `ping_model()` and `main()`;
- a package-level docstring in `__init__.py`.

This matches the prompted rule that public helpers, scripts, and non-obvious
behavior should have concise documentation.

## Testing Rules — What Is Treated as a Contract

### Without Prompt — Manual Minimal Confirmation

The unstaged iteration includes no test package or development dependency. Its
verification model is effectively:

- start the script;
- validate the missing-key path;
- make a real request when a key is available.

### With Prompt — Isolate the External Dependency

The worktree adds pytest and a fake OpenAI-compatible client. The test proves
that `ping_model()`:

- forwards the selected model;
- sends one user message containing the prompt;
- returns the response content;
- does not require a live API call.

This directly reflects the prompted rule to mock external dependencies in API
tests.

### Remaining Test Gaps in the Prompted Worktree

The single test covers only the helper's happy path. It does not verify:

- empty response content raises `RuntimeError`;
- missing `OPENROUTER_API_KEY` returns exit code 2;
- client/API failure returns exit code 1;
- model and prompt environment overrides are honored;
- the installed `luna-ping` entry point imports correctly;
- log output avoids secrets and prompt content.

## Logging and Diagnostic Rules — Operational Visibility

### Without Prompt — Keep Output Limited to Results and Errors

The unstaged script prints the model response to stdout and the missing-key
message to stderr. It has no lifecycle logging.

### With Prompt — Log External Calls and Boundary Failures

The worktree logs before and after the request and logs failures at the CLI
boundary. This makes the external operation visible and preserves the model
response on stdout.

The implementation does not fully satisfy the Programming Prompt's stronger
logging policy, which calls for a centralized project logging module and
standard call tracing. `LOGGER` is declared directly in `ping.py`, and no
shared logging module or tracing decorator exists.

## Error-Handling Rules — Failure Semantics

### Shared Rule — Validate Required Credentials Early

Both versions check `OPENROUTER_API_KEY` before constructing the client and
return exit code 2 with a user-facing stderr message when it is absent.

### Without Prompt — Allow API Failures to Surface Naturally

The unstaged version makes the request without a local exception boundary. It
also converts missing response content into an empty printed string. This is
simple, but callers receive an SDK traceback for API failures and cannot
distinguish empty content from a successful empty line.

### With Prompt — Convert Runtime Failures Into Stable CLI Results

The worktree rejects empty content with `RuntimeError`, catches failures in
`main()`, logs an error, and returns exit code 1. This creates a predictable CLI
contract.

However, `except Exception` conflicts with the prompted preference for specific
exception handling with logged context. It is defensible as a top-level CLI
boundary, but it loses error classification and does not include traceback
context.

## Dependency and Supply-Chain Rules — Reproducibility

### Without Prompt — Lock the Environment, Keep Metadata Minimal

The unstaged `pyproject.toml` declares only project metadata, an OpenAI lower
bound, and the console script. It commits a `uv.lock`, but does not declare a
build backend, development dependencies, a repository-level publication-age
cutoff, or pip hash enforcement.

The generated lockfile contains a 24-hour cutoff because of the environment in
which it was generated, but that is not a portable project policy without the
corresponding `pyproject.toml` settings.

### With Prompt — Make Supply-Chain Policy Explicit and Portable

The worktree adds all of the following:

- Hatchling as the build backend;
- `[tool.uv] exclude-newer = "24 hours"`;
- `[tool.uv.pip] require-hashes = true`;
- `[tool.uv.pip] verify-hashes = true`;
- a committed `uv.lock`;
- a hash-locked `requirements.txt` export for pip compatibility;
- pytest as a development dependency.

These files directly implement the Programming Prompt's Python initialization
and supply-chain rules.

### Dependency Version Difference — Declared Bounds Versus Resolution

- Unstaged lower bound: `openai>=1.99.0`
- Worktree lower bound: `openai>=1.68.0`
- Both lockfiles resolve OpenAI to `2.53.0`

The runtime dependency is therefore the same in the compared lockfiles, while
the worktree advertises compatibility with a wider range of older OpenAI SDK
versions.

## Secret-Handling Rules — Credentials and Examples

### Without Prompt — Provide a Copyable Environment Template

The unstaged iteration includes `.env.example` with a placeholder key and an
optional model override. Its error message explicitly suggests copying that
file or exporting the variable.

The code does not load `.env` automatically, so copying the file alone is not
sufficient unless another tool loads it. That makes the error guidance
partially misleading.

### With Prompt — State the Security Rule in Documentation

The worktree README says never to commit API keys and shows a placeholder in an
`export` command. It does not provide `.env.example` and does not suggest that a
local dotenv file is automatically supported.

Both versions correctly avoid hard-coded real credentials and avoid logging
the API key.

## API-Call Rules — Request Shape and Resource Bounds

### Without Prompt — Add OpenRouter Metadata and Bound Output

The unstaged client adds `HTTP-Referer` and `X-Title` headers and sets
`max_tokens=200`. These choices provide OpenRouter attribution and cap response
size/cost.

### With Prompt — Keep the Request Minimal and Validate the Response

The worktree sends only the model and message payload. It does not set an
explicit timeout or token cap, and it omits the optional OpenRouter headers. It
does validate that returned content is non-empty.

The lack of an explicit timeout is a notable gap because the Programming Prompt
states that API work should handle authentication and timeouts.

## Documentation Rules — User-Facing Behavior

### Without Prompt — Document Interactive Usage

The README explains setup, default execution, a positional custom prompt, and
the model override. The examples match `main.py`, except for the `.env.example`
copy suggestion noted above.

### With Prompt — Document Installed Command and Security Policy

The README explains `uv sync`, the installed `luna-ping` command, model and
prompt environment overrides, the API-key rule, and the 24-hour package cutoff.

It does not document the test command, build command, failure exit codes, or
production verification. Those omissions fall short of the prompt's package
metadata rule, which asks for install, test, type/lint, build, and production
verification commands matching the actual tooling.

## Behavioral Differences — Changes Beyond Writing Style

The two iterations are not behaviorally identical:

| Behavior | Unstaged iteration | OpenRouter worktree |
| --- | --- | --- |
| Default model | `openai/gpt-5.6-luna` | `openai/gpt-5.6` |
| Default prompt | Chess-analysis readiness sentence | Exact `luna online` request |
| Custom prompt source | Positional CLI argument | `LUNA_PROMPT` environment variable |
| Response limit | `max_tokens=200` | SDK/provider default |
| Empty response | Prints an empty line | Raises, logs, and exits 1 |
| API exception | Propagates | Logged and converted to exit 1 |
| OpenRouter headers | Referer and title included | Not included |
| Command | `python main.py` / `chess-llm-ping` | Installed `luna-ping` |

The model-ID difference is especially important: the worktree is titled as a
Luna ping but its default string does not include the `-luna` suffix used by the
unstaged iteration.

## Worktree Difference — Prompted Commit Versus Common Baseline

The clean OpenRouter worktree adds one committed feature with seven changed
files and 790 inserted lines:

### Runtime Package — 47 Lines

- Adds the package marker and package-level documentation.
- Adds a 46-line `ping.py` module.
- Establishes constants for the default model and OpenRouter base URL.
- Adds a reusable, typed, documented `ping_model()` function.
- Adds logging, empty-response validation, and CLI exit-code handling.

### Automated Test — 20 Lines

- Adds one fake-client pytest test.
- Verifies request construction and response extraction without network access.

### Packaging and Dependencies — 711 Lines

- Adds a 26-line `pyproject.toml` with package, build, UV, and dev settings.
- Adds a 437-line `uv.lock`.
- Adds a 248-line hash-locked `requirements.txt` export.

### README — 12 Lines

- Documents `uv sync` and `uv run luna-ping`.
- Documents model and prompt environment variables.
- Adds key-safety and dependency-cutoff guidance.

## Direct File Mapping — Worktree Versus Unstaged Tree

### Files Serving the Same Purpose but Written Differently

- `main.py` maps to `src/chess_llm_analysis_tools/ping.py`.
- Both versions modify `README.md`.
- Both versions add `pyproject.toml` and `uv.lock`.

### Files Only in the Unstaged Iteration

- `.env.example`
- `main.py` as a top-level runtime module

### Files Only in the Prompted Worktree

- `requirements.txt`
- `src/chess_llm_analysis_tools/__init__.py`
- `src/chess_llm_analysis_tools/ping.py`
- `tests/test_ping.py`

### Git-State Difference

- The worktree implementation is committed and its working tree is clean.
- The no-prompt implementation exists only as unstaged/untracked work on
  `master`.

This is a process difference as well as a code difference: the prompted result
is a self-contained feature commit, while the no-prompt result has not yet been
organized into a reviewable commit.

## Prompt Compliance Gaps — Rules the Worktree Still Misses

The prompted implementation shows strong prompt influence, but it does not
fully satisfy the Programming Prompts guidance:

1. **Centralized logging is missing.** Logging lives in the feature module
   instead of one project logging module with shared call tracing.
2. **Exception handling is broad.** `except Exception` is used rather than
   specific SDK or transport exceptions.
3. **API timeout handling is missing.** No explicit request/client timeout is
   configured or tested.
4. **Test coverage is narrow.** Only the pure helper's success path is covered.
5. **Package-operation docs are incomplete.** Test, build, and production
   verification commands are not documented.
6. **Deployment contract coverage is missing.** No test verifies that the
   installed entry point and package import work together.
7. **Non-trivial input verification is incomplete.** There is no test for
   multi-word environment prompts, empty overrides, or default CLI behavior.

Some stronger prompt requirements may be disproportionate for a one-module MVP,
but they remain differences between the written rules and the delivered code.

## Recommended Combined Rule Set — Best Parts of Both Iterations

A stronger next iteration would preserve the prompted worktree's structure
while retaining useful no-prompt behavior:

1. Keep the `src/` package, installable entry point, dependency injection, and
   pytest test structure.
2. Keep the explicit UV supply-chain policy, lockfile, and hashed pip export.
3. Retain command-line prompt input, with `LUNA_PROMPT` as an optional fallback.
4. Retain an explicit response-token cap and OpenRouter attribution headers.
5. Add an explicit timeout and handle specific SDK/network exceptions.
6. Expand tests across empty responses, missing configuration, API failures,
   environment overrides, and installed-entry-point behavior.
7. Keep stdout for model output and stderr/logging for diagnostics.
8. Use an `.env.example` only if the application deliberately loads `.env`, or
   change its guidance to require explicit shell export.
9. Resolve and document the intended default model ID.
10. Document setup, run, test, and build commands that have actually been
    verified.

## Verification — Checks Performed During This Comparison

The comparison used Git history, direct file diffs, file inventories, project
metadata, source inspection, and local non-network execution.

- Unstaged missing-key path: passed with expected exit code 2.
- Prompted worktree pytest suite: `1 passed`.
- Prompted installed command missing-key path: passed with expected exit code 2.
- Both lockfiles resolve `openai==2.53.0`.
- OpenRouter worktree status: clean.

No live OpenRouter request was made, so provider acceptance of either model ID
and real response behavior were not verified.

## Final Assessment — What the Prompt Changed

The strongest demonstrated effect of the Programming Prompt is not additional
business functionality. It is an expansion of the **engineering completion
standard**:

- from runnable script to installable package;
- from tightly coupled call to isolated and testable function;
- from manual confirmation to an automated contract;
- from implicit local dependency behavior to portable supply-chain policy;
- from result-only output to logged operational states;
- from a loose working tree to a clean feature commit.

The no-prompt version remains valuable as evidence of a leaner interface and
better request bounding. The best implementation would combine those practical
choices with the prompted worktree's maintainability, testing, packaging, and
reproducibility rules.
