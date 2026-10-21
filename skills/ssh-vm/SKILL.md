---
name: ssh-vm
description: >-
  v0.0.17 — Use when a task requires SSH access to a VM to deploy software or test it there. Skip local-only tests and SSH discussion without a remote VM action.
---

# SSH VM

Use this skill only when the task calls for an actual SSH deployment or test on
a VM. Ask for the VM IP or hostname if missing. Use `ubuntu` for an Ubuntu
Desktop live USB unless the user gives another username. Whenever you provide
VM-console bootstrap commands, always include a `sudo passwd <username>` step
for the SSH account (default `ubuntu`; use the VM's `whoami` value if different).
The user chooses the password at the VM's local `passwd` prompt; do not ask
them to send it in chat. For password-based SSH login, use an interactive
SSH prompt and let the user enter it there. Never print, log, save, or put
passwords in a shell command.

## First contact with a VM

When the user starts a VM task by providing an IP address or hostname and has
not confirmed that SSH setup is complete, assume the VM is unprepared. Do not
connect, probe the port, or run any network reachability check. Give the user
the VM-console setup commands below and wait for them to confirm they ran the
commands. An IP address alone does not mean SSH is ready. If the user confirms
SSH is already configured, proceed to **Connect after setup is confirmed**.

If the operating system is unknown, ask the user to identify it from the VM
console before giving operating-system-specific commands; still do not probe
the VM over the network.

## Fresh Ubuntu VM setup

Give the complete setup bundle in the same response: the VM-console block
below, the agent-side connection command, and the details the user must report.
Do not make the user request the remaining commands one at a time. Substitute
known connection details in that response; label any remaining placeholders.
Show the connection command now, but wait for setup confirmation before running
it or any network probe.

For a fresh Ubuntu Desktop VM with GNOME and the default SSH port 22, ask the
user to open Terminal on the VM itself (and finish the welcome screen first if
this is a live USB), then run this entire block. Run the `gsettings` commands
as the logged-in desktop user, without sudo; they prevent idle screen blanking
and automatic suspend on both AC and battery power:

```bash
sudo apt update
sudo env DEBIAN_FRONTEND=noninteractive UCF_FORCE_CONFFOLD=1 \
  apt install -y -o Dpkg::Options::="--force-confold" openssh-server
sudo systemctl enable --now ssh
sudo passwd "$(id -un)"
sudo install -d -m 755 /etc/ssh/sshd_config.d
printf '%s\n' 'PasswordAuthentication yes' | sudo tee /etc/ssh/sshd_config.d/00-agent-vm-access.conf >/dev/null
sudo sshd -t && sudo systemctl reload ssh
if command -v ufw >/dev/null && sudo ufw status | grep -q '^Status: active'; then
  sudo ufw allow 22/tcp
fi
gsettings set org.gnome.desktop.session idle-delay uint32 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
gsettings get org.gnome.desktop.session idle-delay
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type
id -un
sudo sshd -T | grep -i '^passwordauthentication'
sudo ss -lntp | grep ':22'
hostname -I
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```

In that same response, label this command **Agent machine — after setup is
confirmed**, replacing `ubuntu` and `VM_IP` with the reported username and
reachable VM address when known:

```bash
ssh -tt -o ConnectTimeout=5 ubuntu@VM_IP
```

`sudo passwd "$(id -un)"` sets the password for the current account; if the SSH
username is different, use `sudo passwd <ssh_username>` for that account. The
user enters the new password at the VM's local `passwd` prompt. The apt command
preserves existing configuration files without package dialogs: the dpkg option
covers dpkg-managed files, while `UCF_FORCE_CONFFOLD=1` covers the ucf-managed
`sshd_config`. Keep the password prompt interactive. If an earlier install is
already showing the `sshd_config` dialog, select **keep the local version
currently installed** and press Enter; these variables apply to new commands.
The SSH drop-in enables the interactive password login used here without
replacing the existing `sshd_config`; validate before reloading. The firewall
step opens port 22 only if UFW is already active. For a supplied custom port,
adapt the listening check, firewall rule and connection command together.
If the effective authentication check still says `no` or the listener is
missing, resolve that console-side failure before connecting.

Ask the user to confirm completion and report the username, reachable IP,
host-key fingerprint, whether `passwordauthentication` is `yes`, and whether
SSH is listening; never request the password. The GNOME readbacks should be
`uint32 0`, `'nothing'`, and `'nothing'`. These settings apply immediately
without a Shell reload. On another desktop, use its idle-display controls
instead of GNOME commands. A live USB loses this setup on reboot.

## Connect after setup is confirmed

Only after the user confirms the console commands ran, or confirms SSH was
already configured, make a connection attempt. Use their IP/hostname, username,
port, and key when provided. For key-based access, a short probe is:

```bash
ssh -o BatchMode=yes -o ConnectTimeout=5 ubuntu@VM_IP 'id -un; hostname'
```

For password-only access, skip the `BatchMode` probe and open an interactive
SSH session so the user can enter the password at the SSH prompt:

```bash
ssh -tt -o ConnectTimeout=5 ubuntu@VM_IP
```

Use the actual username and add `-p PORT` when the user provides a non-default
port. Never ask the user to send the password in chat or put it in a command.

A new live session may generate a new host key. If SSH warns that the key
changed, compare its fingerprint with the VM console's `ssh-keygen` output
before replacing the old `known_hosts` entry. Never disable host-key checks.
If authentication fails, check the username and ask the user to reset the
password locally with `sudo passwd <ssh_username>` if needed. For a timeout,
check the current IP, port 22 with `sudo ss -lntp`, and `sudo ufw status` on the
VM.

## Deploy and verify

After login, confirm `id -un`, `hostname`, and the relevant VM environment.
Inspect the destination before copying. Transfer the needed files with `scp`
or `rsync` without a delete option, run the project's installer or activation
on the VM, then check its behavior, status, and logs **on the VM**. Respect the
project's desktop and service rules.

After installing or updating CLI launchers, refresh the target user's PATH and
command cache yourself before testing. Use the installer's command directory;
for `~/.local/bin` in Bash, run:

```bash
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

In that same remote shell, resolve each requested CLI and configured alias with
`command -v`, confirm it points to the intended installation, and run its
supported version or health check. Require successful exit statuses before
reporting success. Ensure the installer persists the command directory for new
shells, then repeat the command-name checks in a fresh login shell. A PATH export
in one SSH process does not affect later SSH processes.

When the reported failure is in an already-open VM terminal, refresh and test
that terminal too if console control is available. An SSH child process cannot
change that terminal's environment. If only SSH access is available, state which
shells were verified and that the existing terminal still needs a refresh.
Complete all accessible refreshes and checks before handing the task back.

For every relevant local change to a project the user asked to run on the VM,
update that project's VM copy, apply the change there, and verify it there.
Local tests alone do not prove a VM deployment. If SSH is unavailable, report
the exact failure and the VM-console step needed to resume.

For GNOME desktop tests, determine the actual desktop session type rather than
using the SSH shell's session type. When an X11 extension install or code change
needs a Shell reload, check that `xdotool` is installed **on the VM**. If it is
missing, install it using the VM's authorized package access before testing:

```bash
sudo apt install -y -o Dpkg::Options::="--force-confold" xdotool
```

Run desktop commands as the desktop user with that live session's `DISPLAY`,
`XAUTHORITY`, runtime directory, and session bus. Follow `linux-configuration`
for the sanctioned in-place `Alt+F2 r` reload and its verification. Reload only
when needed to load newly installed or edited extension code; settings changes
apply live. On Wayland, follow that policy's manual activation procedure and
never force a Shell restart. After activation, verify the extension is active
and recheck the selected bindings before exercising the shortcut.

When a test depends on visible desktop behavior, capture and inspect a VM
screenshot if a safe, supported capture method is available. SSH access alone
does not guarantee access to the guest display; do not assume GUI screenshot
tools will work from a remote shell. If visual confirmation would help but no
capture method is available, ask the user to provide a screenshot. Use the
image to guide any needed fix, then deploy and verify that fix on the VM. Keep
captures outside the project source unless the user asks to retain them.
