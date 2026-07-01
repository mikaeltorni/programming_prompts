# Programming Prompts

The install catalog intentionally distinguishes plugins from direct skills:

- Plugins: Commit Guidelines, General Programming Guidelines, and Linux Desktop Configuration.
- Direct skills: Init Project, Refactoring, and Setup Repository Guidelines.
- Python Logging is retired and is not published or installed.

Central repository for Codex agent programming guidelines, commit workflows, and refactoring skills — packaged as reusable plugins and skills.

## Repository dependencies

This repository has no runtime dependency. It is the content source consumed by
`linux_codex_claude_code_setup`, which owns CLI, marketplace, and plugin
installation.

See the full cross-repository map in
[installation_scripts/DEPENDENCIES.md](https://github.com/mikaeltorni/installation_scripts/blob/master/DEPENDENCIES.md).

## Overview

This repository maintains the canonical engineering standards used across all
development projects in this workspace. Plugin prompts package exactly one skill
and carry manifests for both Codex and Claude Code; direct skills carry only
`SKILL.md` content.

- **General Programming Guidelines** — Shared coding, testing, and engineering workflow rules for all agent tasks.
- **Commit Guidelines** — Cautious Git commit workflow (inspect → plan → stage hunks → verify → compose).
- **Linux Desktop Configuration** — Shared GNOME/Ubuntu desktop rules: applying changes silently from the command line (gsettings/dconf live, `systemctl --user restart`, `gnome-extensions enable/disable`), activating edited extension code with the sanctioned in-place X11 run-dialog reload (`xdotool` `Alt+F2 r`) while still forbidding destructive session restarts, asking for manual logout to activate extension code on Wayland, preserving user sessions, maintaining clean-install compatibility, and using root-optional (sudo-free) installer patterns.
- **Refactoring Skill** — Test-driven refactoring methodology for restructuring monolithic codebases into clean modules.
- **Init Project Skill** — Auto-triggered secure project initialization with UV + supply-chain protection.
- **Python Logging** — One centralized logging module per project plus a standard call-tracing decorator that logs each function's file and name, its arguments on entry, and its return value on exit.
- **Setup Repository Guidelines** — On-request (or new-project) repository-family routing and installer integration based on the orchestration manifest; no longer auto-triggered on every task.

## Repository Structure

```
programming_prompts/
├── AGENTS.md                               # Rule: no marketplace files in this repo
├── plugins/                                # One directory per plugin; each has
│   │                                       #   .codex-plugin/ + .claude-plugin/ manifests
│   │                                       #   and exactly one skills/<name>/SKILL.md
│   ├── general-programming-guidelines/    # Engineering workflow & coding standards
│   ├── init-project/                      # Secure init with UV + supply-chain protection
│   ├── linux-desktop-configuration/       # Console-only desktop deployment + sudo-free installers
│   ├── python-logging/                     # Centralized logging module + call-tracing decorator
│   └── refactoring/                        # Test-driven refactoring workflow
├── skills/                                 # Direct skills, not plugins
│   ├── commit/                             # Cautious Git commit workflow
│   └── setup-repository-guidelines/        # On-request setup-family routing & install policy
├── tests/                                  # pytest policy tests for the plugin prompts
├── .log/                                  # Runtime logs (gitignored)
├── LICENSE.md                             # MIT License
└── README.md                              # This file
```

## Installation

Installation belongs to the sibling
[`linux_codex_claude_code_setup`](https://github.com/mikaeltorni/linux_codex_claude_code_setup)
repository. Its committed `default.json` maps each prompt to either a plugin or
a direct skill and controls default selection. This repository intentionally
contains no `install.sh`, installer libraries, or marketplace catalogs — marketplace
generation is owned entirely by the installer repository (see `AGENTS.md`). Each
`plugins/<name>` directory stays standalone-installable via its own Codex and
Claude manifests plus its single skill. Top-level `skills/<name>` directories
are installed directly as skills and do not appear in plugin marketplaces.

## Plugins

### general-programming-guidelines

Packages the canonical programming guidelines as a Codex plugin. Provides shared engineering workflow and coding standards that apply to every software task — implementation, debugging, review, testing, and refactoring. The prompt requires agents to preserve the user's wording and local state, avoid clobbering existing configuration with placeholder defaults such as `0`, and sandbox-test user-global installers, wrapper generation, and config deployment before applying them to the real environment. New projects and projects adding Python for the first time must also implement a rolling 24-hour package-release delay with `uv`; plain `pip` installs must consume a hash-locked export rather than resolve dependencies directly.

**Install:** The programming-prompts marketplace installs this as `general-programming-guidelines@programming-prompts`. Confirm with:
```bash
codex plugin list
```

### init-project

Packages secure project initialization as a Codex plugin. Guides agents to set up new projects with UV by Astral as the required package manager, implementing a rolling 24-hour publication delay via uv's native `[tool.uv] exclude-newer = "24 hours"` setting to protect against supply-chain attacks.

**Install:** The programming-prompts marketplace installs this as `init-project@programming-prompts`. Confirm with:
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

### python-logging

Packages the centralized Python logging model as a Codex/Claude plugin (skill
name: `python-logging`). Establishes a single logging module per project that
every other module imports, and forbids ad-hoc `log()` / `log_info()` /
`log_warning()` / `log_error()` helpers redefined in the middle of feature files.
The standard `@log_call` decorator stamps each record with the wrapped function's
file and qualified name, logs every bound argument on entry, and logs the return
value on exit — and nothing else. Logging is best-effort and idempotent, writes
to the repository `.log/` directory by default, and falls back to a null handler
so it never aborts the program. Services swap the file sink for stderr
(journald); TUIs stay file-only — all through the one module.

**Install:** The programming-prompts marketplace installs it as `python-logging@programming-prompts`. Confirm with:
```bash
codex plugin list
```

### refactoring

An installable per-skill plugin that implements the **Test-Driven Refactoring** paradigm. Guides agents to restructure monolithic codebases into well-organized, single-responsibility modules without changing behavior — tests first, then extraction, then integration.

Key principles:
1. Analyze before touching code (identify monoliths, orphaned functions, missing tests).
2. Plan the module structure with clear responsibilities.
3. Write tests for existing functionality before extracting anything.
4. Extract one cohesive module at a time by default; for explicitly broad workspace requests, inventory every repository first and verify each extraction independently.
5. Update imports, documentation, logging paths, and project tree after each extraction.
6. Do not commit unless the user explicitly asks for commits.

## Direct Skills

### commit

Guides agents to inspect all changes (staged + unstaged), split diffs into
logical commits, stage exact hunks, and compose clean conventional commits. It
is installed as a direct skill, not as `commit-guidelines@programming-prompts`.

### setup-repository-guidelines

A direct skill (not an auto-applied global instruction) that applies owner
routing, component selection, clean-install, deployment, and prompt-free
keyring requirements to the repository family discovered from the sibling
`installation_scripts` manifest. It is invoked only on explicit user request or
when starting a completely new project that has no existing repository
guidelines; it is no longer merged into `AGENTS.md`/`CLAUDE.md` as a managed
global conditional that fires at the start of every task. Membership is still
read dynamically from `CLONE_REPOS`, so newly added repositories enter scope
without changing this skill.

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

## License

This project is licensed under the [MIT License](LICENSE.md).

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.
