---
name: setup-repository-guidelines
description: Mandatory for every software task in the installation_scripts Linux setup repository family; dynamically detects membership from scripts/repository_manifest.sh and enforces owner routing, selectable installer integration, clean-install compatibility, safe deployment, and prompt-free keyring handling.
---

# Setup Repository Guidelines

Use this skill for any task in the linked Linux setup repository family.

## Determine scope dynamically

1. Resolve the current Git root and repository basename.
2. Locate `installation_scripts/scripts/repository_manifest.sh` either in the
   current repository or in a sibling checkout under the same projects folder.
3. Source that manifest in a Bash subprocess and read `CLONE_REPOS`. The current
   repository is in scope when its basename is `installation_scripts` or occurs
   in that array.
4. Do not maintain a copied repository-name list in this skill. New repositories
   added to `CLONE_REPOS` must trigger this guidance
   automatically.
5. If the current repository is not in scope, stop applying this skill.

## Route before editing

- Read `installation_scripts/AGENTS.md`, `DEPENDENCIES.md`, and the current
  repository's own `AGENTS.md` before editing.
- Implement each concern in its owning repository. Update the orchestrator only
  for membership, ordering, aggregate selection, or setup-chain documentation.
- Inspect all affected sibling repositories; a feature may span several owners.

## Integrate every installed feature

- A user-visible feature is incomplete until its owning `install.sh` reproduces
  it on a clean machine.
- Component-aware repositories expose each independently selectable feature in
  `installer/components.sh`. New components are default-on unless the product
  requirement explicitly makes them optional.
- Keep listing side-effect free and support `--list-components`, `--select`,
  `--default`, and `--all` through the shared framework.
- Add focused tests for source behavior, installer idempotence, and clean-home
  installation before deployment.
- Run only the narrow owning installer or selected component; never run the
  master installer merely to deploy one child change.

## Prevent keyring prompts

When a task involves GNOME Keyring, Secret Service, automatic-login unlock
dialogs, or a keychain prompt while opening Claude Code:

- Ownership is `linux_configuration_setup`.
- Preserve Secret Service functionality and existing credential items.
- Ensure the default-on `passwordless_keyring` component is present and selected
  by the clean installation path.
- Migrate text and binary secrets without printing or logging secret values.
- Verify the resulting Login collection accepts the empty automatic-login
  password and remains the default collection.
- State the security tradeoff: removing prompts makes keyring contents no longer
  protected by an at-rest password.

## Deploy safely

Follow the Linux desktop configuration skill for desktop settings, services,
extensions, hotkeys, and installers. Apply the narrowest silent command and
verify installed state against source. Never force changes through with logout,
reboot, session termination, `gnome-shell --replace`, or shell-kill commands;
the only Shell reload an agent may perform is the in-place X11 run-dialog reload
(`xdotool` `Alt+F2 r`) for activating edited extension code, and on Wayland that
activation stays a manual logout.
