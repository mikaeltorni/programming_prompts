# Programming Prompts

Central repository for Codex agent programming guidelines, commit workflows, and refactoring skills — packaged as reusable plugins and skills.

## Overview

This repository maintains the canonical engineering standards used across all development projects in this workspace. It packages three core capabilities as installable Codex plugins and skills:

- **General Programming Guidelines** — Shared coding, testing, and engineering workflow rules for all agent tasks.
- **Commit Guidelines** — Cautious Git commit workflow (inspect → plan → stage hunks → verify → compose).
- **Refactoring Skill** — Test-driven refactoring methodology for restructuring monolithic codebases into clean modules.

## Repository Structure

```
programming_prompts/
├── plugins/
│   ├── general-programming-guidelines/    # Codex plugin: engineering workflow & coding standards
│   │   └── .codex-plugin/plugin.json
│   └── commit-guidelines/                 # Codex plugin: cautious Git commit workflow
│       └── .codex-plugin/plugin.json
├── skills/
│   └── refactoring/                       # Standalone SKILL.md for test-driven refactoring
│       └── SKILL.md
├── tests/
│   └── test_logging.py                    # Tests for logging utility assertions
├── .log/                                  # Runtime logs (gitignored)
├── AGENTS.md                              # Agent instructions for this repo
├── LICENSE.md                             # MIT License
└── README.md                              # This file
```

## Plugins

### general-programming-guidelines

Packages the canonical programming guidelines as a Codex plugin. Provides shared engineering workflow and coding standards that apply to every software task — implementation, debugging, review, testing, and refactoring.

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

## Skills

### refactoring

A standalone skill that implements the **Test-Driven Refactoring** paradigm. Guides agents to restructure monolithic codebases into well-organized, single-responsibility modules without changing behavior — tests first, then extraction, then integration.

Key principles:
1. Analyze before touching code (identify monoliths, orphaned functions, missing tests).
2. Plan the module structure with clear responsibilities.
3. Write tests for existing functionality before extracting anything.
4. Extract one module at a time, verify, and commit separately.
5. Update imports, documentation, and project tree after each extraction.

## Logging

The repository uses a standardized `.log/` directory for runtime logs from utilities such as `copy_prompts_to_projects`. These are gitignored to keep the working tree clean:

```bash
# Log output lives here (gitignored)
.log/copy_prompts_to_projects.log
```

## Testing

Run the test suite with pytest:

```bash
cd tests && python -m pytest test_logging.py -v
```

## License

This project is licensed under the [MIT License](LICENSE.md).

## Disclaimer

This software is provided under the MIT License on an **“as is”** basis, without warranties of any kind. To the maximum extent permitted by applicable law, the authors and copyright holders shall not be liable for any claims, damages, losses, or other liability arising from the use of this software.

You are solely responsible for determining whether this software is suitable, safe, lawful, and appropriate for your intended use. Unless explicitly stated otherwise, this project is general-purpose software and is not designed, tested, certified, or approved for safety-critical, medical, automotive, aviation, industrial-control, life-support, cybersecurity-critical, financial-critical, or other high-risk use cases.

The authors and copyright holders make no guarantees regarding security, reliability, availability, correctness, compliance, non-infringement, or fitness for any particular purpose.

This notice is intended to clarify the nature of the project and does not impose additional restrictions beyond the MIT License.
