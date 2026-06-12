---
name: linux-configuration
description: >-
  Mandatory rules for any task that touches Linux desktop configuration on
  this machine: GNOME Shell extensions, gsettings, themes, hotkeys, systemd
  user services, or repository installers. Covers safe in-place GNOME Shell
  reloads (X11 Alt+F2 r), Wayland restrictions, clean installation
  compatibility, and the root-optional (sudo-free) installer pattern.
---

# Linux Desktop Configuration Guidelines

These rules apply whenever a change touches GNOME Shell, desktop settings,
hotkeys, systemd user services, or any repository `install.sh`.

## Reloading GNOME Shell

When a change needs GNOME Shell to reload (extensions, themes, shell-side
configuration), reload it in place — never log the user out or terminate the
session.

- **X11 session (the in-place reload is X11-exclusive):** run the complete
  command
  `xdotool key Alt+F2; sleep 1; xdotool type r; xdotool key Return`.
  This opens the GNOME run dialog, enters its internal `r` command, and
  submits it, restarting gnome-shell while preserving open windows and
  applications. Do not open Alt+F2 by itself to test or inspect the dialog;
  that interrupts the human's active work. Always run the complete sequence
  when a reload is required.
- **Wayland session:** there is no in-place reload. Ask the user to log out
  and back in themselves. Do NOT initiate it.

Never use any of the following to force changes through, regardless of
session type:

- `gnome-session-quit` / `--logout` / `--force`
- `loginctl terminate-session …` / `loginctl kill-user …`
- `systemctl --user stop gnome-session*` or similar unit stops
- `pkill -HUP gnome-shell`, `killall gnome-shell`, or any signal that ends
  the shell process on Wayland
- `gnome-shell --replace` — it can disrupt the current session and leave
  user extensions globally disabled

Losing the user's open work is a worse outcome than waiting for them to
reload manually.

After extension work, verify `gsettings get org.gnome.shell
disable-user-extensions` is `false` and previously enabled extensions are
still active.

A Shell reload is NOT needed when the change only affects a systemd user
service or installer-side gsettings; restart the service instead
(`systemctl --user restart <unit>`).

## Clean Installation Compatibility

All repository changes must remain compatible with a clean installation run
through `installation_scripts/install.sh` and the repository's own
`install.sh`. Do not rely on packages, files, settings, or manual steps that
exist only on the current machine. Add every required dependency, asset,
configuration step, and migration to the installer so a fresh checkout can
reproduce the complete setup.

Keep installation steps idempotent and verify the clean-install path for
every change.

## Root-Optional Installers (avoid sudo)

All project `install.sh` scripts must run sudo-free in user mode; only
`linux_installations_setup` hard-requires root. When writing or modifying
installers:

- Default invocation is `bash install.sh` with no sudo. Root-only steps
  (e.g. `apt install`, udev rules, files under `/etc` or `/usr`) are
  skipped, collected in a `SUDO_REQUIRED_STEPS` list, and reported at the
  end with the exact `sudo` command to apply them.
- When invoked via sudo (clean-install chain), use a `run_as_target` helper
  (`sudo -H -u "$TARGET_USER" env …`) so user-level work still lands in the
  desktop user's session, never in root's home.
- Prefer user-level mechanisms that need no root at all:
  - `gsettings` — always works as the logged-in user.
  - GNOME extensions in `~/.local/share/gnome-shell/extensions/` —
    user-owned; patch and reconfigure without root.
  - `gnome-extensions enable/disable` — user-level.
  - `systemctl --user` units instead of system units.
  - Files under `$HOME` (`~/.claude`, `~/.config`, `~/.local`).
- sudo is genuinely required only for: package management (`apt`),
  system-wide extension dirs (`/usr/share/gnome-shell/extensions/`), and
  root-owned paths (`/etc`, `/usr/lib`, udev rules).
- Never bake an unconditional `sudo` into a script step that a non-root run
  will hit; it stalls unattended/agent runs on a password prompt.
