# Programming Prompts — AI Coding-Agent Prompts

[![Last commit](https://img.shields.io/github/last-commit/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/commits/master)
[![Commit activity](https://img.shields.io/github/commit-activity/m/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/graphs/commit-activity)
[![Issues](https://img.shields.io/github/issues/mikaeltorni/programming_prompts)](https://github.com/mikaeltorni/programming_prompts/issues)

Programming Prompts is a prompt library that provides reusable AI coding-agent prompts and engineering guidance for Codex and Claude Code users.

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
- Direct skills: General Programming Guidelines, Init Project, Refactoring, and Setup Repository Guidelines.
- Python Logging is retired and has been removed from this repository.

## Repository dependencies

This repository has no runtime dependency.

Repository ownership and routing are documented in [AGENTS.md](AGENTS.md).

Related research is documented in [Prompt Engineering for Software Development](https://github.com/mikaeltorni/prompt_engineering_for_software_development),
and challenge generation is covered by the
[Prompt Challenge Generator](https://github.com/mikaeltorni/prompt_challenge_generator).

## Quickstart

Clone the content source and inspect a skill directly:

```bash
git clone https://github.com/mikaeltorni/programming_prompts.git
cd programming_prompts
sed -n '1,120p' skills/general-programming-guidelines/SKILL.md
```

The command prints the reusable engineering workflow that agents load for
software tasks.

## AI coding-agent prompt features

This repository maintains the canonical engineering standards used across all
development projects in this workspace. Plugin prompts package exactly one skill
and carry manifests for both Codex and Claude Code; direct skills carry only
`SKILL.md` content.

- **General Programming Guidelines** — Shared coding, testing, and engineering workflow rules for all agent tasks.
- **Commit Guidelines** — Cautious Git commit workflow (inspect → plan → stage hunks → verify → compose).
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
│   └── linux-desktop-configuration/        # Console-only desktop deployment + sudo-free installers
├── skills/                                 # Direct skills, not plugins
│   ├── general-programming-guidelines/     # Engineering workflow & coding standards
│   ├── init-project/                       # Secure init with UV + supply-chain protection
│   ├── refactoring/                        # Test-driven refactoring workflow
│   └── setup-repository-guidelines/        # On-request setup-family routing & install policy
├── dispatch-skills/                        # Menu-selectable task skills: repo in, score out
│   └── github-seo/                        # GitHub discoverability audit, scored 0–100, looped
├── global-instructions/                    # Bootstrap tags merged into runtime instructions
│   └── general-programming-guidelines.md   # Starts the full-guidelines delivery path
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

### general-programming-guidelines

Current version: **v1.13.0**.

The canonical programming guidelines as a direct skill (formerly a plugin). Provides shared engineering workflow and coding standards that apply to every software task — implementation, debugging, review, testing, and refactoring. The prompt requires agents to preserve the user's wording and local state, avoid clobbering existing configuration with placeholder defaults such as `0`, and sandbox-test user-global installers, wrapper generation, and config deployment before applying them to the real environment. New projects and projects adding Python for the first time must also implement a rolling 24-hour package-release delay with `uv`; plain `pip` installs must consume a hash-locked export rather than resolve dependencies directly.

The bootstrap tag in `global-instructions/general-programming-guidelines.md` is
merged by the installer into every agent's instruction file. For the always-on
guidelines, the installer replaces that tag's body with the complete current
`SKILL.md`, and verifies the exact payload and native skill copy for every
configured Codex home plus Claude, Cline, Grok, and opencode. This keeps weak or
free models from having to discover a second file after the session starts.

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
`installation_scripts` manifest. It is invoked only on explicit user request or
when starting a completely new project that has no existing repository
guidelines; it is no longer merged into `AGENTS.md`/`CLAUDE.md` as a managed
global conditional that fires at the start of every task. Membership is still
read dynamically from `CLONE_REPOS`, so newly added repositories enter scope
without changing this skill.

## Dispatch Skills

`dispatch-skills/` holds the task prompts that are meaningful with no context
beyond "here is a repository". They are the only prompts offered by the
notes-app skill menu, which launches one agent per selected project with the
harness-native invocation — `/name` for Claude Code, Cline, and Grok, `$name`
for the Codex family — built from the skill's directory name.

A prompt qualifies for this folder only if it defines a measurable score, a
tracked scorecard file, and an improvement loop with an explicit stop condition;
see [`dispatch-skills/README.md`](dispatch-skills/README.md).

### github-seo

Audits a GitHub project's discoverability against a weighted 100-point rubric —
repository metadata and topics, README above the fold, keyword coverage,
AI/LLM citability (`llms.txt`, question-shaped FAQ, a quotable definitional
sentence), community health signals, docs-site technical SEO, registry presence,
cross-links, and freshness — minus penalties for keyword stuffing,
unsupported claims, badge and topic spam, artificial engagement, and dead links.
Scores land in a committed `docs/seo-scorecard.md` with per-criterion evidence
and a round history, so successive agent runs compare against real numbers
instead of opinions. The loop closes the highest-value gap, re-measures from
scratch, and repeats until a re-audit independently reproduces 100/100, then
switches to maintenance. Points are only awarded against recorded evidence, and
nothing is published, renamed, or posted on the user's behalf.

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

## Configuration

This content repository has no runtime configuration. Plugin manifests,
direct-skill directories, and `dispatch-skills/` are the source of truth; the
installer reads them when it deploys prompts to an agent environment.

## Troubleshooting and FAQ

### Where should I start with Programming Prompts?

Start with [general-programming-guidelines](skills/general-programming-guidelines/SKILL.md)
for the shared workflow, or browse the [plugin directories](plugins/) when you
need a packaged Codex and Claude Code integration.

### Is this repository a plugin marketplace?

No. It is the content source for plugins and skills. Marketplace generation and
installation are owned by the external installer workflow, so no marketplace
catalog is committed here.

### Which prompt is used for GitHub SEO audits?

Use the [github-seo dispatch skill](dispatch-skills/github-seo/SKILL.md). It
audits a repository, records a scorecard, and loops over verified gaps.

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
