# Programming Prompts

Central repository for Codex agent programming guidelines, commit workflows, and refactoring skills — packaged as reusable plugins and skills.

## Overview

This repository maintains the canonical engineering standards used across all development projects in this workspace. It packages five core capabilities as installable Codex plugins and skills:

- **General Programming Guidelines** — Shared coding, testing, and engineering workflow rules for all agent tasks.
- **Commit Guidelines** — Cautious Git commit workflow (inspect → plan → stage hunks → verify → compose).
- **Linux Desktop Configuration** — Shared GNOME/Ubuntu desktop rules: applying changes silently from the command line (gsettings/dconf live, `systemctl --user restart`, `gnome-extensions enable/disable`), never automating GNOME Shell reloads or GUI resets, reporting manual activation when extension code needs a fresh Shell session, preserving user sessions, maintaining clean-install compatibility, and using root-optional (sudo-free) installer patterns.
- **Refactoring Skill** — Test-driven refactoring methodology for restructuring monolithic codebases into clean modules.
- **Init Project Skill** — Auto-triggered secure project initialization with UV + supply-chain protection.

## Repository Structure

```
programming_prompts/
├── plugins/
│   ├── general-programming-guidelines/    # Codex plugin: engineering workflow & coding standards
│   │   └── .codex-plugin/plugin.json
│   ├── commit-guidelines/                 # Codex plugin: cautious Git commit workflow
│   │   └── .codex-plugin/plugin.json
│   ├── init-project/                      # Codex plugin: secure init with UV + supply-chain protection
│   │   └── .codex-plugin/plugin.json
│   └── linux-desktop-configuration/       # Codex plugin: console-only desktop deployment + sudo-free installer rules
│       └── .codex-plugin/plugin.json
├── skills/
│   └── refactoring/                       # Standalone SKILL.md for test-driven refactoring
│       └── SKILL.md
├── .kilo/
│   ├── skill/                             # Auto-loaded skills for project initialization
│   │   └── init-project.md
│   └── command/                           # Command triggers for skill auto-detection
│       └── init-project.md
├── tests/
│   └── test_python_supply_chain_policy.py # Tests for the supply-chain policy guidance
├── .log/                                  # Runtime logs (gitignored)
├── LICENSE.md                             # MIT License
└── README.md                              # This file
```

## Plugins

### general-programming-guidelines

Packages the canonical programming guidelines as a Codex plugin. Provides shared engineering workflow and coding standards that apply to every software task — implementation, debugging, review, testing, and refactoring. The prompt requires agents to preserve the user's wording and local state, avoid clobbering existing configuration with placeholder defaults such as `0`, and sandbox-test user-global installers, wrapper generation, and config deployment before applying them to the real environment. New projects and projects adding Python for the first time must also implement a rolling 24-hour package-release delay with `uv`; plain `pip` installs must consume a hash-locked export rather than resolve dependencies directly.

**Install:** The personal marketplace installs this as `general-programming-guidelines@personal`. Confirm with:
```bash
codex plugin list
```

### commit-guidelines

Packages the cautious Git commit workflow as a Codex plugin. Guides agents to inspect all changes (staged + unstaged), split diffs into logical commits, stage exact hunks, and compose clean conventional commits — one at a time, with verification.

**Install:** The personal marketplace installs this as `commit-guidelines@personal`. Confirm with:
```bash
codex plugin list
```

### init-project

Packages secure project initialization as a Codex plugin. Guides agents to set up new projects with UV by Astral as the required package manager, implementing a rolling 24-hour publication delay via uv's native `[tool.uv] exclude-newer = "24 hours"` setting to protect against supply-chain attacks.

**Install:** The personal marketplace installs this as `init-project@personal`. Confirm with:
```bash
codex plugin list
```

### linux-desktop-configuration

Packages the shared Linux desktop configuration rules as a Codex plugin (skill name: `linux-configuration`). Applies to any task touching GNOME Shell extensions, gsettings, themes, hotkeys, systemd user services, or repository installers:

- **Apply changes silently from the console:** most changes need no Shell reload — `gsettings set` (hotkeys/themes/shell keys/an extension's own settings) applies live, `systemctl --user restart <unit>` restarts only the affected service, and `gnome-extensions enable/disable` toggles extension state without a GUI flash. For extension *code* changes, deploy and verify the files, then report that the user must start a fresh GNOME Shell session before the running desktop can execute the edited source. Never automate GNOME Shell reloads, run-dialog reloads, logout, reboot, `gnome-shell --replace`, or shell-kill commands.
- **Clean installation compatibility:** every change must reproduce on a fresh checkout via `installation_scripts/install.sh`; installers stay idempotent.
- **Root-optional installers:** all project `install.sh` scripts run sudo-free in user mode (root-only steps are skipped and reported via `SUDO_REQUIRED_STEPS`); only `linux_installations_setup` hard-requires root.

**Install:** The agent_command_center installer copies it to `~/.claude/skills/linux-desktop-configuration`; the personal marketplace installs it as `linux-desktop-configuration@personal`. Confirm with:
```bash
codex plugin list
```


## Skills

### refactoring

A standalone skill that implements the **Test-Driven Refactoring** paradigm. Guides agents to restructure monolithic codebases into well-organized, single-responsibility modules without changing behavior — tests first, then extraction, then integration.

Key principles:
1. Analyze before touching code (identify monoliths, orphaned functions, missing tests).
2. Plan the module structure with clear responsibilities.
3. Write tests for existing functionality before extracting anything.
4. Extract one cohesive module at a time by default; for explicitly broad workspace requests, inventory every repository first and verify each extraction independently.
5. Update imports, documentation, logging paths, and project tree after each extraction.
6. Do not commit unless the user explicitly asks for commits.

### init-project (auto-triggered)

An auto-loaded skill triggered on project initialization. Implements supply-chain
protection for Python with UV by Astral and rolling 24-hour publication delay.
Located in `.kilo/skill/init-project.md` — no manual invocation needed when
creating Python projects.


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

## License

This project is licensed under the [MIT License](LICENSE.md).

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.
