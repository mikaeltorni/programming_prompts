---
name: linux-configuration
description: >-
  Mandatory rules for any task on this machine that touches Linux desktop
  configuration: GNOME Shell extensions, gsettings, themes, hotkeys, systemd
  user services, or a repository install.sh. Requires console-only, silent
  deployment paths and forbids agent-initiated GNOME Shell reloads, GUI resets,
  session restarts, logout, `gnome-shell --replace`, and shell-kill commands.
  Covers clean-install compatibility and the root-optional (sudo-free)
  installer pattern.
---

# Linux Desktop Configuration Guidelines

These rules apply whenever a change touches GNOME Shell, desktop settings,
hotkeys, systemd user services, or any repository `install.sh`. They are
mandatory, not advisory: follow them exactly even when the user's prompt does
not restate them, and never reach for a faster shortcut (session logout,
`gnome-shell --replace`, killing the Shell, or automating a GUI Shell reload)
to "just make it apply."

## Applying changes silently (required default)

Most desktop changes do NOT need a GNOME Shell reload. Reloading the Shell
flashes the panel, resets the overview/animations, and steals focus, so it
interrupts the human's active work. Do not automate Shell reloads or GUI
resets. Apply changes with the narrowest command-line mechanism that takes
effect live, in place, with no visible disruption:

- **gsettings / dconf** (hotkeys, `org.gnome.desktop.*`, `org.gnome.shell.*`
  keys, themes, app behavior): `gsettings set …` takes effect immediately in
  the running session. No reload.
- **An extension's own settings** (keys in its GSettings schema, read at
  runtime by the extension): `gsettings set` (or `dconf write`) on that
  schema applies live. No reload.
- **systemd user service** (trackers, daemons, helpers): restart only that
  unit — `systemctl --user restart <unit>`. No Shell reload, no GUI flash.
- **Enabling/disabling an extension** (toggling its on/off state, not
  changing its code): `gnome-extensions enable <uuid>` /
  `gnome-extensions disable <uuid>` runs the extension's own enable/disable
  in place without restarting the Shell.

Always state the exact silent command you ran to apply the change, and verify
it took effect (e.g. read the gsettings key back, `systemctl --user status`,
`gnome-extensions info <uuid>`).

## Extension code changes (deploy, do not reload)

Changing the **code** of a loaded extension (its `extension.js` / installed
files) still needs a fresh Shell process before the running desktop will execute
the edited source, because the Shell imports each extension's JS once per
shell-process lifetime and caches the module. There is no sanctioned,
non-disruptive command-line hot-reload for edited extension source:

- `gnome-extensions disable && enable` calls the *cached* module's
  disable/enable — it does NOT re-read the edited source.
- The `org.gnome.Shell.Extensions.ReloadExtension` D-Bus method is locked down
  (same restriction as `Eval`) and refuses external calls.
- A newly added extension directory is not detected by the running Shell at
  all until it reloads.

For extension code changes: deploy the files from the console, verify the
installed files and settings, then report that activation requires the user to
start a fresh GNOME Shell session themselves. Do not automate the run dialog,
do not send key events to trigger a Shell reload, and do not initiate logout,
reboot, or session restart.

Never use any of the following to force changes through, regardless of
session type:

- GNOME run-dialog reload automation, including `Alt+F2 r` or `xdotool`
  key/type sequences that trigger it
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
service or installer-side gsettings. Restart only the affected service instead
(`systemctl --user restart <unit>`), and do not reset the GUI.

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
